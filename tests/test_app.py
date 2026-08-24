import os
import tempfile
from app import create_app


def app_client():
    fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
    app=create_app({'TESTING':True,'DATABASE':path,'SECRET_KEY':'test'})
    return app.test_client(),path


def login(client,user,pw):
    return client.post('/login',data={'username':user,'password':pw},follow_redirects=True)


def test_health_and_seed():
    c,path=app_client()
    try:
        r=c.get('/health'); assert r.status_code==200; assert r.json['phase']==3
        r=login(c,'student','student'); assert b'Phase 3 Modules' in r.data
        assert b'Water Systems' in r.data and b'Transportation' in r.data
    finally: os.unlink(path)


def test_deep_lesson_and_admin():
    c,path=app_client()
    try:
        login(c,'student','student')
        r=c.get('/lesson/water-capstone'); assert r.status_code==200
        assert b'120' in r.data and b'Remediation' in r.data
        c.get('/logout'); login(c,'admin','change-me-local')
        r=c.get('/admin'); assert r.status_code==200; assert b'Constructed Responses' in r.data
        r=c.get('/admin/export/grades.csv'); assert r.status_code==200
    finally: os.unlink(path)
