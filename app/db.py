import csv
import io
import os
import sqlite3
from datetime import datetime, timezone
from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(_e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('admin','student')),
  age INTEGER
);
CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  agency TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  verified_on TEXT NOT NULL,
  refresh_days INTEGER NOT NULL DEFAULT 365
);
CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  sort_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY,
  course_id INTEGER NOT NULL REFERENCES courses(id),
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  min_age INTEGER NOT NULL,
  max_age INTEGER NOT NULL,
  summary TEXT NOT NULL,
  content TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  xp INTEGER NOT NULL DEFAULT 25,
  sort_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  prompt TEXT NOT NULL,
  choice_a TEXT NOT NULL,
  choice_b TEXT NOT NULL,
  choice_c TEXT NOT NULL,
  choice_d TEXT NOT NULL,
  correct TEXT NOT NULL CHECK(correct IN ('A','B','C','D')),
  explanation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS progress (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  best_score REAL NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  completed INTEGER NOT NULL DEFAULT 0,
  mastery REAL NOT NULL DEFAULT 0,
  last_completed_at TEXT,
  UNIQUE(user_id, lesson_id)
);
CREATE TABLE IF NOT EXISTS grade_events (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  score REAL NOT NULL,
  correct_count INTEGER NOT NULL,
  question_count INTEGER NOT NULL,
  completed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS game_attempts (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  game_key TEXT NOT NULL,
  score REAL NOT NULL,
  correct_count INTEGER NOT NULL,
  question_count INTEGER NOT NULL,
  duration_seconds INTEGER NOT NULL DEFAULT 0,
  completed_at TEXT NOT NULL
);
'''

SOURCES = [
('Georgia Social Studies', 'Georgia Department of Education', 'https://gadoe.org/learning/social-studies/', 'standards', '2026-08-24', 180),
('Watershed Protection Branch', 'Georgia Environmental Protection Division', 'https://epd.georgia.gov/about-us/watershed-protection-branch', 'water', '2026-08-24', 90),
('Water Supply Watersheds', 'Georgia Environmental Protection Division', 'https://epd.georgia.gov/water-supply-watersheds', 'gis', '2026-08-24', 90),
('Road & Traffic Data', 'Georgia Department of Transportation', 'https://www.dot.ga.gov/GDOT/Pages/RoadTrafficData.aspx', 'transportation', '2026-08-24', 90),
('Georgia Highway & Transportation Maps', 'Georgia Department of Transportation', 'https://www.dot.ga.gov/GDOT/Pages/Maps.aspx', 'transportation', '2026-08-24', 90),
('Georgia Geologic Survey Maps', 'Georgia Environmental Protection Division', 'https://epd.georgia.gov/outreach/publications/georgia-geologic-survey-maps', 'geology', '2026-08-24', 365),
('QuickFacts: Georgia', 'U.S. Census Bureau', 'https://www.census.gov/quickfacts/fact/table/GA/PST045223', 'economics', '2026-08-24', 90),
]
COURSES = [
('Georgia Foundations','foundations','Map skills, regions, counties, cities, and major geographic features.',1),
('Rivers & Water Systems','water','Rivers, watersheds, reservoirs, drinking water, stormwater, and wastewater.',2),
('Infrastructure & Economy','infrastructure','Roads, rail, ports, airports, utilities, logistics, and Georgia business systems.',3),
('Georgia History & Communities','history','How people, places, geography, and historical events shaped Georgia.',4),
]
LESSONS = [
('foundations','Georgia’s Five Geographic Regions','five-regions',9,14,'Learn the five major geographic regions of Georgia and how landforms influence settlement and work.',
'''Georgia can be studied through five major physiographic regions: Appalachian Plateau, Ridge and Valley, Blue Ridge, Piedmont, and Coastal Plain. A physiographic region is an area with a recognizable pattern of landforms and geology.\n\nFor ages 9–10, focus on locating each region and comparing mountains, hills, and flatter land. For ages 11–12, connect regions to cities, agriculture, and transportation. For ages 13–14, ask how geology, elevation, resources, and infrastructure influence economic activity and settlement.''','Georgia Social Studies',25,1),
('water','Georgia Water Systems: From Watershed to Tap','watershed-to-tap',9,14,'Understand watersheds and how Georgia manages drinking water, wastewater, and stormwater.',
'''A watershed is the land area that drains toward a common body of water. Georgia EPD’s Watershed Protection Branch manages regulatory and protection programs involving drinking water, wastewater discharges, stormwater, water withdrawals, dam safety, drought management, and water-quality monitoring.\n\nThink of the system as a cycle: rain falls on a watershed; water enters streams and reservoirs; public systems treat drinking water; homes and businesses use it; wastewater systems treat used water; and treated water is returned to the environment under permits and standards. Stormwater is different because rain can run from streets and land directly toward streams, carrying pollution with it.''','Watershed Protection Branch',35,1),
('infrastructure','How Georgia Moves: Roads and Traffic Data','ga-transportation-network',10,14,'Explore why roads, traffic measurement, rail, ports, and airports matter to Georgia communities and business.',
'''Transportation infrastructure connects households, schools, farms, factories, stores, ports, and airports. Georgia DOT collects traffic information from public roads and makes traffic counts and reports available through its transportation-data systems.\n\nFor younger students, identify major routes and the places they connect. Older students should compare transportation choices: Which mode is fast? Which carries the most freight? Why do businesses build near highway interchanges, rail lines, airports, or ports?''','Road & Traffic Data',30,1),
('infrastructure','Georgia by the Numbers','georgia-by-the-numbers',11,14,'Use Census data to interpret population and economic change rather than memorizing a frozen statistic.',
'''The U.S. Census Bureau publishes official population and community statistics. Its July 1, 2025 population estimate for Georgia was 11,302,748. Because population changes over time, good geographic study includes both the number and the date of the estimate.\n\nStudents should learn to ask: What year is this statistic from? Is it an estimate or a census count? How could population growth affect roads, schools, water systems, housing, and jobs?''','QuickFacts: Georgia',30,2),
]
QUESTIONS = {
'five-regions': [
('Which term describes an area with a recognizable pattern of landforms and geology?','Watershed','Physiographic region','County seat','Trade corridor','B','A physiographic region groups places by physical landform and geologic characteristics.'),
('Which learning goal goes beyond simply naming regions?','Connect regions to settlement and economic activity','Memorize only their colors','Ignore elevation','Treat every region as physically identical','A','Geography becomes useful when students connect landforms to people, infrastructure, and economic choices.'),
],
'watershed-to-tap': [
('What is a watershed?','A building where water is bottled','Land that drains toward a common body of water','Only a large dam','A sewer pipe','B','A watershed is defined by where water drains across the landscape.'),
('Which activity is part of Georgia EPD watershed responsibilities?','Issuing driver licenses','Managing wastewater and water-withdrawal permits','Running school cafeterias','Building every local road','B','Georgia EPD oversees multiple water-resource regulatory and monitoring programs.'),
('Why is stormwater important?','Runoff can carry pollution into waterways','It never reaches streams','It is always drinking water','It happens only near the coast','A','Stormwater runoff can move pollutants from land and streets into receiving waters.'),
],
'ga-transportation-network': [
('Why does Georgia DOT collect traffic counts?','To understand use of the transportation system','To count fish','To set school grades','To predict rainfall','A','Traffic counts help describe how public roads are being used.'),
('Why might a warehouse locate near a major highway?','To improve access for moving goods','To avoid all transportation','Because highways create rivers','Because roads replace electricity','A','Location near transportation can reduce time and complexity for freight movement.'),
],
'georgia-by-the-numbers': [
('What was Georgia’s July 1, 2025 population estimate in the seeded Census lesson?','11,302,748','159','1,000,000','341,784,857','A','The lesson uses the Census Bureau’s V2025 estimate for Georgia.'),
('Why should a statistic include its date?','Statistics can change over time','Dates make every number larger','A date turns estimates into laws','Dates are only needed for maps','A','Population and economic statistics must be interpreted in time context.'),
]
}


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    # Seed users only once.
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    admin_pw = os.getenv('ADMIN_PASSWORD', 'change-me-local')
    student_user = os.getenv('STUDENT_USERNAME', 'student')
    student_pw = os.getenv('STUDENT_PASSWORD', 'student')
    db.execute('INSERT OR IGNORE INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
               (admin_user, generate_password_hash(admin_pw), 'Local Administrator', 'admin', None))
    db.execute('INSERT OR IGNORE INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
               (student_user, generate_password_hash(student_pw), 'Demo Student', 'student', 12))
    for row in SOURCES:
        db.execute('INSERT OR IGNORE INTO sources(name,agency,url,category,verified_on,refresh_days) VALUES (?,?,?,?,?,?)', row)
    for row in COURSES:
        db.execute('INSERT OR IGNORE INTO courses(title,slug,description,sort_order) VALUES (?,?,?,?)', row)
    db.commit()
    source_ids = {r['name']: r['id'] for r in db.execute('SELECT id,name FROM sources')}
    course_ids = {r['slug']: r['id'] for r in db.execute('SELECT id,slug FROM courses')}
    for course_slug,title,slug,min_age,max_age,summary,content,source_name,xp,sort_order in LESSONS:
        db.execute('''INSERT OR IGNORE INTO lessons(course_id,title,slug,min_age,max_age,summary,content,source_id,xp,sort_order)
                      VALUES (?,?,?,?,?,?,?,?,?,?)''',
                   (course_ids[course_slug],title,slug,min_age,max_age,summary,content,source_ids[source_name],xp,sort_order))
    db.commit()
    lesson_ids = {r['slug']: r['id'] for r in db.execute('SELECT id,slug FROM lessons')}
    for slug, questions in QUESTIONS.items():
        lid = lesson_ids[slug]
        existing = db.execute('SELECT COUNT(*) AS n FROM questions WHERE lesson_id=?',(lid,)).fetchone()['n']
        if not existing:
            for q in questions:
                db.execute('''INSERT INTO questions(lesson_id,prompt,choice_a,choice_b,choice_c,choice_d,correct,explanation)
                              VALUES (?,?,?,?,?,?,?,?)''',(lid,*q))
    db.commit()
    current_app.teardown_appcontext(close_db)


def csv_for_grades(user_id=None):
    db = get_db()
    sql = '''SELECT u.display_name student, u.age, c.title course, l.title lesson,
                    g.score, g.correct_count, g.question_count, g.completed_at
             FROM grade_events g JOIN users u ON u.id=g.user_id
             JOIN lessons l ON l.id=g.lesson_id JOIN courses c ON c.id=l.course_id'''
    params = []
    if user_id:
        sql += ' WHERE u.id=?'
        params.append(user_id)
    sql += ' ORDER BY g.completed_at DESC'
    rows = db.execute(sql, params).fetchall()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['student','age','course','lesson','score_percent','correct','questions','completed_at'])
    for r in rows:
        w.writerow([r['student'],r['age'],r['course'],r['lesson'],f"{r['score']:.1f}",r['correct_count'],r['question_count'],r['completed_at']])
    return out.getvalue()


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
