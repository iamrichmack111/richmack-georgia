from functools import wraps
import secrets
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db, csv_for_grades, gradebook_rows, utcnow
from .phase5 import current_academic_year_id, skill_stats, assignment_rows

bp = Blueprint('main', __name__)
MASTER = 85.0


def current_user():
    if not session.get('user_id'):
        return None
    return get_db().execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()


def login_required(role=None, permission=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('main.login'))
            u = current_user()
            if not u or not u['active']:
                session.clear()
                flash('This account is disabled.')
                return redirect(url_for('main.login'))
            if role:
                roles = {role} if isinstance(role, str) else set(role)
                if u['role'] not in roles:
                    abort(403)
            if permission and u['role'] == 'student' and not u[permission]:
                flash('This area is currently restricted for this student account.')
                return redirect(url_for('main.dashboard'))
            return fn(*args, **kwargs)
        return wrapper
    return deco


def can_view_student(student_id):
    if session.get('role') == 'admin':
        return True
    if session.get('role') != 'parent':
        return session.get('user_id') == student_id
    row = get_db().execute('SELECT 1 FROM parent_student_links WHERE parent_id=? AND student_id=?',
                           (session['user_id'], student_id)).fetchone()
    return bool(row)


def record_usage(event_type, endpoint=None, duration=0, detail=None, user_id=None):
    uid = user_id or session.get('user_id')
    if not uid:
        return
    db = get_db()
    db.execute('INSERT INTO usage_events(user_id,event_type,endpoint,duration_seconds,detail,created_at) VALUES (?,?,?,?,?,?)',
               (uid, event_type, endpoint, max(0, int(duration or 0)), detail, utcnow()))
    db.commit()


@bp.route('/health')
def health():
    return {'status': 'ok', 'app': 'richmack-georgia', 'phase': '5.0'}, 200


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        u = db.execute('SELECT * FROM users WHERE username=?', (request.form.get('username', '').strip(),)).fetchone()
        if u and u['active'] and check_password_hash(u['password_hash'], request.form.get('password', '')):
            now = utcnow()
            session.clear()
            session.update(user_id=u['id'], role=u['role'], display_name=u['display_name'])
            db.execute('UPDATE users SET last_login_at=? WHERE id=?', (now, u['id']))
            db.execute('INSERT INTO usage_events(user_id,event_type,endpoint,duration_seconds,detail,created_at) VALUES (?,?,?,?,?,?)',
                       (u['id'], 'login', 'login', 0, None, now))
            db.commit()
            if u['must_change_password']:
                flash('Please set a new password before continuing.')
                return redirect(url_for('main.change_password'))
            if u['role'] == 'admin':
                return redirect(url_for('main.admin'))
            if u['role'] == 'parent':
                return redirect(url_for('main.parent_portal'))
            return redirect(url_for('main.dashboard'))
        flash('Invalid username/password, or the account is disabled.')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


@bp.route('/account/password', methods=['GET', 'POST'])
@login_required()
def change_password():
    u = current_user()
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if not check_password_hash(u['password_hash'], current):
            flash('Current password is incorrect.')
        elif len(new) < 8:
            flash('New password must be at least 8 characters.')
        elif new != confirm:
            flash('New passwords do not match.')
        else:
            db = get_db()
            db.execute('UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?',
                       (generate_password_hash(new), u['id']))
            db.commit()
            flash('Password changed.')
            return redirect(url_for('main.admin' if u['role'] == 'admin' else 'main.parent_portal' if u['role'] == 'parent' else 'main.dashboard'))
    return render_template('change_password.html')


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/dashboard')
@login_required(role='student')
def dashboard():
    u = current_user(); db = get_db(); uid = u['id']
    modules = db.execute('''SELECT m.*,c.title course_title, COUNT(l.id) lesson_count,
      SUM(CASE WHEN p.status='mastered' THEN 1 ELSE 0 END) mastered_count
      FROM modules m JOIN courses c ON c.id=m.course_id JOIN lessons l ON l.module_id=m.id
      LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=?
      WHERE ? BETWEEN l.min_age AND l.max_age
      GROUP BY m.id ORDER BY c.sort_order,m.sort_order''', (uid,u['age'])).fetchall()
    lessons = db.execute('''SELECT l.*,m.title module_title,c.title course_title,p.best_auto_score,p.final_score,p.status
      FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
      LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? WHERE ? BETWEEN l.min_age AND l.max_age ORDER BY c.sort_order,m.sort_order,l.sort_order''', (uid,u['age'])).fetchall()
    summary = db.execute('''SELECT COUNT(*) attempted,
      SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END) mastered,
      SUM(CASE WHEN status='provisional' THEN 1 ELSE 0 END) provisional,
      COALESCE(AVG(CASE WHEN final_score IS NOT NULL THEN final_score ELSE best_auto_score END),0) avg_score
      FROM progress WHERE user_id=?''', (uid,)).fetchone()
    game_stats = db.execute('''SELECT COUNT(*) attempts,COALESCE(MAX(score),0) best_score,COALESCE(AVG(score),0) avg_score,
                               COALESCE(SUM(duration_seconds),0) seconds FROM game_attempts WHERE user_id=?''', (uid,)).fetchone()
    tips = build_tips(uid)
    assignments = assignment_rows(uid)
    skills = [x for x in skill_stats(uid) if x['evidence_count'] > 0]
    record_usage('view', 'dashboard')
    return render_template('dashboard.html', modules=modules, lessons=lessons, summary=summary, game_stats=game_stats,
                           tips=tips, assignments=assignments, skills=skills, user=u)


@bp.route('/module/<slug>')
@login_required(role='student', permission='allow_courses')
def module_view(slug):
    db = get_db(); uid = session['user_id']
    module = db.execute('''SELECT m.*,c.title course_title FROM modules m JOIN courses c ON c.id=m.course_id WHERE m.slug=?''', (slug,)).fetchone()
    if not module: abort(404)
    age=current_user()['age']
    lessons = db.execute('''SELECT l.*,p.best_auto_score,p.final_score,p.status FROM lessons l
       LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? WHERE l.module_id=? AND ? BETWEEN l.min_age AND l.max_age ORDER BY l.sort_order''', (uid, module['id'],age)).fetchall()
    record_usage('view', 'module', detail=slug)
    return render_template('module.html', module=module, lessons=lessons)


@bp.route('/lesson/<slug>', methods=['GET', 'POST'])
@login_required(role='student', permission='allow_courses')
def lesson(slug):
    db = get_db(); uid = session['user_id']
    lesson = db.execute('''SELECT l.*,m.title module_title,m.slug module_slug,m.mastery_threshold,c.title course_title,
      s.name source_name,s.agency,s.url source_url,s.verified_on
      FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
      LEFT JOIN sources s ON s.id=l.source_id WHERE l.slug=?''', (slug,)).fetchone()
    if not lesson: abort(404)
    items = db.execute('SELECT * FROM assessment_items WHERE lesson_id=? ORDER BY sort_order,id', (lesson['id'],)).fetchall()
    result = None
    timer_key = f"lesson_start_{lesson['id']}"
    if request.method == 'GET':
        session[timer_key] = int(time.time())
        record_usage('view', 'lesson', detail=slug)
    else:
        earned = 0.0; possible = 0.0; details = []; constructed_count = 0; now = utcnow()
        for item in items:
            typ = item['item_type']
            if typ == 'constructed':
                text = request.form.get(f"i{item['id']}", '').strip()
                if text:
                    constructed_count += 1
                    db.execute('''INSERT INTO constructed_submissions(user_id,lesson_id,item_id,response_text,submitted_at)
                                  VALUES (?,?,?,?,?)''', (uid, lesson['id'], item['id'], text, now))
                details.append({'item': item, 'ok': None, 'answer': text})
                continue
            possible += item['points']; ok = False; ans = request.form.get(f"i{item['id']}", '').strip()
            if typ == 'mcq': ok = (ans == item['correct_text'])
            elif typ == 'numeric':
                try: ok = abs(float(ans) - float(item['numeric_answer'])) <= float(item['numeric_tolerance'] or 0)
                except ValueError: ok = False
            if ok: earned += item['points']
            details.append({'item': item, 'ok': ok, 'answer': ans})
        auto = 100.0 * earned / possible if possible else 0.0
        required_constructed = sum(1 for i in items if i['item_type'] == 'constructed')
        if auto >= MASTER and constructed_count >= required_constructed and required_constructed > 0: status = 'provisional'
        elif auto >= MASTER and required_constructed == 0: status = 'mastered'
        else: status = 'remediation'
        prev = db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?', (uid, lesson['id'])).fetchone()
        attempts = (prev['attempts'] if prev else 0) + 1; best = max(auto, prev['best_auto_score'] if prev else 0)
        final = prev['final_score'] if prev else None
        db.execute('''INSERT INTO progress(user_id,lesson_id,best_auto_score,final_score,attempts,status,last_completed_at)
          VALUES (?,?,?,?,?,?,?) ON CONFLICT(user_id,lesson_id) DO UPDATE SET
          best_auto_score=excluded.best_auto_score,final_score=COALESCE(progress.final_score,excluded.final_score),attempts=excluded.attempts,
          status=CASE WHEN progress.status='mastered' THEN 'mastered' ELSE excluded.status END,last_completed_at=excluded.last_completed_at''',
          (uid, lesson['id'], best, final, attempts, status, now))
        year_id = current_academic_year_id(db)
        db.execute('INSERT INTO grade_events(user_id,lesson_id,auto_score,final_score,status,completed_at,academic_year_id) VALUES (?,?,?,?,?,?,?)',
                   (uid, lesson['id'], auto, final, status, now, year_id))
        duration = max(0, int(time.time()) - int(session.pop(timer_key, int(time.time()))))
        db.execute('INSERT INTO usage_events(user_id,event_type,endpoint,duration_seconds,detail,created_at) VALUES (?,?,?,?,?,?)',
                   (uid, 'lesson_submit', 'lesson', duration, slug, now))
        db.commit(); result = {'auto_score': auto, 'status': status, 'details': details, 'constructed': constructed_count}
    return render_template('lesson.html', lesson=lesson, items=items, result=result, mastery=MASTER)


@bp.route('/map')
@login_required()
def map_view():
    u = current_user()
    if u['role'] == 'student' and not u['allow_map']:
        flash('Map access is currently restricted for this student account.')
        return redirect(url_for('main.dashboard'))
    record_usage('view', 'map')
    return render_template('map.html', game_mode=request.args.get('game') == 'map-hunt')


@bp.route('/games')
@login_required(role='student', permission='allow_games')
def games():
    record_usage('view', 'games')
    return render_template('games.html')


@bp.route('/api/games/map-hunt/score', methods=['POST'])
@login_required(role='student', permission='allow_games')
def save_map_hunt_score():
    p = request.get_json(silent=True) or {}
    correct = max(0, int(p.get('correct', 0))); total = max(1, int(p.get('total', 1))); duration = max(0, int(p.get('duration_seconds', 0)))
    score = min(100.0, 100.0 * correct / total); db = get_db(); now = utcnow()
    year_id = current_academic_year_id(db)
    cur = db.execute('INSERT INTO game_attempts(user_id,game_key,score,correct_count,question_count,duration_seconds,completed_at,academic_year_id) VALUES (?,?,?,?,?,?,?,?)',
               (session['user_id'], 'map-hunt', score, correct, total, duration, now, year_id))
    game_attempt_id = cur.lastrowid
    breakdown = p.get('skill_breakdown') or {}
    for skill_key, values in breakdown.items():
        try:
            c = max(0, int(values.get('correct', 0))); q = max(0, int(values.get('total', 0)))
        except (AttributeError, TypeError, ValueError):
            continue
        if q:
            db.execute('INSERT INTO game_skill_attempts(game_attempt_id,user_id,skill_key,correct_count,question_count,score) VALUES (?,?,?,?,?,?)',
                       (game_attempt_id, session['user_id'], skill_key, c, q, 100.0*c/q))
    db.execute('INSERT INTO usage_events(user_id,event_type,endpoint,duration_seconds,detail,created_at) VALUES (?,?,?,?,?,?)',
               (session['user_id'], 'game_submit', 'map-hunt', duration, f'{correct}/{total}', now))
    db.commit()
    return jsonify({'ok': True, 'score': round(score, 1), 'gradebook': True})


def build_tips(uid):
    db = get_db(); tips = []
    weak = db.execute('''SELECT l.title,p.best_auto_score,p.final_score,p.attempts,p.status FROM progress p
       JOIN lessons l ON l.id=p.lesson_id WHERE p.user_id=?
       ORDER BY COALESCE(p.final_score,p.best_auto_score) ASC,p.attempts DESC LIMIT 3''', (uid,)).fetchall()
    for w in weak:
        score = w['final_score'] if w['final_score'] is not None else w['best_auto_score']
        if score < MASTER:
            tips.append(f"Review {w['title']}: current score {score:.0f}%. Re-read the worked example, then retry after explaining the main idea in your own words.")
        elif w['attempts'] > 1:
            tips.append(f"Strengthen {w['title']}: you reached mastery, but needed {w['attempts']} attempts. Try one fresh problem without notes.")
    gs = db.execute('SELECT COUNT(*) n,COALESCE(AVG(score),0) avg,COALESCE(MAX(score),0) best FROM game_attempts WHERE user_id=?', (uid,)).fetchone()
    if gs['n'] and gs['avg'] < MASTER:
        tips.append(f"Map Hunt average is {gs['avg']:.0f}%. Focus on transportation and water layers separately before combining all layers.")
    elif gs['n'] and gs['best'] >= 90:
        tips.append('Map recognition is strong. Move into explanation questions: describe why the feature matters, what connects to it, and what would change if it failed.')
    skill_rows = [x for x in skill_stats(uid) if x['evidence_count'] > 0]
    if skill_rows:
        weakest = sorted(skill_rows, key=lambda x: (x['score'], -x['evidence_count']))[0]
        if weakest['score'] < MASTER:
            tips.insert(0, f"Skill focus: {weakest['label']} is currently {weakest['score']:.0f}% across {weakest['evidence_count']} evidence item(s). Choose practice that targets this skill before repeating your strongest area.")
    if not tips:
        tips.append('Complete another lesson or Map Hunt round. Improvement tips become more specific as the system collects more attempts.')
    return tips[:4]


def student_report_data(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (student_id,)).fetchone()
    if not student: abort(404)
    grade_rows = gradebook_rows(student_id, limit=25)
    lesson_stats = db.execute('''SELECT COUNT(*) attempted,COALESCE(AVG(COALESCE(final_score,best_auto_score)),0) avg,
      SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END) mastered,COALESCE(SUM(attempts),0) attempts
      FROM progress WHERE user_id=?''', (student_id,)).fetchone()
    game_stats = db.execute('''SELECT COUNT(*) attempts,COALESCE(AVG(score),0) avg,COALESCE(MAX(score),0) best,
      COALESCE(SUM(duration_seconds),0) seconds FROM game_attempts WHERE user_id=?''', (student_id,)).fetchone()
    usage = db.execute('''SELECT COUNT(*) events,COUNT(DISTINCT substr(created_at,1,10)) active_days,
      COALESCE(SUM(duration_seconds),0) seconds,MAX(created_at) last_active FROM usage_events WHERE user_id=?''', (student_id,)).fetchone()
    recent = db.execute('SELECT * FROM usage_events WHERE user_id=? ORDER BY created_at DESC LIMIT 15', (student_id,)).fetchall()
    return student, grade_rows, lesson_stats, game_stats, usage, recent, build_tips(student_id)


@bp.route('/admin')
@login_required(role='admin')
def admin():
    db = get_db()
    students = db.execute('''SELECT u.id,u.display_name,u.username,u.age,u.active,u.last_login_at,
      (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id) lesson_attempted,
      (SELECT COUNT(*) FROM game_attempts ga WHERE ga.user_id=u.id) game_attempts,
      (SELECT ROUND(AVG(score),1) FROM game_attempts ga WHERE ga.user_id=u.id) game_avg,
      (SELECT ROUND(AVG(COALESCE(final_score,best_auto_score)),1) FROM progress p WHERE p.user_id=u.id) course_avg
      FROM users u WHERE u.role='student' ORDER BY u.display_name''').fetchall()
    pending = db.execute('''SELECT cs.*,u.display_name,l.title lesson,ai.prompt,ai.rubric FROM constructed_submissions cs
      JOIN users u ON u.id=cs.user_id JOIN lessons l ON l.id=cs.lesson_id JOIN assessment_items ai ON ai.id=cs.item_id
      WHERE cs.rubric_score IS NULL ORDER BY cs.submitted_at''').fetchall()
    latest_grades = gradebook_rows(limit=30)
    sources = db.execute('SELECT * FROM sources ORDER BY agency,name').fetchall()
    invites = db.execute('''SELECT pi.*,u.display_name student FROM parent_invites pi LEFT JOIN users u ON u.id=pi.student_id
                            ORDER BY pi.created_at DESC LIMIT 10''').fetchall()
    years = db.execute('SELECT * FROM academic_years ORDER BY starts_on DESC').fetchall()
    modules = db.execute('SELECT m.id,m.title,c.title course FROM modules m JOIN courses c ON c.id=m.course_id ORDER BY c.sort_order,m.sort_order').fetchall()
    lessons = db.execute('SELECT l.id,l.title,m.title module FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id ORDER BY c.sort_order,m.sort_order,l.sort_order').fetchall()
    recent_assignments = db.execute('''SELECT a.*,u.display_name student,COALESCE(l.title,m.title) activity,ay.name academic_year
       FROM assignments a JOIN users u ON u.id=a.student_id JOIN academic_years ay ON ay.id=a.academic_year_id
       LEFT JOIN lessons l ON l.id=a.lesson_id LEFT JOIN modules m ON m.id=a.module_id
       WHERE a.archived=0 ORDER BY a.id DESC LIMIT 20''').fetchall()
    return render_template('admin.html', students=students, pending=pending, latest_grades=latest_grades, sources=sources, invites=invites,
                           years=years, modules=modules, lessons=lessons, recent_assignments=recent_assignments)


@bp.route('/admin/student/<int:student_id>')
@login_required(role=('admin', 'parent'))
def student_report(student_id):
    if not can_view_student(student_id): abort(403)
    student, grade_rows, lesson_stats, game_stats, usage, recent, tips = student_report_data(student_id)
    skills = skill_stats(student_id)
    assignments = assignment_rows(student_id)
    return render_template('student_report.html', student=student, grade_rows=grade_rows, lesson_stats=lesson_stats,
                           game_stats=game_stats, usage=usage, recent=recent, tips=tips, skills=skills, assignments=assignments)


@bp.route('/parent')
@login_required(role='parent')
def parent_portal():
    db = get_db()
    students = db.execute('''SELECT u.* FROM users u JOIN parent_student_links psl ON psl.student_id=u.id
                             WHERE psl.parent_id=? ORDER BY u.display_name''', (session['user_id'],)).fetchall()
    modules = db.execute('SELECT m.id,m.title,c.title course FROM modules m JOIN courses c ON c.id=m.course_id ORDER BY c.sort_order,m.sort_order').fetchall()
    lessons = db.execute('SELECT l.id,l.title,m.title module FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id ORDER BY c.sort_order,m.sort_order,l.sort_order').fetchall()
    return render_template('parent.html', students=students, modules=modules, lessons=lessons)


@bp.route('/parent/students/create', methods=['POST'])
@login_required(role='parent')
def parent_create_student():
    db = get_db()
    display = request.form.get('display_name', '').strip()
    username = request.form.get('username', '').strip()
    age = request.form.get('age', type=int)
    pw = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    if not display or len(username) < 3:
        flash('Enter a student name and username of at least 3 characters.')
    elif age is None or age < 9 or age > 14:
        flash('Student age must be between 9 and 14 for this curriculum.')
    elif len(pw) < 8 or pw != confirm:
        flash('Student passwords must match and be at least 8 characters.')
    elif db.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone():
        flash('That username is already in use.')
    else:
        cur = db.execute('''INSERT INTO users(username,password_hash,display_name,role,age,must_change_password)
                            VALUES (?,?,?,?,?,1)''',
                         (username, generate_password_hash(pw), display, 'student', age))
        sid = cur.lastrowid
        db.execute('INSERT INTO parent_student_links(parent_id,student_id) VALUES (?,?)',
                   (session['user_id'], sid))
        db.commit()
        flash(f'{display} was created and linked only to your parent account. The student must change the temporary password at first login.')
    return redirect(url_for('main.parent_portal'))


@bp.route('/parent/students/claim', methods=['POST'])
@login_required(role='parent')
def parent_claim_student():
    db = get_db()
    code = request.form.get('claim_code', '').strip().upper().replace('-', '')
    row = db.execute('''SELECT scc.*,u.display_name FROM student_claim_codes scc
                        JOIN users u ON u.id=scc.student_id
                        WHERE replace(upper(scc.code),'-','')=?''', (code,)).fetchone()
    if not row or row['used_at']:
        flash('That Family Link Code is invalid or has already been used.')
    elif row['expires_at'] and datetime.fromisoformat(row['expires_at']) < datetime.now(timezone.utc):
        flash('That Family Link Code has expired.')
    else:
        db.execute('INSERT OR IGNORE INTO parent_student_links(parent_id,student_id) VALUES (?,?)',
                   (session['user_id'], row['student_id']))
        db.execute('UPDATE student_claim_codes SET used_at=?,used_by_parent_id=? WHERE id=?',
                   (utcnow(), session['user_id'], row['id']))
        db.commit()
        flash(f"{row['display_name']} is now linked to your family.")
    return redirect(url_for('main.parent_portal'))


@bp.route('/admin/invites', methods=['POST'])
@login_required(role='admin')
def create_parent_invite():
    db = get_db(); student_id = request.form.get('student_id', type=int)
    if student_id and not db.execute("SELECT 1 FROM users WHERE id=? AND role='student'", (student_id,)).fetchone(): abort(400)
    token = secrets.token_urlsafe(24); now = datetime.now(timezone.utc); expires = now + timedelta(days=7)
    db.execute('INSERT INTO parent_invites(token,created_by,student_id,expires_at,created_at) VALUES (?,?,?,?,?)',
               (token, session['user_id'], student_id, expires.replace(microsecond=0).isoformat(), now.replace(microsecond=0).isoformat()))
    db.commit()
    invite_url = url_for('main.accept_invite', token=token, _external=True)
    flash(f'Parent invite created: {invite_url}')
    return redirect(url_for('main.admin'))


@bp.route('/invite/<token>', methods=['GET', 'POST'])
def accept_invite(token):
    db = get_db(); inv = db.execute('SELECT * FROM parent_invites WHERE token=?', (token,)).fetchone()
    if not inv or inv['used_at']:
        return render_template('invite.html', invalid=True), 410
    if inv['expires_at'] and datetime.fromisoformat(inv['expires_at']) < datetime.now(timezone.utc):
        return render_template('invite.html', invalid=True), 410
    if request.method == 'POST':
        username = request.form.get('username', '').strip(); display_name = request.form.get('display_name', '').strip()
        pw = request.form.get('password', ''); confirm = request.form.get('confirm_password', '')
        if len(username) < 3 or not display_name:
            flash('Enter a display name and a username of at least 3 characters.')
        elif len(pw) < 8 or pw != confirm:
            flash('Passwords must match and be at least 8 characters.')
        elif db.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone():
            flash('That username is already in use.')
        else:
            cur = db.execute('INSERT INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
                             (username, generate_password_hash(pw), display_name, 'parent', None))
            parent_id = cur.lastrowid
            if inv['student_id']:
                db.execute('INSERT OR IGNORE INTO parent_student_links(parent_id,student_id) VALUES (?,?)', (parent_id, inv['student_id']))
            # A parent invite with no student is intentionally unscoped. It grants zero student records.
            # The parent can create a child or claim an existing student with a one-time Family Link Code.
            db.execute('UPDATE parent_invites SET used_at=? WHERE id=?', (utcnow(), inv['id']))
            db.commit(); flash('Parent account created. You can sign in now.')
            return redirect(url_for('main.login'))
    student = db.execute('SELECT display_name FROM users WHERE id=?', (inv['student_id'],)).fetchone() if inv['student_id'] else None
    return render_template('invite.html', invite=inv, student=student, invalid=False)


@bp.route('/admin/students/<int:student_id>/family-code', methods=['POST'])
@login_required(role='admin')
def create_family_link_code(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (student_id,)).fetchone()
    if not student:
        abort(404)
    # Invalidate older unused codes for this student so there is only one current claim secret.
    db.execute('UPDATE student_claim_codes SET used_at=? WHERE student_id=? AND used_at IS NULL',
               (utcnow(), student_id))
    raw = secrets.token_hex(4).upper()
    code = raw[:4] + '-' + raw[4:]
    now = datetime.now(timezone.utc); expires = now + timedelta(days=7)
    db.execute('''INSERT INTO student_claim_codes(student_id,code,created_by,expires_at,created_at)
                  VALUES (?,?,?,?,?)''',
               (student_id, code, session['user_id'], expires.replace(microsecond=0).isoformat(),
                now.replace(microsecond=0).isoformat()))
    db.commit()
    flash(f"Family Link Code for {student['display_name']}: {code} (expires in 7 days; one use)")
    return redirect(url_for('main.manage_users'))


@bp.route('/admin/users')
@login_required(role='admin')
def manage_users():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY role,display_name').fetchall()
    students = db.execute("SELECT id,display_name,age,active FROM users WHERE role='student' ORDER BY display_name").fetchall()
    parent_links = {}
    for row in db.execute('SELECT parent_id,student_id FROM parent_student_links'):
        parent_links.setdefault(row['parent_id'], set()).add(row['student_id'])
    claim_codes = {}
    for row in db.execute('''SELECT * FROM student_claim_codes WHERE used_at IS NULL ORDER BY created_at DESC'''):
        claim_codes.setdefault(row['student_id'], row)
    return render_template('users.html', users=users, students=students, parent_links=parent_links, claim_codes=claim_codes)


@bp.route('/admin/users/create', methods=['POST'])
@login_required(role='admin')
def create_user():
    db = get_db(); username = request.form.get('username', '').strip(); display = request.form.get('display_name', '').strip()
    role = request.form.get('role', 'student'); age = request.form.get('age', type=int); pw = request.form.get('password', '')
    if role not in {'student', 'parent', 'admin'}: abort(400)
    if len(username) < 3 or not display or len(pw) < 8:
        flash('Username/display name required; password must be at least 8 characters.')
    elif db.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone():
        flash('Username already exists.')
    else:
        db.execute('INSERT INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
                   (username, generate_password_hash(pw), display, role, age if role == 'student' else None))
        db.commit(); flash('User created.')
    return redirect(url_for('main.manage_users'))


@bp.route('/admin/parents/<int:parent_id>/links', methods=['POST'])
@login_required(role='admin')
def update_parent_links(parent_id):
    db = get_db()
    parent = db.execute("SELECT * FROM users WHERE id=? AND role='parent'", (parent_id,)).fetchone()
    if not parent:
        abort(404)
    raw_ids = request.form.getlist('student_ids')
    valid_ids = []
    for raw in raw_ids:
        try:
            sid = int(raw)
        except (TypeError, ValueError):
            continue
        if db.execute("SELECT 1 FROM users WHERE id=? AND role='student'", (sid,)).fetchone():
            valid_ids.append(sid)
    db.execute('DELETE FROM parent_student_links WHERE parent_id=?', (parent_id,))
    for sid in sorted(set(valid_ids)):
        db.execute('INSERT INTO parent_student_links(parent_id,student_id) VALUES (?,?)', (parent_id, sid))
    db.commit()
    flash(f"Student visibility updated for {parent['display_name']}.")
    return redirect(url_for('main.manage_users'))


@bp.route('/admin/users/<int:user_id>/update', methods=['POST'])
@login_required(role='admin')
def update_user(user_id):
    db = get_db(); u = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not u: abort(404)
    active = 1 if request.form.get('active') else 0
    allow_courses = 1 if request.form.get('allow_courses') else 0
    allow_map = 1 if request.form.get('allow_map') else 0
    allow_games = 1 if request.form.get('allow_games') else 0
    if user_id == session['user_id']: active = 1
    db.execute('UPDATE users SET active=?,allow_courses=?,allow_map=?,allow_games=? WHERE id=?',
               (active, allow_courses, allow_map, allow_games, user_id)); db.commit(); flash('User access updated.')
    return redirect(url_for('main.manage_users'))


@bp.route('/admin/users/<int:user_id>/password', methods=['POST'])
@login_required(role='admin')
def admin_reset_password(user_id):
    db = get_db(); u = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not u: abort(404)
    pw = request.form.get('new_password', '')
    if len(pw) < 8:
        flash('Temporary password must be at least 8 characters.')
    else:
        db.execute('UPDATE users SET password_hash=?,must_change_password=1 WHERE id=?', (generate_password_hash(pw), user_id))
        db.commit(); flash(f"Password reset for {u['display_name']}. They must change it at next login.")
    return redirect(url_for('main.manage_users'))


@bp.route('/admin/users/reset-all.csv', methods=['POST'])
@login_required(role='admin')
def bulk_reset_passwords():
    db = get_db()
    users = db.execute("SELECT id,username,display_name,role FROM users WHERE id<>? AND active=1 ORDER BY role,display_name", (session['user_id'],)).fetchall()
    import csv, io
    out = io.StringIO(); writer = csv.writer(out); writer.writerow(['display_name','username','role','temporary_password'])
    for u in users:
        temp = secrets.token_urlsafe(9)
        db.execute('UPDATE users SET password_hash=?,must_change_password=1 WHERE id=?', (generate_password_hash(temp), u['id']))
        writer.writerow([u['display_name'],u['username'],u['role'],temp])
    db.commit()
    return Response(out.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=richmack_georgia_temporary_passwords.csv'})


@bp.route('/admin/review/<int:submission_id>', methods=['POST'])
@login_required(role='admin')
def review_submission(submission_id):
    db = get_db(); sub = db.execute('SELECT * FROM constructed_submissions WHERE id=?', (submission_id,)).fetchone()
    if not sub: abort(404)
    score = max(0, min(4, int(request.form.get('rubric_score', 0)))); comment = request.form.get('teacher_comment', '').strip(); now = utcnow()
    db.execute('UPDATE constructed_submissions SET rubric_score=?,teacher_comment=?,reviewed_at=? WHERE id=?', (score, comment, now, submission_id))
    p = db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?', (sub['user_id'], sub['lesson_id'])).fetchone()
    constructed_items = db.execute("SELECT id FROM assessment_items WHERE lesson_id=? AND item_type='constructed'", (sub['lesson_id'],)).fetchall()
    rubric_scores = []
    for i in constructed_items:
        r = db.execute('''SELECT rubric_score FROM constructed_submissions WHERE user_id=? AND lesson_id=? AND item_id=? AND rubric_score IS NOT NULL ORDER BY reviewed_at DESC LIMIT 1''',
                       (sub['user_id'], sub['lesson_id'], i['id'])).fetchone()
        if r: rubric_scores.append(r['rubric_score'])
    if constructed_items and len(rubric_scores) == len(constructed_items):
        rubric_pct = 100.0 * sum(rubric_scores) / (4 * len(rubric_scores)); final = 0.70 * p['best_auto_score'] + 0.30 * rubric_pct
        status = 'mastered' if final >= MASTER else 'remediation'
        db.execute('UPDATE progress SET final_score=?,status=? WHERE user_id=? AND lesson_id=?', (final, status, sub['user_id'], sub['lesson_id']))
        year_id = current_academic_year_id(db)
        db.execute('INSERT INTO grade_events(user_id,lesson_id,auto_score,final_score,status,completed_at,academic_year_id) VALUES (?,?,?,?,?,?,?)',
                   (sub['user_id'], sub['lesson_id'], p['best_auto_score'], final, status, now, year_id))
    db.commit(); flash('Constructed response reviewed and lesson grade recalculated when all rubric items are complete.')
    return redirect(url_for('main.admin'))


@bp.route('/admin/export/grades.csv')
@login_required(role=('admin', 'parent'))
def export_grades():
    student_id = request.args.get('student_id', type=int)
    if session.get('role') == 'parent':
        if not student_id or not can_view_student(student_id): abort(403)
    return Response(csv_for_grades(student_id), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=richmack_georgia_gradebook.csv'})


def gradebook_for_year(year_id, student_id=None, limit=200):
    db=get_db(); params=[year_id]; student_clause=''
    if student_id:
        student_clause=' AND u.id=?'; params.append(student_id)
    rows=db.execute(f'''SELECT 'coursework' record_type,u.display_name student,u.id student_id,c.title course,m.title module,
       l.title activity,g.auto_score score,g.final_score,g.status,g.completed_at
       FROM grade_events g JOIN users u ON u.id=g.user_id JOIN lessons l ON l.id=g.lesson_id
       JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
       WHERE u.role='student' AND g.academic_year_id=? {student_clause}
       UNION ALL
       SELECT 'game',u.display_name,u.id,'Games','Map Skills','Map Hunt',ga.score,ga.score,
       CASE WHEN ga.score>=85 THEN 'mastered' ELSE 'practice' END,ga.completed_at
       FROM game_attempts ga JOIN users u ON u.id=ga.user_id
       WHERE u.role='student' AND ga.academic_year_id=? {student_clause}
       ORDER BY completed_at DESC LIMIT ?''', params + [year_id] + ([student_id] if student_id else []) + [limit]).fetchall()
    return rows


@bp.route('/admin/assignments', methods=['POST'])
@login_required(role=('admin','parent'))
def create_assignment():
    db=get_db(); student_id=request.form.get('student_id',type=int)
    if not student_id or not db.execute("SELECT 1 FROM users WHERE id=? AND role='student' AND active=1",(student_id,)).fetchone(): abort(400)
    if session.get('role')=='parent' and not can_view_student(student_id): abort(403)
    lesson_id=request.form.get('lesson_id',type=int); module_id=request.form.get('module_id',type=int)
    target_type=request.form.get('target_type','module')
    if target_type=='lesson': module_id=None
    else: lesson_id=None
    if bool(lesson_id)==bool(module_id):
        flash('Choose exactly one module or lesson to assign.')
        return redirect(request.referrer or url_for('main.admin'))
    if lesson_id:
        target=db.execute('SELECT title FROM lessons WHERE id=?',(lesson_id,)).fetchone()
    else:
        target=db.execute('SELECT title FROM modules WHERE id=?',(module_id,)).fetchone()
    if not target: abort(400)
    min_score=max(0,min(100,float(request.form.get('min_score',85) or 85)))
    due=(request.form.get('due_date') or '').strip() or None
    year_id=current_academic_year_id(db)
    db.execute('''INSERT INTO assignments(created_by,student_id,lesson_id,module_id,title,due_date,min_score,academic_year_id,created_at)
                  VALUES (?,?,?,?,?,?,?,?,?)''',(session['user_id'],student_id,lesson_id,module_id,target['title'],due,min_score,year_id,utcnow()))
    db.commit(); flash(f"Assigned {target['title']} with a {min_score:.0f}% target.")
    return redirect(request.referrer or url_for('main.admin'))


@bp.route('/admin/assignments/<int:assignment_id>/archive', methods=['POST'])
@login_required(role=('admin','parent'))
def archive_assignment(assignment_id):
    db=get_db(); a=db.execute('SELECT * FROM assignments WHERE id=?',(assignment_id,)).fetchone()
    if not a: abort(404)
    if session.get('role')=='parent' and not can_view_student(a['student_id']): abort(403)
    db.execute('UPDATE assignments SET archived=1 WHERE id=?',(assignment_id,)); db.commit(); flash('Assignment archived.')
    return redirect(request.referrer or url_for('main.admin'))


@bp.route('/admin/academic-years', methods=['POST'])
@login_required(role='admin')
def create_academic_year():
    db=get_db(); name=request.form.get('name','').strip(); starts=request.form.get('starts_on','').strip(); ends=request.form.get('ends_on','').strip()
    if not name or not starts or not ends or starts>=ends:
        flash('Enter a name and a valid start/end date range.')
    else:
        db.execute('INSERT OR IGNORE INTO academic_years(name,starts_on,ends_on,active) VALUES (?,?,?,0)',(name,starts,ends)); db.commit(); flash(f'Academic year {name} added.')
    return redirect(url_for('main.admin'))


@bp.route('/admin/academic-years/<int:year_id>/activate', methods=['POST'])
@login_required(role='admin')
def activate_academic_year(year_id):
    db=get_db()
    if not db.execute('SELECT 1 FROM academic_years WHERE id=?',(year_id,)).fetchone(): abort(404)
    db.execute('UPDATE academic_years SET active=0'); db.execute('UPDATE academic_years SET active=1 WHERE id=?',(year_id,)); db.commit(); flash('Active academic year changed. New grades and assignments will use it.')
    return redirect(url_for('main.admin'))


@bp.route('/admin/gradebook')
@login_required(role=('admin','parent'))
def academic_gradebook():
    db=get_db(); year_id=request.args.get('year_id',type=int) or current_academic_year_id(db); student_id=request.args.get('student_id',type=int)
    if session.get('role')=='parent':
        if not student_id or not can_view_student(student_id): abort(403)
        years=db.execute('''SELECT DISTINCT ay.* FROM academic_years ay LEFT JOIN grade_events g ON g.academic_year_id=ay.id AND g.user_id=?
                            LEFT JOIN game_attempts ga ON ga.academic_year_id=ay.id AND ga.user_id=?
                            WHERE g.id IS NOT NULL OR ga.id IS NOT NULL OR ay.active=1 ORDER BY ay.starts_on DESC''',(student_id,student_id)).fetchall()
        students=db.execute('SELECT u.id,u.display_name FROM users u JOIN parent_student_links p ON p.student_id=u.id WHERE p.parent_id=? ORDER BY u.display_name',(session['user_id'],)).fetchall()
    else:
        years=db.execute('SELECT * FROM academic_years ORDER BY starts_on DESC').fetchall(); students=db.execute("SELECT id,display_name FROM users WHERE role='student' ORDER BY display_name").fetchall()
    year=db.execute('SELECT * FROM academic_years WHERE id=?',(year_id,)).fetchone()
    rows=gradebook_for_year(year_id,student_id)
    return render_template('gradebook.html',year=year,years=years,rows=rows,students=students,student_id=student_id)
