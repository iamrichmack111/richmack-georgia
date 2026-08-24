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
  role TEXT NOT NULL CHECK(role IN ('admin','student','parent')),
  age INTEGER,
  active INTEGER NOT NULL DEFAULT 1,
  allow_courses INTEGER NOT NULL DEFAULT 1,
  allow_map INTEGER NOT NULL DEFAULT 1,
  allow_games INTEGER NOT NULL DEFAULT 1,
  must_change_password INTEGER NOT NULL DEFAULT 0,
  last_login_at TEXT
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
CREATE TABLE IF NOT EXISTS modules (
  id INTEGER PRIMARY KEY,
  course_id INTEGER NOT NULL REFERENCES courses(id),
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  essential_question TEXT NOT NULL,
  mastery_threshold REAL NOT NULL DEFAULT 85,
  sort_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY,
  module_id INTEGER NOT NULL REFERENCES modules(id),
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  min_age INTEGER NOT NULL,
  max_age INTEGER NOT NULL,
  summary TEXT NOT NULL,
  learning_objectives TEXT NOT NULL,
  content TEXT NOT NULL,
  worked_example TEXT NOT NULL,
  remediation TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  xp INTEGER NOT NULL DEFAULT 40,
  sort_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS assessment_items (
  id INTEGER PRIMARY KEY,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  item_type TEXT NOT NULL CHECK(item_type IN ('mcq','numeric','constructed')),
  prompt TEXT NOT NULL,
  choice_a TEXT,
  choice_b TEXT,
  choice_c TEXT,
  choice_d TEXT,
  correct_text TEXT,
  numeric_answer REAL,
  numeric_tolerance REAL DEFAULT 0,
  explanation TEXT NOT NULL,
  rubric TEXT,
  points REAL NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS progress (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  best_auto_score REAL NOT NULL DEFAULT 0,
  final_score REAL,
  attempts INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'not_started' CHECK(status IN ('not_started','remediation','provisional','mastered')),
  last_completed_at TEXT,
  UNIQUE(user_id, lesson_id)
);
CREATE TABLE IF NOT EXISTS grade_events (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  auto_score REAL NOT NULL,
  final_score REAL,
  status TEXT NOT NULL,
  completed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS constructed_submissions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  item_id INTEGER NOT NULL REFERENCES assessment_items(id),
  response_text TEXT NOT NULL,
  rubric_score INTEGER CHECK(rubric_score BETWEEN 0 AND 4),
  teacher_comment TEXT,
  submitted_at TEXT NOT NULL,
  reviewed_at TEXT
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
CREATE TABLE IF NOT EXISTS parent_invites (
  id INTEGER PRIMARY KEY,
  token TEXT UNIQUE NOT NULL,
  created_by INTEGER NOT NULL REFERENCES users(id),
  student_id INTEGER REFERENCES users(id),
  expires_at TEXT,
  used_at TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS parent_student_links (
  parent_id INTEGER NOT NULL REFERENCES users(id),
  student_id INTEGER NOT NULL REFERENCES users(id),
  PRIMARY KEY(parent_id,student_id)
);
CREATE TABLE IF NOT EXISTS usage_events (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  event_type TEXT NOT NULL,
  endpoint TEXT,
  duration_seconds INTEGER NOT NULL DEFAULT 0,
  detail TEXT,
  created_at TEXT NOT NULL
);
'''

SOURCES = [
('Georgia Social Studies', 'Georgia Department of Education', 'https://gadoe.org/learning/social-studies/', 'standards', '2026-08-24', 180),
('Watershed Protection Branch', 'Georgia Environmental Protection Division', 'https://epd.georgia.gov/watershed-protection-branch-2', 'water', '2026-08-24', 90),
('Water Supply Watersheds', 'Georgia Environmental Protection Division', 'https://epd.georgia.gov/water-supply-watersheds', 'gis', '2026-08-24', 90),
('Wastewater Program', 'Georgia Environmental Protection Division', 'https://epd.georgia.gov/watershed-protection-branch/wastewater', 'water', '2026-08-24', 90),
('Road & Traffic Data', 'Georgia Department of Transportation', 'https://www.dot.ga.gov/GDOT/Pages/RoadTrafficData.aspx', 'transportation', '2026-08-24', 90),
('Port of Savannah', 'Georgia Ports Authority', 'https://gaports.com/facilities/port-of-savannah/', 'transportation', '2026-08-24', 90),
('QuickFacts: Georgia', 'U.S. Census Bureau', 'https://www.census.gov/quickfacts/fact/table/GA/PST045225', 'economics', '2026-08-24', 90),
]

COURSES = [
('Georgia Water Systems','water-systems','Watersheds, drinking water, wastewater, stormwater, capacity, and civic decision-making.',1),
('Transportation & Logistics','transport-logistics','Roads, rail, ports, freight, location decisions, and the economics of moving goods.',2),
]

MODULES = [
('water-systems','Module 1 — Georgia Water Systems','water-systems-module','Follow water from watershed to tap to treatment and back to the environment.','How should a growing Georgia community manage a limited water system responsibly?',1),
('transport-logistics','Module 2 — Transportation & Logistics','transport-logistics-module','Study how roads, rail, ports, geography, and costs shape Georgia freight decisions.','Why do transportation networks change where businesses locate and how Georgia competes?',1),
]

LESSONS = [
('water-systems-module','1.1 Watersheds: Geography Controls Flow','watersheds-control-flow',9,14,
 'Learn why watershed boundaries matter and practice reasoning about upstream and downstream effects.',
 'Define watershed and drainage divide; infer downstream effects from a map; distinguish a watershed from a political boundary.',
 '''A watershed is the land area that drains toward a common stream, river, lake, or other receiving water. Watershed boundaries follow high ground rather than county lines. That means two homes in the same county can send runoff toward different streams, while communities in different counties can share the same downstream river.\n\nGeorgia EPD uses watershed monitoring, assessment, planning, permitting, and modeling to protect water resources. The practical lesson is that actions upstream can create consequences downstream. Rain moving across parking lots can pick up oil, sediment, litter, fertilizer, and other pollutants before reaching a stream. A wastewater discharge also enters a receiving water at a specific location, so downstream conditions matter.\n\nGeography therefore controls part of the problem. A city cannot manage water only by looking at its city limits. It has to understand the larger drainage system, upstream land uses, downstream users, reservoirs, water intakes, permitted discharges, and drought conditions. Good water decisions are systems decisions.''',
 '''Worked example: A school and a farm are both upstream of the same creek. Heavy rain washes sediment from bare soil and runoff from the school parking lot into tributaries. Those tributaries meet before reaching a town reservoir. Even though the pollution sources are separated geographically, the watershed connects them. The correct analysis is to trace flow paths, identify the common receiving water, and consider prevention at each source.''',
 'Review the atlas water layer. Trace one river from north to south and say aloud: source area → tributary → reservoir/river → downstream community. Then retry the flow questions.',
 'Watershed Protection Branch',45,1),
('water-systems-module','1.2 From Reservoir to Tap','reservoir-to-tap',9,14,
 'Study drinking-water supply as a chain of infrastructure rather than a single treatment plant.',
 'Sequence the major stages of a public water system; calculate demand and reserve capacity; explain why drought and growth can stress the same system.',
 '''Public drinking-water systems must deliver safe water reliably. A simplified system includes a source such as a river, reservoir, or groundwater well; an intake; treatment; storage; pumps; distribution mains; and customer connections. Georgia EPD oversees public water systems and water-withdrawal programs as part of its watershed responsibilities.\n\nCapacity matters. Suppose a treatment plant can safely produce 20 million gallons per day (MGD) and customers currently require 17 MGD. The plant has 3 MGD of unused treatment capacity, or a 15% capacity margin relative to its maximum. Growth, drought, equipment failures, or unusually high demand can shrink that margin.\n\nEngineers and public officials therefore do not ask only, “Can the plant meet demand today?” They also ask about peak demand, source availability, storage, redundancy, maintenance, future population, drought, and the cost of expansion. A system with almost no reserve capacity may be vulnerable even if it technically meets today's average demand.''',
 '''Worked example: A 24-MGD plant currently treats 18 MGD. Unused capacity is 6 MGD. If demand grows 10%, expected demand becomes 19.8 MGD, leaving 4.2 MGD. The arithmetic is simple; the deeper question is whether 4.2 MGD is enough after considering peak-day demand, maintenance outages, drought, and future growth.''',
 'Rework the example using a calculator. Write the three quantities on paper: maximum capacity, current demand, unused capacity. Do not continue until you can explain the difference between average demand and maximum capacity.',
 'Watershed Protection Branch',50,2),
('water-systems-module','1.3 Wastewater, Stormwater, and Downstream Risk','wastewater-stormwater-risk',10,14,
 'Compare wastewater and stormwater and reason about why treatment, permits, monitoring, and location matter.',
 'Distinguish wastewater from stormwater; explain the purpose of treatment and discharge permits; identify downstream risk in a scenario.',
 '''Wastewater and stormwater are related to water quality, but they are not the same system. Domestic and industrial wastewater is collected and treated before disposal or discharge under applicable permits. Georgia EPD administers wastewater permitting in the state under delegated Clean Water Act authority. Stormwater is rainfall or snowmelt runoff that can move across streets, roofs, construction sites, farms, and other surfaces before reaching waterways.\n\nA simplified wastewater treatment sequence can include screening, settling, biological treatment, clarification, disinfection, and discharge. Real plants vary, and permits can include limitations, monitoring, reporting, and special conditions. The important concept is that treatment reduces pollutants before water is returned to the environment.\n\nCritical thinking requires looking downstream. A treatment plant may be operating correctly while a watershed still faces other pollution sources. Likewise, reducing pollution at one location does not solve every problem in the basin. Students should ask what enters the water, where it enters, what treatment occurs, how flow changes during storms or drought, and who or what is downstream.''',
 '''Worked example: Town A discharges treated wastewater to a river. Five miles downstream, Town B has a drinking-water intake. A student should not conclude automatically that the discharge is unsafe or safe. The correct reasoning is to ask about permit limits, treatment performance, river flow, monitoring results, distance, other pollutant sources, and treatment at Town B.''',
 'Create a two-column comparison titled WASTEWATER and STORMWATER. Put at least three differences under each. Then use the map to identify an upstream and downstream location on the same river.',
 'Wastewater Program',50,3),
('water-systems-module','1.4 Water Systems Capstone: Growth Under Constraint','water-capstone',11,14,
 'Combine geography, percentages, capacity planning, and policy tradeoffs in a community water scenario.',
 'Calculate projected demand; compare demand with capacity; identify missing data; defend a recommendation using evidence and tradeoffs.',
 '''This capstone treats water as a coupled geographic and infrastructure system. Communities must balance reliability, cost, conservation, environmental effects, and future growth. The hardest questions usually have more than one defensible answer because the decision depends on evidence and assumptions.\n\nYou will analyze a fictional Georgia community using realistic planning concepts. The community has a treatment capacity of 18 MGD and current average demand of 15.8 MGD. Assume demand changes at the same rate as population unless the problem states otherwise. A strong response will calculate correctly, separate facts from assumptions, identify missing information, and explain tradeoffs rather than merely choosing “build more” or “use less.”''',
 '''Worked example: If demand rises from 10 MGD by 5%, new demand is 10 × 1.05 = 10.5 MGD. If capacity is 12 MGD, the nominal margin is 1.5 MGD. That does not prove the system is safe; peak demand, drought source limits, storage, redundancy, and equipment outages could change the conclusion.''',
 'Return to Lessons 1.1–1.3 if you cannot explain watershed, capacity margin, and the difference between wastewater and stormwater without notes.',
 'Watershed Protection Branch',70,4),
('transport-logistics-module','2.1 Georgia as a Transportation Network','ga-network-thinking',9,14,
 'Move beyond naming highways by studying connections, bottlenecks, redundancy, and network effects.',
 'Explain why a transportation network is more than individual roads; interpret connectivity; identify bottlenecks and alternate routes.',
 '''Georgia DOT maintains road inventory data for more than 125,000 centerline miles of public roads. A road network matters because each segment connects to other segments. Interstates, state routes, local roads, bridges, rail lines, airports, and ports form a system that moves people and goods.\n\nA bottleneck is a place where limited capacity or disruption can constrain the larger network. Redundancy means there are alternate ways to reach a destination. A warehouse beside an interstate may still be poorly located if local roads cannot handle trucks or if a key bridge creates a single point of failure.\n\nStudents should therefore ask: What connects to what? How many alternate routes exist? Which links carry the most important flows? What happens if one link fails? Those are network questions, not memorization questions.''',
 '''Worked example: Two warehouses are both 100 miles from customers. Warehouse A has direct interstate access and two alternate routes. Warehouse B depends on one two-lane bridge. Distance alone suggests a tie, but network resilience favors Warehouse A if the bridge is a major failure risk.''',
 'Open the Transportation layer. Pick one interstate and identify two cities it connects. Then imagine one segment closes and name an alternate path or transportation mode.',
 'Road & Traffic Data',45,1),
('transport-logistics-module','2.2 Port, Rail, and Interstate Connections','savannah-port-connections',10,14,
 'Understand why Savannah works as a logistics gateway by connecting port geography to highways and rail.',
 'Identify the role of I-16 and I-95; compare truck and rail strengths; explain why multimodal access matters to a port.',
 '''The Port of Savannah connects ocean shipping with inland transportation. Georgia Ports Authority describes immediate access to I-16 east-west and I-95 north-south, as well as Class I rail service. This is a good example of multimodal transportation: ships do not deliver most containers directly to inland stores or factories, so cargo transfers to trucks or trains.\n\nMode choice depends on more than speed. Trucking can be flexible for shorter or distributed deliveries. Rail can move large freight volumes efficiently over longer distances, especially when origin and destination have good intermodal connections. A strong logistics decision considers distance, time, cost, reliability, cargo type, terminal access, and capacity.\n\nI-16 is geographically important because it links the Savannah area westward toward Macon, where the broader interstate network provides additional connections. I-95 provides a major north-south corridor near the coast. The value of the port comes partly from these connections, not merely from the docks themselves.''',
 '''Worked example: A container arrives in Savannah and must reach an Atlanta-area distribution center. A planner could consider truck, rail, or a combination. The best answer cannot be chosen from distance alone; the planner needs rates, schedules, terminal locations, delivery deadlines, cargo requirements, congestion, and final-mile access.''',
 'Use the atlas to trace Savannah → I-16 → Macon, then identify how the route can continue toward Atlanta. Review the difference between a port, interstate corridor, and rail terminal.',
 'Port of Savannah',55,2),
('transport-logistics-module','2.3 Logistics Word Problems: Cost, Time, and Capacity','logistics-word-problems',11,14,
 'Use arithmetic as evidence in transportation decisions instead of treating math as a separate subject.',
 'Calculate trip cost and capacity; compare alternatives; recognize when the cheapest option is not automatically the best option.',
 '''Logistics decisions usually balance several quantities. Total transportation cost can include a fixed terminal or handling charge plus a variable cost based on distance, time, weight, containers, or vehicle use. Capacity tells how much can move in one trip. Travel time matters when deliveries have deadlines.\n\nFor this lesson, use simplified fictional rates to practice reasoning. The numbers are not current commercial freight rates. The goal is to learn a decision method: define the alternatives, calculate comparable quantities, identify constraints, then explain which option fits the objective.\n\nA good answer states assumptions. If one route costs less but is too slow for the deadline, it is not feasible. If a rail option has lower line-haul cost but requires expensive final-mile trucking, the student should include that extra leg. Quantitative reasoning improves the decision, but it does not replace judgment.''',
 '''Worked example: Route A costs $2.20 per mile for 280 miles: $616. Route B has a $300 handling charge plus $0.90 per mile for 300 miles: $570. Route B is $46 cheaper under the simplified assumptions. But if Route B misses the delivery deadline or requires an additional final-mile charge, the recommendation could change.''',
 'Write COST, TIME, CAPACITY, RELIABILITY, and FINAL MILE on paper. For every logistics problem, check all five before making a recommendation.',
 'Road & Traffic Data',60,3),
('transport-logistics-module','2.4 Logistics Capstone: Choose a Georgia Distribution Strategy','logistics-capstone',12,14,
 'Make and defend a distribution-location recommendation using geography, network access, quantitative evidence, and uncertainty.',
 'Compare locations; calculate weighted costs; identify evidence gaps; defend a recommendation and explain what could reverse it.',
 '''A distribution center is valuable because of the network it can reach. Georgia locations differ in access to population centers, interstates, rail, ports, airports, land, labor, and customers. A location decision should therefore be evidence-based.\n\nIn this capstone, you will compare fictional sites near Savannah, Macon, and Atlanta. No site is automatically “best.” Savannah may favor port proximity, Atlanta may favor access to a very large metropolitan market and major transportation connections, and Macon can offer a central position on important routes. The correct choice depends on the company's freight pattern.\n\nThe assessment rewards reasoning. You must distinguish facts supplied by the problem from facts you would still need to research. Strong answers explain what could change the recommendation: fuel cost, rail rates, customer distribution, congestion, land cost, labor availability, inventory strategy, or a new transportation constraint.''',
 '''Worked example: If 70% of a firm's freight is imported through Savannah but 80% of customers are north of Atlanta, minimizing only port-to-warehouse distance may increase warehouse-to-customer cost. A better analysis considers the full supply chain and weights flows by volume.''',
 'Return to Lessons 2.1–2.3 if you cannot explain bottleneck, multimodal, final mile, and why lowest line-haul cost may not equal lowest total cost.',
 'Port of Savannah',75,4),
]

ITEMS = {
'watersheds-control-flow': [
('mcq','A chemical spill occurs in a tributary upstream of a reservoir. Which question should a watershed analyst ask first?','Which county has the largest population?','Where does the tributary flow and what lies downstream?','Which highway is closest?','What is the state bird?','B',None,0,'Watershed analysis begins by tracing drainage and downstream receptors.',None,2,1),
('mcq','Why can county boundaries be misleading when studying water pollution?','Water always flows along county lines.','Watersheds follow topography rather than political boundaries.','Counties do not contain streams.','Pollution only travels by road.','B',None,0,'Drainage divides are geographic, not political.',None,2,2),
('constructed','A parking lot, farm field, and construction site all drain to the same creek. Explain two different ways pollution could reach the creek and one prevention strategy for each source.',None,None,None,None,None,None,0,'A strong answer connects runoff pathways to source-specific prevention.','4: identifies multiple pathways, specific prevention strategies, and explains watershed connection; 3: mostly correct with adequate reasoning; 2: partial; 1: minimal; 0: missing/off-topic.',4,3),
],
'reservoir-to-tap': [
('numeric','A plant has a maximum treatment capacity of 24 MGD and current demand of 18 MGD. How many MGD of unused treatment capacity remain?',None,None,None,None,None,6,0.01,'Unused capacity = 24 − 18 = 6 MGD.',None,3,1),
('numeric','If current demand is 18 MGD and rises by 10%, what is the new demand in MGD?',None,None,None,None,None,19.8,0.01,'18 × 1.10 = 19.8 MGD.',None,3,2),
('mcq','Which statement best explains why a 2-MGD reserve margin may still be risky?','Average demand is the only number that matters.','Peak demand, drought, maintenance outages, and source limits can reduce reliability.','Unused capacity can never change.','Reservoirs eliminate all risk.','B',None,0,'Infrastructure planning considers reliability and uncertainty, not only averages.',None,2,3),
('constructed','A community proposes a large subdivision while its water plant is already using 92% of treatment capacity on average. Give a recommendation and identify at least three pieces of additional evidence you would demand before approving or rejecting the project.',None,None,None,None,None,None,0,'Good answers separate a preliminary recommendation from missing evidence.','4: defensible recommendation + 3 or more relevant evidence needs + tradeoffs; 3: good reasoning with minor gaps; 2: partial; 1: minimal; 0: missing/off-topic.',4,4),
],
'wastewater-stormwater-risk': [
('mcq','Which situation is stormwater rather than wastewater?','Used water leaving a household sewer','Rain runoff carrying sediment from a construction site','Industrial wastewater entering a treatment system','Sewage entering a wastewater plant','B',None,0,'Stormwater is precipitation runoff across land and built surfaces.',None,2,1),
('mcq','A permitted wastewater discharge is upstream from a drinking-water intake. What is the best conclusion?','It is automatically unsafe.','It is automatically harmless.','Evaluate permit limits, treatment performance, flow, monitoring, other sources, and downstream treatment.','Move the intake without gathering data.','C',None,0,'Risk evaluation requires evidence and context.',None,3,2),
('constructed','Explain why improving a wastewater plant alone may not solve every water-quality problem in the watershed. Use at least two other possible pollutant sources or processes.',None,None,None,None,None,None,0,'Watersheds can contain multiple point and nonpoint sources.','4: clearly explains multiple sources/processes and systems interaction; 3: adequate; 2: partial; 1: minimal; 0: missing.',4,3),
],
'water-capstone': [
('numeric','A town uses 15.8 MGD. If demand grows by 3.1%, estimate next year’s demand in MGD. Round to two decimals.',None,None,None,None,None,16.2898,0.02,'15.8 × 1.031 = 16.2898 ≈ 16.29 MGD.',None,3,1),
('numeric','With an 18-MGD treatment capacity and projected demand of 16.29 MGD, how much nominal treatment capacity remains?',None,None,None,None,None,1.71,0.02,'18 − 16.29 = 1.71 MGD.',None,3,2),
('mcq','Which additional fact is most important before claiming the system is sustainable for five years?','The school mascot','Peak demand, drought/source limits, projected growth, and system redundancy','The color of the treatment plant','The number of counties in Georgia','B',None,0,'Long-term reliability requires more than one-year average-demand arithmetic.',None,2,3),
('constructed','Write a 120–250 word recommendation to the town council. Decide whether to approve unrestricted growth, approve growth with conditions, or delay major approvals. Use your calculations, identify at least three missing facts, and propose at least two actions.',None,None,None,None,None,None,0,'The response should combine quantitative evidence, uncertainty, and policy tradeoffs.','4: calculation-based recommendation, 3+ missing facts, 2+ actions, clear tradeoffs; 3: strong but incomplete; 2: partial; 1: weak; 0: missing.',6,4),
],
'ga-network-thinking': [
('mcq','Two warehouses are equally distant from customers. One has two interstate routes; the other depends on one bridge. What concept most favors the first site?','Redundancy','Latitude','Watershed divide','Elevation','A',None,0,'Multiple viable routes can improve network resilience.',None,2,1),
('constructed','Choose a Georgia interstate visible in the atlas. Describe one plausible bottleneck and one form of redundancy that could reduce disruption if part of the corridor closes.',None,None,None,None,None,None,0,'Students should reason about connections and alternatives, not merely name a road.','4: specific corridor, plausible bottleneck, credible alternate route/mode; 3: mostly complete; 2: partial; 1: minimal; 0: missing.',4,2),
],
'savannah-port-connections': [
('mcq','Why is I-16 especially important to the Port of Savannah?','It is an east-west connection from the Savannah area toward inland Georgia.','It is a river.','It connects only airports.','It replaces rail service.','A',None,0,'I-16 is a major east-west interstate connection from Savannah.',None,2,1),
('mcq','Why is multimodal access valuable?','Every shipment must use every mode.','It gives shippers choices among ship, truck, and rail connections based on the job.','Rail and trucks are identical.','Ports work only without highways.','B',None,0,'Different modes have different strengths, costs, schedules, and constraints.',None,2,2),
('constructed','A container must move from Savannah to an Atlanta-area customer. Compare truck and rail as options. Name at least four pieces of information needed before choosing.',None,None,None,None,None,None,0,'A good comparison includes cost, time, terminal/final-mile access, reliability, cargo, and capacity.','4: balanced comparison + 4+ relevant data needs; 3: good but incomplete; 2: partial; 1: minimal; 0: missing.',4,3),
],
'logistics-word-problems': [
('numeric','Route A is 280 miles at $2.20 per mile. What is the simplified transportation cost in dollars?',None,None,None,None,None,616,0.01,'280 × 2.20 = $616.',None,3,1),
('numeric','Route B has a $300 handling charge plus 300 miles at $0.90 per mile. What is the simplified total cost?',None,None,None,None,None,570,0.01,'$300 + (300 × $0.90) = $570.',None,3,2),
('mcq','Route B is $46 cheaper, but it misses the delivery deadline. Which is the better decision?','Route B because cost is the only constraint.','Choose a feasible option that meets the deadline, then compare total costs among feasible options.','Cancel all deliveries.','Distance no longer matters in logistics.','B',None,0,'Optimization occurs within constraints; an infeasible cheap option is not best.',None,2,3),
('constructed','Create one realistic factor that could make the more expensive route preferable. Explain exactly how that factor changes the decision.',None,None,None,None,None,None,0,'Students should understand that reliability, deadlines, damage risk, capacity, or final mile can outweigh line-haul cost.','4: specific factor + causal explanation + decision effect; 3: good; 2: partial; 1: minimal; 0: missing.',4,4),
],
'logistics-capstone': [
('numeric','A company imports 600 containers per month. If 70% arrive through Savannah, how many containers is that?',None,None,None,None,None,420,0.01,'600 × 0.70 = 420 containers.',None,3,1),
('mcq','If most inbound freight enters Savannah but most customers are north of Atlanta, what is the best location method?','Minimize port distance only.','Consider the weighted full supply chain from inbound port to warehouse to customers.','Choose the largest city automatically.','Ignore final-mile delivery.','B',None,0,'Distribution-location decisions should consider the full flow pattern.',None,3,2),
('constructed','Choose Savannah-area, Macon-area, or Atlanta-area for a fictional distribution center. Defend your choice in 150–300 words using at least three geographic/logistics factors, one calculation or quantity from the scenario, two facts you would still research, and one condition that could reverse your recommendation.',None,None,None,None,None,None,0,'No single location is automatically correct; evidence and assumptions determine the recommendation.','4: evidence-rich, quantitative, identifies research gaps and reversal condition; 3: strong; 2: partial; 1: weak; 0: missing.',6,3),
],
}


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    admin_pw = os.getenv('ADMIN_PASSWORD', 'change-me-local')
    student_user = os.getenv('STUDENT_USERNAME', 'student')
    student_pw = os.getenv('STUDENT_PASSWORD', 'student')
    db.execute('INSERT OR IGNORE INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
               (admin_user, generate_password_hash(admin_pw), 'Local Administrator', 'admin', None))
    db.execute('INSERT OR IGNORE INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
               (student_user, generate_password_hash(student_pw), 'Demo Student', 'student', 12))
    db.execute('INSERT OR IGNORE INTO users(username,password_hash,display_name,role,age) VALUES (?,?,?,?,?)',
               ('student14', generate_password_hash('student14'), 'Age 14 Test Student', 'student', 14))
    for row in SOURCES:
        db.execute('INSERT OR IGNORE INTO sources(name,agency,url,category,verified_on,refresh_days) VALUES (?,?,?,?,?,?)', row)
    for row in COURSES:
        db.execute('INSERT OR IGNORE INTO courses(title,slug,description,sort_order) VALUES (?,?,?,?)', row)
    db.commit()
    course_ids = {r['slug']: r['id'] for r in db.execute('SELECT id,slug FROM courses')}
    for course_slug,title,slug,description,essential_question,sort_order in MODULES:
        db.execute('INSERT OR IGNORE INTO modules(course_id,title,slug,description,essential_question,sort_order) VALUES (?,?,?,?,?,?)',
                   (course_ids[course_slug],title,slug,description,essential_question,sort_order))
    db.commit()
    source_ids = {r['name']: r['id'] for r in db.execute('SELECT id,name FROM sources')}
    module_ids = {r['slug']: r['id'] for r in db.execute('SELECT id,slug FROM modules')}
    for mod_slug,title,slug,min_age,max_age,summary,obj,content,worked,remediation,source_name,xp,sort_order in LESSONS:
        db.execute('''INSERT OR IGNORE INTO lessons(module_id,title,slug,min_age,max_age,summary,learning_objectives,content,worked_example,remediation,source_id,xp,sort_order)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (module_ids[mod_slug],title,slug,min_age,max_age,summary,obj,content,worked,remediation,source_ids[source_name],xp,sort_order))
    db.commit()
    lesson_ids = {r['slug']: r['id'] for r in db.execute('SELECT id,slug FROM lessons')}
    for slug, items in ITEMS.items():
        lid = lesson_ids[slug]
        existing = db.execute('SELECT COUNT(*) n FROM assessment_items WHERE lesson_id=?',(lid,)).fetchone()['n']
        if not existing:
            for item in items:
                typ,prompt,a,b,c,d,correct,numeric,tolerance,explanation,rubric,points,sort_order = item
                db.execute('''INSERT INTO assessment_items(lesson_id,item_type,prompt,choice_a,choice_b,choice_c,choice_d,correct_text,numeric_answer,numeric_tolerance,explanation,rubric,points,sort_order)
                              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (lid,typ,prompt,a,b,c,d,correct,numeric,tolerance,explanation,rubric,points,sort_order))
    db.commit()
    current_app.teardown_appcontext(close_db)


def gradebook_rows(user_id=None, limit=None):
    db = get_db()
    params=[]
    where_l = " WHERE u.role='student'"
    where_g = " WHERE u.role='student'"
    if user_id:
        where_l += ' AND u.id=?'; where_g += ' AND u.id=?'; params=[user_id,user_id]
    sql = f"""
      SELECT 'coursework' record_type, g.id source_id, u.id user_id, u.display_name student, u.age,
             c.title course, m.title module, l.title activity, g.auto_score score, g.final_score final_score,
             g.status status, 0 duration_seconds, g.completed_at completed_at
      FROM grade_events g JOIN users u ON u.id=g.user_id
      JOIN lessons l ON l.id=g.lesson_id JOIN modules m ON m.id=l.module_id JOIN courses c ON c.id=m.course_id
      {where_l}
      UNION ALL
      SELECT 'game' record_type, ga.id source_id, u.id user_id, u.display_name student, u.age,
             'Games' course, 'Map Skills' module,
             CASE ga.game_key WHEN 'map-hunt' THEN 'Map Hunt' ELSE ga.game_key END activity,
             ga.score score, ga.score final_score,
             CASE WHEN ga.score>=85 THEN 'mastered' ELSE 'practice' END status, ga.duration_seconds, ga.completed_at
      FROM game_attempts ga JOIN users u ON u.id=ga.user_id
      {where_g}
      ORDER BY completed_at DESC
    """
    rows=db.execute(sql,params).fetchall()
    return rows[:limit] if limit else rows


def csv_for_grades(user_id=None):
    rows=gradebook_rows(user_id)
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(['student','age','record_type','course','module','activity','score_percent','final_score_percent','status','duration_seconds','completed_at'])
    for r in rows:
        w.writerow([r['student'],r['age'],r['record_type'],r['course'],r['module'],r['activity'],f"{r['score']:.1f}",
                    '' if r['final_score'] is None else f"{r['final_score']:.1f}",r['status'],r['duration_seconds'],r['completed_at']])
    return out.getvalue()


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
