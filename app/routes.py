from functools import wraps
import secrets
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db, csv_for_grades, gradebook_rows, utcnow

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
    return {'status': 'ok', 'app': 'richmack-georgia', 'phase': '4.0'}, 200


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
      GROUP BY m.id ORDER BY c.sort_order,m.sort_order''', (uid,)).fetchall()
    lessons = db.execute('''SELECT l.*,m.title module_title,c.title course_title,p.best_auto_score,p.final_score,p.status
      FROM lessons l JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
      LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? ORDER BY c.sort_order,m.sort_order,l.sort_order''', (uid,)).fetchall()
    summary = db.execute('''SELECT COUNT(*) attempted,
      SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END) mastered,
      SUM(CASE WHEN status='provisional' THEN 1 ELSE 0 END) provisional,
      COALESCE(AVG(CASE WHEN final_score IS NOT NULL THEN final_score ELSE best_auto_score END),0) avg_score
      FROM progress WHERE user_id=?''', (uid,)).fetchone()
    game_stats = db.execute('''SELECT COUNT(*) attempts,COALESCE(MAX(score),0) best_score,COALESCE(AVG(score),0) avg_score,
                               COALESCE(SUM(duration_seconds),0) seconds FROM game_attempts WHERE user_id=?''', (uid,)).fetchone()
    tips = build_tips(uid)
    record_usage('view', 'dashboard')
    return render_template('dashboard.html', modules=modules, lessons=lessons, summary=summary, game_stats=game_stats,
                           tips=tips, user=u)


@bp.route('/module/<slug>')
@login_required(role='student', permission='allow_courses')
def module_view(slug):
    db = get_db(); uid = session['user_id']
    module = db.execute('''SELECT m.*,c.title course_title FROM modules m JOIN courses c ON c.id=m.course_id WHERE m.slug=?''', (slug,)).fetchone()
    if not module: abort(404)
    lessons = db.execute('''SELECT l.*,p.best_auto_score,p.final_score,p.status FROM lessons l
       LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? WHERE l.module_id=? ORDER BY l.sort_order''', (uid, module['id'])).fetchall()
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
        db.execute('INSERT INTO grade_events(user_id,lesson_id,auto_score,final_score,status,completed_at) VALUES (?,?,?,?,?,?)',
                   (uid, lesson['id'], auto, final, status, now))
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
    db.execute('INSERT INTO game_attempts(user_id,game_key,score,correct_count,question_count,duration_seconds,completed_at) VALUES (?,?,?,?,?,?,?)',
               (session['user_id'], 'map-hunt', score, correct, total, duration, now))
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
    return render_template('admin.html', students=students, pending=pending, latest_grades=latest_grades, sources=sources, invites=invites)


@bp.route('/admin/student/<int:student_id>')
@login_required(role=('admin', 'parent'))
def student_report(student_id):
    if not can_view_student(student_id): abort(403)
    student, grade_rows, lesson_stats, game_stats, usage, recent, tips = student_report_data(student_id)
    return render_template('student_report.html', student=student, grade_rows=grade_rows, lesson_stats=lesson_stats,
                           game_stats=game_stats, usage=usage, recent=recent, tips=tips)


@bp.route('/parent')
@login_required(role='parent')
def parent_portal():
    db = get_db()
    students = db.execute('''SELECT u.* FROM users u JOIN parent_student_links psl ON psl.student_id=u.id
                             WHERE psl.parent_id=? ORDER BY u.display_name''', (session['user_id'],)).fetchall()
    return render_template('parent.html', students=students)


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
            else:
                db.execute("INSERT OR IGNORE INTO parent_student_links(parent_id,student_id) SELECT ?,id FROM users WHERE role='student'", (parent_id,))
            db.execute('UPDATE parent_invites SET used_at=? WHERE id=?', (utcnow(), inv['id']))
            db.commit(); flash('Parent account created. You can sign in now.')
            return redirect(url_for('main.login'))
    student = db.execute('SELECT display_name FROM users WHERE id=?', (inv['student_id'],)).fetchone() if inv['student_id'] else None
    return render_template('invite.html', invite=inv, student=student, invalid=False)


@bp.route('/admin/users')
@login_required(role='admin')
def manage_users():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY role,display_name').fetchall()
    students = db.execute("SELECT id,display_name,age,active FROM users WHERE role='student' ORDER BY display_name").fetchall()
    parent_links = {}
    for row in db.execute('SELECT parent_id,student_id FROM parent_student_links'):
        parent_links.setdefault(row['parent_id'], set()).add(row['student_id'])
    return render_template('users.html', users=users, students=students, parent_links=parent_links)


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
        db.execute('INSERT INTO grade_events(user_id,lesson_id,auto_score,final_score,status,completed_at) VALUES (?,?,?,?,?,?)',
                   (sub['user_id'], sub['lesson_id'], p['best_auto_score'], final, status, now))
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
