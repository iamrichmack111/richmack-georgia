from app import create_app


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_admin_dashboard_redirects_to_admin(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path/'t.db'))
    app=create_app({'TESTING':True})
    c=app.test_client(); login(c,'admin','change-me-local')
    r=c.get('/dashboard', follow_redirects=False)
    assert r.status_code in (301,302)
    assert '/admin' in r.headers['Location']


def test_student_grade_visible_in_admin(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path/'t2.db'))
    app=create_app({'TESTING':True})
    s=app.test_client(); login(s,'student14','student14')
    # Reservoir-to-tap: correct numeric + mcq; constructed response present => provisional 100.
    with app.app_context():
        from app.db import get_db
        db=get_db(); lesson=db.execute("SELECT id FROM lessons WHERE slug='reservoir-to-tap'").fetchone()
        items=db.execute("SELECT * FROM assessment_items WHERE lesson_id=? ORDER BY sort_order,id",(lesson['id'],)).fetchall()
    data={}
    for i in items:
        if i['item_type']=='numeric': data[f"i{i['id']}"]=str(i['numeric_answer'])
        elif i['item_type']=='mcq': data[f"i{i['id']}"]=i['correct_text']
        else: data[f"i{i['id']}"]='I would check peak demand, drought source limits, maintenance outages, and projected growth before approval.'
    r=s.post('/lesson/reservoir-to-tap',data=data,follow_redirects=True)
    assert b'100.0%' in r.data
    a=app.test_client(); login(a,'admin','change-me-local')
    r=a.get('/admin')
    assert b'Age 14 Test Student' in r.data
    assert b'100.0%' in r.data
    assert b'provisional' in r.data
