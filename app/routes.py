from functools import wraps
from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from .db import get_db, csv_for_grades, utcnow

bp=Blueprint('main',__name__)
MASTER=85.0


def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args,**kwargs):
            if not session.get('user_id'): return redirect(url_for('main.login'))
            if role and session.get('role')!=role: abort(403)
            return fn(*args,**kwargs)
        return wrapper
    return deco

@bp.route('/health')
def health(): return {'status':'ok','app':'richmack-georgia','phase':3},200

@bp.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=get_db().execute('SELECT * FROM users WHERE username=?',(request.form.get('username','').strip(),)).fetchone()
        if u and check_password_hash(u['password_hash'],request.form.get('password','')):
            session.clear(); session.update(user_id=u['id'],role=u['role'],display_name=u['display_name'])
            return redirect(url_for('main.admin') if u['role']=='admin' else url_for('main.dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

@bp.route('/logout')
def logout(): session.clear(); return redirect(url_for('main.login'))

@bp.route('/')
def home(): return render_template('home.html')

@bp.route('/dashboard')
@login_required()
def dashboard():
    db=get_db(); uid=session['user_id']
    modules=db.execute('''SELECT m.*,c.title course_title,
      COUNT(l.id) lesson_count,
      SUM(CASE WHEN p.status='mastered' THEN 1 ELSE 0 END) mastered_count
      FROM modules m JOIN courses c ON c.id=m.course_id JOIN lessons l ON l.module_id=m.id
      LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=?
      GROUP BY m.id ORDER BY c.sort_order,m.sort_order''',(uid,)).fetchall()
    lessons=db.execute('''SELECT l.*,m.title module_title,c.title course_title,p.best_auto_score,p.final_score,p.status
      FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
      LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? ORDER BY c.sort_order,m.sort_order,l.sort_order''',(uid,)).fetchall()
    summary=db.execute('''SELECT COUNT(*) attempted,
      SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END) mastered,
      SUM(CASE WHEN status='provisional' THEN 1 ELSE 0 END) provisional,
      COALESCE(AVG(CASE WHEN final_score IS NOT NULL THEN final_score ELSE best_auto_score END),0) avg_score
      FROM progress WHERE user_id=?''',(uid,)).fetchone()
    game_stats=db.execute("SELECT COALESCE(MAX(score),0) best_score FROM game_attempts WHERE user_id=?",(uid,)).fetchone()
    return render_template('dashboard.html',modules=modules,lessons=lessons,summary=summary,game_stats=game_stats)

@bp.route('/module/<slug>')
@login_required()
def module_view(slug):
    db=get_db(); uid=session['user_id']
    module=db.execute('''SELECT m.*,c.title course_title FROM modules m JOIN courses c ON c.id=m.course_id WHERE m.slug=?''',(slug,)).fetchone()
    if not module: abort(404)
    lessons=db.execute('''SELECT l.*,p.best_auto_score,p.final_score,p.status FROM lessons l
       LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? WHERE l.module_id=? ORDER BY l.sort_order''',(uid,module['id'])).fetchall()
    return render_template('module.html',module=module,lessons=lessons)

@bp.route('/lesson/<slug>',methods=['GET','POST'])
@login_required()
def lesson(slug):
    db=get_db(); uid=session['user_id']
    lesson=db.execute('''SELECT l.*,m.title module_title,m.slug module_slug,m.mastery_threshold,c.title course_title,
      s.name source_name,s.agency,s.url source_url,s.verified_on
      FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
      LEFT JOIN sources s ON s.id=l.source_id WHERE l.slug=?''',(slug,)).fetchone()
    if not lesson: abort(404)
    items=db.execute('SELECT * FROM assessment_items WHERE lesson_id=? ORDER BY sort_order,id',(lesson['id'],)).fetchall()
    result=None
    if request.method=='POST':
        earned=0.0; possible=0.0; details=[]; constructed_count=0
        now=utcnow()
        for item in items:
            typ=item['item_type']
            if typ=='constructed':
                text=request.form.get(f"i{item['id']}",'').strip()
                if text:
                    constructed_count += 1
                    db.execute('''INSERT INTO constructed_submissions(user_id,lesson_id,item_id,response_text,submitted_at)
                                  VALUES (?,?,?,?,?)''',(uid,lesson['id'],item['id'],text,now))
                details.append({'item':item,'ok':None,'answer':text})
                continue
            possible += item['points']
            ok=False; ans=request.form.get(f"i{item['id']}",'').strip()
            if typ=='mcq': ok=(ans==item['correct_text'])
            elif typ=='numeric':
                try: ok=abs(float(ans)-float(item['numeric_answer'])) <= float(item['numeric_tolerance'] or 0)
                except ValueError: ok=False
            if ok: earned += item['points']
            details.append({'item':item,'ok':ok,'answer':ans})
        auto=100.0*earned/possible if possible else 0.0
        required_constructed=sum(1 for i in items if i['item_type']=='constructed')
        if auto>=MASTER and constructed_count>=required_constructed and required_constructed>0: status='provisional'
        elif auto>=MASTER and required_constructed==0: status='mastered'
        else: status='remediation'
        prev=db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?',(uid,lesson['id'])).fetchone()
        attempts=(prev['attempts'] if prev else 0)+1; best=max(auto,prev['best_auto_score'] if prev else 0)
        final=prev['final_score'] if prev else None
        db.execute('''INSERT INTO progress(user_id,lesson_id,best_auto_score,final_score,attempts,status,last_completed_at)
          VALUES (?,?,?,?,?,?,?) ON CONFLICT(user_id,lesson_id) DO UPDATE SET
          best_auto_score=excluded.best_auto_score,final_score=COALESCE(progress.final_score,excluded.final_score),attempts=excluded.attempts,
          status=CASE WHEN progress.status='mastered' THEN 'mastered' ELSE excluded.status END,last_completed_at=excluded.last_completed_at''',
          (uid,lesson['id'],best,final,attempts,status,now))
        db.execute('INSERT INTO grade_events(user_id,lesson_id,auto_score,final_score,status,completed_at) VALUES (?,?,?,?,?,?)',
                   (uid,lesson['id'],auto,final,status,now))
        db.commit(); result={'auto_score':auto,'status':status,'details':details,'constructed':constructed_count}
    return render_template('lesson.html',lesson=lesson,items=items,result=result,mastery=MASTER)

@bp.route('/map')
def map_view(): return render_template('map.html',game_mode=request.args.get('game')=='map-hunt')

@bp.route('/games')
@login_required()
def games(): return render_template('games.html')

@bp.route('/api/games/map-hunt/score',methods=['POST'])
@login_required()
def save_map_hunt_score():
    if session.get('role')!='student': return jsonify({'ok':False,'error':'student account required'}),403
    p=request.get_json(silent=True) or {}; correct=max(0,int(p.get('correct',0))); total=max(1,int(p.get('total',1))); duration=max(0,int(p.get('duration_seconds',0)))
    score=min(100.0,100.0*correct/total); db=get_db(); db.execute('INSERT INTO game_attempts(user_id,game_key,score,correct_count,question_count,duration_seconds,completed_at) VALUES (?,?,?,?,?,?,?)',(session['user_id'],'map-hunt',score,correct,total,duration,utcnow())); db.commit()
    return jsonify({'ok':True,'score':round(score,1)})

@bp.route('/admin')
@login_required('admin')
def admin():
    db=get_db()
    students=db.execute('''SELECT u.id,u.display_name,u.age,COUNT(p.id) attempted,
      SUM(CASE WHEN p.status='mastered' THEN 1 ELSE 0 END) mastered,
      COALESCE(ROUND(AVG(CASE WHEN p.final_score IS NOT NULL THEN p.final_score ELSE p.best_auto_score END),1),0) avg_score
      FROM users u LEFT JOIN progress p ON p.user_id=u.id WHERE u.role='student' GROUP BY u.id''').fetchall()
    pending=db.execute('''SELECT cs.*,u.display_name,l.title lesson,ai.prompt,ai.rubric FROM constructed_submissions cs
      JOIN users u ON u.id=cs.user_id JOIN lessons l ON l.id=cs.lesson_id JOIN assessment_items ai ON ai.id=cs.item_id
      WHERE cs.rubric_score IS NULL ORDER BY cs.submitted_at''').fetchall()
    sources=db.execute('SELECT * FROM sources ORDER BY agency,name').fetchall()
    return render_template('admin.html',students=students,pending=pending,sources=sources)

@bp.route('/admin/review/<int:submission_id>',methods=['POST'])
@login_required('admin')
def review_submission(submission_id):
    db=get_db(); sub=db.execute('SELECT * FROM constructed_submissions WHERE id=?',(submission_id,)).fetchone()
    if not sub: abort(404)
    score=max(0,min(4,int(request.form.get('rubric_score',0)))); comment=request.form.get('teacher_comment','').strip(); now=utcnow()
    db.execute('UPDATE constructed_submissions SET rubric_score=?,teacher_comment=?,reviewed_at=? WHERE id=?',(score,comment,now,submission_id))
    # Recalculate lesson final when all constructed responses for the latest attempt have at least one reviewed response per constructed item.
    p=db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?',(sub['user_id'],sub['lesson_id'])).fetchone()
    constructed_items=db.execute("SELECT id FROM assessment_items WHERE lesson_id=? AND item_type='constructed'",(sub['lesson_id'],)).fetchall()
    rubric_scores=[]
    for i in constructed_items:
        r=db.execute('''SELECT rubric_score FROM constructed_submissions WHERE user_id=? AND lesson_id=? AND item_id=? AND rubric_score IS NOT NULL ORDER BY reviewed_at DESC LIMIT 1''',(sub['user_id'],sub['lesson_id'],i['id'])).fetchone()
        if r: rubric_scores.append(r['rubric_score'])
    if constructed_items and len(rubric_scores)==len(constructed_items):
        rubric_pct=100.0*sum(rubric_scores)/(4*len(rubric_scores)); final=0.70*p['best_auto_score']+0.30*rubric_pct
        status='mastered' if final>=MASTER else 'remediation'
        db.execute('UPDATE progress SET final_score=?,status=? WHERE user_id=? AND lesson_id=?',(final,status,sub['user_id'],sub['lesson_id']))
        db.execute('INSERT INTO grade_events(user_id,lesson_id,auto_score,final_score,status,completed_at) VALUES (?,?,?,?,?,?)',(sub['user_id'],sub['lesson_id'],p['best_auto_score'],final,status,now))
    db.commit(); flash('Constructed response reviewed and lesson grade recalculated when all rubric items are complete.')
    return redirect(url_for('main.admin'))

@bp.route('/admin/export/grades.csv')
@login_required('admin')
def export_grades():
    return Response(csv_for_grades(request.args.get('student_id',type=int)),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=georgia_phase3_grades.csv'})
