import os
import tempfile
import pytest
from app import create_app

@pytest.fixture()
def client():
    fd, path=tempfile.mkstemp(suffix='.db'); os.close(fd)
    app=create_app({'TESTING':True,'DATABASE':path,'SECRET_KEY':'test'})
    with app.test_client() as c:
        yield c
    os.unlink(path)

def login(c,u,p):
    return c.post('/login',data={'username':u,'password':p},follow_redirects=True)

def test_health(client):
    r=client.get('/health'); assert r.status_code==200; assert r.json['status']=='ok'

def test_home_and_map(client):
    assert client.get('/').status_code==200
    r=client.get('/map'); assert r.status_code==200; assert b'Leaflet' in r.data

def test_student_quiz_records_grade(client):
    r=login(client,'student','student'); assert b'Georgia Journey' in r.data
    page=client.get('/lesson/watershed-to-tap'); assert page.status_code==200
    # seeded question ids are deterministic in new test DB: regions 1-2, water 3-5
    r=client.post('/lesson/watershed-to-tap',data={'q3':'B','q4':'B','q5':'A'},follow_redirects=True)
    assert b'Score: 100%' in r.data

def test_admin_csv_export(client):
    r=login(client,'admin','change-me-local'); assert b'Academic Dashboard' in r.data
    r=client.get('/admin/export/grades.csv'); assert r.status_code==200; assert b'score_percent' in r.data
