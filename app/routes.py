from functools import wraps
from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from .db import get_db, csv_for_grades, utcnow

bp = Blueprint('main', __name__)


def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            uid = session.get('user_id')
            if not uid:
                return redirect(url_for('main.login'))
            if role and session.get('role') != role:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco


@bp.route('/health')
def health():
    return {'status': 'ok', 'app': 'richmack-georgia'}, 200


@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = get_db().execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session.update(user_id=user['id'], role=user['role'], display_name=user['display_name'])
            return redirect(url_for('main.admin') if user['role']=='admin' else url_for('main.dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/dashboard')
@login_required()
def dashboard():
    db = get_db(); uid=session['user_id']
    lessons = db.execute('''SELECT l.*, c.title course_title, p.best_score, p.mastery, p.completed
                            FROM lessons l JOIN courses c ON c.id=l.course_id
                            LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=?
                            ORDER BY c.sort_order,l.sort_order''',(uid,)).fetchall()
    summary = db.execute('''SELECT COUNT(*) lesson_count,
        SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) completed_count,
        COALESCE(AVG(CASE WHEN attempts>0 THEN mastery END),0) avg_mastery
        FROM progress WHERE user_id=?''',(uid,)).fetchone()
    game_stats = db.execute('''SELECT COUNT(*) attempts, COALESCE(MAX(score),0) best_score FROM game_attempts WHERE user_id=?''',(uid,)).fetchone()
    return render_template('dashboard.html', lessons=lessons, summary=summary, game_stats=game_stats)


@bp.route('/lesson/<slug>', methods=['GET','POST'])
@login_required()
def lesson(slug):
    db=get_db(); uid=session['user_id']
    lesson = db.execute('''SELECT l.*, c.title course_title, s.name source_name, s.agency, s.url source_url,
                           s.verified_on FROM lessons l JOIN courses c ON c.id=l.course_id
                           LEFT JOIN sources s ON s.id=l.source_id WHERE l.slug=?''',(slug,)).fetchone()
    if not lesson: abort(404)
    questions = db.execute('SELECT * FROM questions WHERE lesson_id=? ORDER BY id',(lesson['id'],)).fetchall()
    result=None
    if request.method=='POST' and questions:
        correct=0; details=[]
        for q in questions:
            answer=request.form.get(f"q{q['id']}")
            ok=answer==q['correct']; correct += int(ok)
            details.append((q,answer,ok))
        score=100.0*correct/len(questions)
        now=utcnow()
        row=db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?',(uid,lesson['id'])).fetchone()
        attempts=(row['attempts'] if row else 0)+1
        best=max(score,row['best_score'] if row else 0)
        mastery=max(score,row['mastery'] if row else 0)
        completed=1 if score>=70 or (row and row['completed']) else 0
        db.execute('''INSERT INTO progress(user_id,lesson_id,best_score,attempts,completed,mastery,last_completed_at)
                      VALUES (?,?,?,?,?,?,?) ON CONFLICT(user_id,lesson_id) DO UPDATE SET
                      best_score=excluded.best_score,attempts=excluded.attempts,completed=excluded.completed,
                      mastery=excluded.mastery,last_completed_at=excluded.last_completed_at''',
                   (uid,lesson['id'],best,attempts,completed,mastery,now))
        db.execute('INSERT INTO grade_events(user_id,lesson_id,score,correct_count,question_count,completed_at) VALUES (?,?,?,?,?,?)',
                   (uid,lesson['id'],score,correct,len(questions),now))
        db.commit(); result={'score':score,'correct':correct,'total':len(questions),'details':details}
    return render_template('lesson.html', lesson=lesson, questions=questions, result=result)


@bp.route('/map')
def map_view():
    game_mode = request.args.get('game') == 'map-hunt'
    return render_template('map.html', game_mode=game_mode)


@bp.route('/api/games/map-hunt/score', methods=['POST'])
@login_required()
def save_map_hunt_score():
    if session.get('role') != 'student':
        return jsonify({'ok': False, 'error': 'student account required'}), 403
    payload = request.get_json(silent=True) or {}
    correct = max(0, int(payload.get('correct', 0)))
    total = max(1, int(payload.get('total', 1)))
    duration = max(0, int(payload.get('duration_seconds', 0)))
    score = min(100.0, 100.0 * correct / total)
    db = get_db()
    db.execute('''INSERT INTO game_attempts(user_id,game_key,score,correct_count,question_count,duration_seconds,completed_at)
                  VALUES (?,?,?,?,?,?,?)''',
               (session['user_id'], 'map-hunt', score, correct, total, duration, utcnow()))
    db.commit()
    return jsonify({'ok': True, 'score': round(score, 1)})


@bp.route('/games')
@login_required()
def games():
    return render_template('games.html')


@bp.route('/admin')
@login_required('admin')
def admin():
    db=get_db()
    students=db.execute('''SELECT u.id,u.display_name,u.age,
      COUNT(DISTINCT p.lesson_id) attempted,
      SUM(CASE WHEN p.completed=1 THEN 1 ELSE 0 END) completed,
      COALESCE(ROUND(AVG(CASE WHEN p.attempts>0 THEN p.mastery END),1),0) mastery
      FROM users u LEFT JOIN progress p ON p.user_id=u.id
      WHERE u.role='student' GROUP BY u.id ORDER BY u.display_name''').fetchall()
    sources=db.execute('SELECT * FROM sources ORDER BY agency,name').fetchall()
    grades=db.execute('''SELECT g.*,u.display_name,l.title lesson FROM grade_events g
                         JOIN users u ON u.id=g.user_id JOIN lessons l ON l.id=g.lesson_id
                         ORDER BY g.completed_at DESC LIMIT 20''').fetchall()
    return render_template('admin.html',students=students,sources=sources,grades=grades)


@bp.route('/admin/export/grades.csv')
@login_required('admin')
def export_grades():
    text=csv_for_grades(request.args.get('student_id',type=int))
    return Response(text,mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=georgia_grades.csv'})
