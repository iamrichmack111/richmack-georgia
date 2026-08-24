from app import create_app


def app_client(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'phase5.db'),'SECRET_KEY':'test-secret'})
    return app, app.test_client()


def login(c,u,p):
    return c.post('/login',data={'username':u,'password':p},follow_redirects=True)


def test_health_and_phase5_seed(tmp_path):
    app,c=app_client(tmp_path)
    assert c.get('/health').json['phase']=='5.0'
    with app.app_context():
        from app.db import get_db
        db=get_db()
        assert db.execute('SELECT COUNT(*) n FROM modules').fetchone()['n'] >= 6
        assert db.execute('SELECT COUNT(*) n FROM skills').fetchone()['n'] >= 16
        assert db.execute("SELECT COUNT(*) n FROM lessons WHERE slug IN ('five-regions-constraints','business-expansion-capstone')").fetchone()['n']==2
        assert db.execute('SELECT COUNT(*) n FROM academic_years WHERE active=1').fetchone()['n']==1


def test_parent_assignment_is_scoped_and_student_sees_it(tmp_path):
    app,a=app_client(tmp_path); login(a,'admin','change-me-local')
    with app.app_context():
        from app.db import get_db
        db=get_db(); sid=db.execute("SELECT id FROM users WHERE username='student14'").fetchone()['id']; mid=db.execute("SELECT id FROM modules WHERE slug='physical-geography-module'").fetchone()['id']
    r=a.post('/admin/assignments',data={'student_id':sid,'target_type':'module','module_id':mid,'min_score':'85'},follow_redirects=True)
    assert b'Assigned' in r.data
    s=app.test_client(); login(s,'student14','student14'); page=s.get('/dashboard')
    assert b'Physical Geography' in page.data and b'My Assignments' in page.data


def test_skill_breakdown_from_map_game(tmp_path):
    app,s=app_client(tmp_path); login(s,'student14','student14')
    r=s.post('/api/games/map-hunt/score',json={'correct':8,'total':10,'duration_seconds':90,'skill_breakdown':{'rivers':{'correct':2,'total':3},'transportation':{'correct':3,'total':3}}})
    assert r.status_code==200
    with app.app_context():
        from app.db import get_db
        rows=get_db().execute("SELECT skill_key,score FROM game_skill_attempts ORDER BY skill_key").fetchall()
        assert len(rows)==2


def test_academic_year_gradebook(tmp_path):
    app,s=app_client(tmp_path); login(s,'student14','student14')
    s.post('/api/games/map-hunt/score',json={'correct':9,'total':10,'duration_seconds':60})
    a=app.test_client(); login(a,'admin','change-me-local')
    page=a.get('/admin/gradebook')
    assert page.status_code==200 and b'2026' in page.data and b'Map Hunt' in page.data
