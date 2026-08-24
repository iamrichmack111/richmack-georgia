import os
from app import create_app


def app_client(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'phase4.db'),'SECRET_KEY':'test-secret'})
    return app, app.test_client()


def login(c,u,p):
    return c.post('/login',data={'username':u,'password':p},follow_redirects=True)


def test_health_phase4(tmp_path):
    app,c=app_client(tmp_path)
    r=c.get('/health'); assert r.status_code==200; assert r.json['phase']=='4.0'


def test_game_score_is_in_gradebook_and_csv(tmp_path):
    app,s=app_client(tmp_path); login(s,'student14','student14')
    r=s.post('/api/games/map-hunt/score',json={'correct':9,'total':10,'duration_seconds':120})
    assert r.status_code==200 and r.json['score']==90.0
    a=app.test_client(); login(a,'admin','change-me-local')
    page=a.get('/admin'); assert b'Map Hunt' in page.data and b'90.0%' in page.data and b'Game' in page.data
    csv=a.get('/admin/export/grades.csv'); assert b'Map Hunt' in csv.data and b'game' in csv.data and b'90.0' in csv.data


def test_admin_can_disable_games_and_reset_password(tmp_path):
    app,a=app_client(tmp_path); login(a,'admin','change-me-local')
    with app.app_context():
        from app.db import get_db
        uid=get_db().execute("SELECT id FROM users WHERE username='student14'").fetchone()['id']
    a.post(f'/admin/users/{uid}/update',data={'active':'on','allow_courses':'on','allow_map':'on'},follow_redirects=True)
    s=app.test_client(); login(s,'student14','student14')
    r=s.get('/games',follow_redirects=True); assert b'restricted' in r.data.lower()
    a.post(f'/admin/users/{uid}/password',data={'new_password':'Temporary123'},follow_redirects=True)
    s2=app.test_client(); r=login(s2,'student14','Temporary123'); assert b'Change Password' in r.data


def test_parent_invite_register_and_scope(tmp_path):
    app,a=app_client(tmp_path); login(a,'admin','change-me-local')
    with app.app_context():
        from app.db import get_db
        sid=get_db().execute("SELECT id FROM users WHERE username='student14'").fetchone()['id']
    a.post('/admin/invites',data={'student_id':sid},follow_redirects=True)
    with app.app_context():
        from app.db import get_db
        token=get_db().execute('SELECT token FROM parent_invites ORDER BY id DESC LIMIT 1').fetchone()['token']
    p=app.test_client(); r=p.post(f'/invite/{token}',data={'display_name':'Parent One','username':'parent1','password':'ParentPass1','confirm_password':'ParentPass1'},follow_redirects=True)
    assert b'Login' in r.data or b'sign in' in r.data.lower()
    login(p,'parent1','ParentPass1'); r=p.get('/parent'); assert b'Age 14 Test Student' in r.data
