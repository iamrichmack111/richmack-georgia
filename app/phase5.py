from datetime import date
from .db import get_db, utcnow

PHASE5_SCHEMA = '''
CREATE TABLE IF NOT EXISTS academic_years (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  starts_on TEXT NOT NULL,
  ends_on TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS skills (
  id INTEGER PRIMARY KEY,
  skill_key TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lesson_skills (
  lesson_id INTEGER NOT NULL REFERENCES lessons(id),
  skill_id INTEGER NOT NULL REFERENCES skills(id),
  weight REAL NOT NULL DEFAULT 1,
  PRIMARY KEY(lesson_id, skill_id)
);
CREATE TABLE IF NOT EXISTS game_skill_attempts (
  id INTEGER PRIMARY KEY,
  game_attempt_id INTEGER NOT NULL REFERENCES game_attempts(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  skill_key TEXT NOT NULL,
  correct_count INTEGER NOT NULL,
  question_count INTEGER NOT NULL,
  score REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
  id INTEGER PRIMARY KEY,
  created_by INTEGER NOT NULL REFERENCES users(id),
  student_id INTEGER NOT NULL REFERENCES users(id),
  lesson_id INTEGER REFERENCES lessons(id),
  module_id INTEGER REFERENCES modules(id),
  title TEXT NOT NULL,
  due_date TEXT,
  min_score REAL NOT NULL DEFAULT 85,
  academic_year_id INTEGER REFERENCES academic_years(id),
  created_at TEXT NOT NULL,
  archived INTEGER NOT NULL DEFAULT 0,
  CHECK ((lesson_id IS NOT NULL AND module_id IS NULL) OR (lesson_id IS NULL AND module_id IS NOT NULL))
);
'''

SKILLS = [
('map-reasoning','Map & Spatial Reasoning','Geography','Use location, direction, scale, patterns, and connections to interpret Georgia maps.'),
('physical-regions','Physiographic Regions','Physical Geography','Distinguish Georgia regions using landform, relief, geology, and location evidence.'),
('mountains-relief','Mountains & Relief','Physical Geography','Reason about elevation, relief, headwaters, erosion, and mountainous terrain.'),
('fall-line','Fall Line & Transition Zones','Physical Geography','Explain why transition zones influence settlement, transportation, and industry.'),
('rivers','Rivers & Drainage','Water','Trace rivers and explain upstream/downstream relationships.'),
('watersheds','Watershed Reasoning','Water','Analyze drainage basins, shared impacts, and watershed boundaries.'),
('lakes-reservoirs','Lakes & Reservoirs','Water','Explain reservoir purposes, tradeoffs, capacity, and downstream effects.'),
('water-quality','Water Quality','Water','Interpret pollution sources, monitoring, designated uses, and management responses.'),
('transportation','Transportation Networks','Infrastructure','Analyze road, rail, port, and airport connectivity and bottlenecks.'),
('economics','Economic Reasoning','Economics','Use incentives, tradeoffs, costs, specialization, and evidence in economic decisions.'),
('industry','Georgia Industries','Economics','Connect Georgia industries to geography, labor, infrastructure, and markets.'),
('quantitative','Quantitative Reasoning','Cross-Curricular','Use percentages, rates, projections, weighted values, and units as evidence.'),
('historical-causation','Historical Causation','History','Explain causes, effects, continuity, change, and multiple contributing factors.'),
('source-analysis','Source Analysis','History','Distinguish evidence, claims, context, perspective, and missing information.'),
('civics-history','Civic & Historical Geography','History','Connect places, government decisions, communities, and historical change.'),
('critical-thinking','Critical Thinking','Cross-Curricular','Defend conclusions, identify assumptions, compare alternatives, and name missing evidence.'),
]

SOURCES = [
('Georgia Geologic Survey Publications','Georgia Environmental Protection Division','https://epd.georgia.gov/georgia-geologic-survey/publications','physical-geography','2026-08-24',365),
('River Basins of Georgia','Georgia Environmental Protection Division','https://epd.georgia.gov/document/publication/fcg2014073114eabpdf/download','water','2026-08-24',365),
('Georgia Archives','Georgia Archives','https://www.georgiaarchives.org/','history','2026-08-24',365),
('Georgia Industries','Georgia Department of Economic Development','https://georgia.org/industries','economics','2026-08-24',90),
('Georgia Manufacturing','Georgia Department of Economic Development','https://georgia.org/industries/manufacturing','economics','2026-08-24',90),
('Georgia Agribusiness','Georgia Department of Economic Development','https://georgia.org/industries/agribusiness','economics','2026-08-24',90),
]

COURSES = [
('Physical Geography & Mountains','physical-geography','Landforms, physiographic regions, elevation, geology, and how physical geography shapes human systems.',3),
('Rivers, Lakes & Watersheds','rivers-lakes','Georgia river basins, reservoirs, water quality, competing uses, and watershed-scale decisions.',4),
('Georgia History: Place, Change & Evidence','georgia-history','Georgia history through geography, evidence, cause and effect, and competing interpretations.',5),
('Georgia Economics & Business','georgia-economics','Industry, agriculture, manufacturing, logistics, location decisions, tradeoffs, and economic evidence.',6),
]

MODULES = [
('physical-geography','Module 3 — Physical Geography & Mountains','physical-geography-module','Read Georgia as a physical system: regions, relief, mountains, geology, and transition zones.','How does Georgia’s physical landscape create opportunities, limits, and patterns of settlement?',1),
('rivers-lakes','Module 4 — Rivers, Lakes & Watersheds','rivers-lakes-module','Analyze Georgia’s 14 river basins, reservoirs, water quality, and competing demands.','How should Georgians make water decisions when one watershed serves many communities and purposes?',1),
('georgia-history','Module 5 — Georgia History: Place, Change & Evidence','georgia-history-module','Use geography and evidence to explain historical change rather than memorize isolated dates.','How does place shape historical choices, and how do we know whether an explanation is strong?',1),
('georgia-economics','Module 6 — Georgia Economics & Business','georgia-economics-module','Connect industries to resources, workers, infrastructure, markets, and measurable tradeoffs.','Why do industries cluster where they do, and how should communities judge economic-development choices?',1),
]

LESSONS = [
('physical-geography-module','3.1 Five Regions, Five Different Constraints','five-regions-constraints',9,14,
 'Compare Georgia’s physiographic regions using evidence instead of memorizing a color-coded map.',
 'Distinguish the five regions; connect relief and geology to land use; defend a region identification from multiple clues.',
 '''Georgia is commonly taught through five physiographic regions: Appalachian Plateau, Ridge and Valley, Blue Ridge, Piedmont, and Coastal Plain. A region is useful because it groups places with related physical characteristics, but a boundary on a classroom map is only the start of analysis. Students should ask how elevation, slope, rock, soil, drainage, and access affect what people can build or produce.\n\nA steep mountain landscape changes road construction, farming, erosion risk, and stream behavior. Rolling Piedmont terrain creates different opportunities and constraints. The broad Coastal Plain has lower relief and a different geologic history. The important skill is not reciting names—it is using physical evidence to predict consequences.\n\nWhen two regions meet, conditions can change gradually rather than at a perfect line. Real geographic reasoning accepts transition zones and asks which evidence is strongest.''',
 '''Worked example: A site has steep slopes, narrow valleys, high relief, and many headwater streams. Those clues support a mountain-region hypothesis. A strong answer also explains consequences: road grades may be harder, runoff can move quickly, and flat buildable land can be limited.''',
 'Open the Regions layer and compare two adjacent regions. Write three physical clues and two likely human consequences before retrying.',
 'Georgia Geologic Survey Publications',55,1),
('physical-geography-module','3.2 Mountains, Relief, and Headwaters','mountains-headwaters',10,14,
 'Connect elevation and relief to drainage, erosion, transportation, and settlement.',
 'Distinguish elevation from relief; explain why mountains often contain headwaters; calculate grade; evaluate a route tradeoff.',
 '''Elevation measures height relative to a reference such as sea level; relief describes the difference between high and low places within an area. Two locations can have similar average elevation but very different relief. High-relief terrain influences water flow, road design, erosion, recreation, and development.\n\nMany streams begin in upland or mountainous areas because precipitation drains downslope and small channels combine into larger ones. This does not mean every high place is a major river source, but topography strongly organizes drainage.\n\nTransportation planners also care about grade. A road climbing 600 feet over 2 horizontal miles has a different engineering challenge from one climbing 600 feet over 10 miles. Students should combine arithmetic with geography rather than treating them separately.''',
 '''Worked example: A road rises 400 feet over 2 miles. Two miles is 10,560 feet. Grade ≈ 400/10,560 × 100 = 3.8%. A second route may be longer but flatter; choosing between them requires cost, safety, travel time, and environmental evidence.''',
 'Review elevation versus relief, then compute one grade problem slowly with matching units. Explain why a longer route can sometimes be easier to build.',
 'Georgia Geologic Survey Publications',60,2),
('physical-geography-module','3.3 The Fall Line: A Transition That Shapes Systems','fall-line-systems',11,14,
 'Use the Fall Line as a case study in how physical geography can influence cities, industry, and transportation.',
 'Describe a transition zone; connect river gradient to historical uses; analyze why cities can emerge near geographic breaks.',
 '''The Fall Line marks a broad transition between harder Piedmont rocks and younger Coastal Plain sediments. Rivers crossing this zone can change gradient and historically produced rapids or falls. Geographic transitions can influence navigation, water power, settlement, and transportation routes.\n\nA weak explanation says, “Cities are there because of the Fall Line.” A stronger explanation identifies mechanisms: river travel may become harder, goods may need transfer, water power may be available, routes may converge, and later transportation networks can reinforce an existing settlement.\n\nHistorical geography is rarely one-cause geography. Physical setting can create an opportunity, but technology, politics, labor, markets, and transportation investment determine what happens next.''',
 '''Worked example: If river cargo can travel easily below a point but not above it, a transfer location can become economically valuable. If roads and later rail lines also converge there, the original geographic advantage can compound over time.''',
 'On paper, complete: physical change → immediate transportation effect → economic opportunity → possible city growth. Then give one factor besides geography that could strengthen or weaken the pattern.',
 'Georgia Geologic Survey Publications',65,3),

('rivers-lakes-module','4.1 Georgia’s 14 River Basins as Connected Systems','fourteen-basins',9,14,
 'Move from memorizing river names to reasoning about basin boundaries and shared downstream consequences.',
 'Recognize Georgia’s 14 major river basins; distinguish basin from river; infer downstream connections and cross-county effects.',
 '''Georgia EPD materials identify 14 major river basins in the state. A river basin includes the land drained by a river and its tributaries. The basin concept is larger than the main river channel and can cross many county or city boundaries.\n\nA useful systems question is: who shares the water? Upstream communities can affect downstream conditions, and downstream needs can influence how an entire basin is managed. Water supply, recreation, habitat, wastewater discharge, industry, agriculture, and flood risk can all occur in the same basin.\n\nPolitical boundaries remain important for government, but water follows topography. Effective analysis overlays both systems rather than assuming one boundary answers every question.''',
 '''Worked example: Two counties are in the same basin but on different tributaries. A pollutant from one tributary will not necessarily reach every point in the basin. You must trace the tributary network and confluences before claiming a downstream effect.''',
 'Use the water map to trace one main river and imagine two tributaries joining it. Explain why “same basin” does not mean “same exact flow path.”',
 'River Basins of Georgia',55,1),
('rivers-lakes-module','4.2 Reservoirs: Storage, Supply, Floods, Power, and Tradeoffs','reservoir-tradeoffs',10,14,
 'Analyze reservoirs as multi-purpose infrastructure with competing objectives.',
 'Explain reservoir storage; calculate percentage drawdown; compare water-supply, flood-control, hydropower, recreation, and ecological tradeoffs.',
 '''A reservoir stores water behind a dam, but the useful question is not simply “How much water is there?” Operators and communities care about usable storage, inflow, releases, drought, flood-control space, water-supply demand, hydropower, recreation, and downstream flow needs.\n\nThese goals can conflict. Holding more water may help supply or recreation, while leaving storage space can matter before major storms. Releasing water can support downstream needs but reduce stored volume. A serious decision therefore requires objectives, forecasts, legal constraints, and current measurements.\n\nStudents should resist single-variable answers. A reservoir problem is a tradeoff problem.''',
 '''Worked example: A fictional reservoir has 500,000 acre-feet of usable storage and falls to 410,000. The drawdown is 90,000 acre-feet, or 18% of usable storage. Whether that is alarming depends on season, inflow forecasts, demand, required releases, and operating rules.''',
 'Calculate drawdown as amount lost ÷ starting usable storage × 100. Then list three facts you would need before recommending restrictions.',
 'Water Supply Watersheds',65,2),
('rivers-lakes-module','4.3 Water Quality Investigation: Evidence Before Conclusions','water-quality-evidence',11,14,
 'Interpret a simplified water-quality case without jumping from one measurement to a causal claim.',
 'Distinguish observation from cause; compare upstream/downstream measurements; identify confounders; propose a monitoring plan.',
 '''Georgia water-quality assessment uses data, designated uses, criteria, and basin context. In this lesson, the focus is scientific reasoning: a measurement can show a condition, but one measurement rarely proves the cause.\n\nSuppose turbidity rises downstream of a construction area after rainfall. Construction runoff is a plausible hypothesis, but other tributaries, bank erosion, road runoff, timing, sampling error, and upstream conditions also matter. Good investigation compares locations and times and looks for patterns.\n\nStudents should write conclusions at the strength supported by the evidence: “consistent with,” “suggests,” or “does not yet distinguish between” can be more accurate than “proved.”''',
 '''Worked example: Upstream turbidity is 8 units before rain and 30 after rain; downstream is 10 before and 95 after. The downstream increase is larger, but the data do not identify a source by themselves. Add sampling near likely inputs, repeat across storms, and compare land-use conditions.''',
 'Separate your notes into OBSERVATION, HYPOTHESIS, and NEXT TEST. Never put a cause in the observation column.',
 'River Basins of Georgia',70,3),

('georgia-history-module','5.1 Geography Is a Cause, Not the Only Cause','history-geography-causation',9,14,
 'Learn to use geography in historical explanations without turning it into geographic determinism.',
 'Build multi-cause explanations; distinguish enabling conditions from direct causes; rank evidence by relevance.',
 '''Historical events usually have multiple causes. Geography can shape opportunities and constraints—ports affect trade, rivers affect movement, fertile land affects agriculture, and transportation corridors affect settlement—but geography does not make human choices inevitable.\n\nA strong explanation distinguishes background conditions, triggers, institutions, technologies, and decisions. For example, a transportation crossroads may make a city more likely to grow, but investment, migration, policy, conflict, and markets influence how much it grows and when.\n\nStudents should avoid sentences such as “Georgia had X geography, therefore Y had to happen.” Replace them with explanations of mechanisms and competing factors.''',
 '''Worked example: “A port caused the city to grow” is incomplete. Better: port access lowered some transportation costs, attracted trade-related activity, and interacted with roads, labor, capital, government policy, and regional demand.''',
 'Take one geographic factor and write three non-geographic factors that could alter its historical effect.',
 'Georgia Archives',55,1),
('georgia-history-module','5.2 Source Detective: Claim, Evidence, Context','source-detective',10,14,
 'Evaluate historical claims using source type, context, corroboration, and missing evidence.',
 'Separate primary and secondary evidence; identify perspective; corroborate claims; explain what a source cannot prove.',
 '''Historical sources are evidence created in contexts. A newspaper, law, map, photograph, letter, census table, oral history, and later scholarly account answer different questions. A source can be valuable without being neutral or complete.\n\nSource analysis asks who created it, when, for what purpose, for what audience, and what information the creator could know. Corroboration compares independent evidence. Context explains what was happening around the source.\n\nThe goal is not to dismiss biased sources. Bias itself can be historically informative. The goal is to avoid treating one source as a complete window into the past.''',
 '''Worked example: A promotional railroad brochure says a town is “the best location in Georgia.” It is evidence that promoters wanted investment, but not sufficient proof that the town objectively had the best economy. Compare freight data, maps, population records, competing advertisements, and later outcomes.''',
 'For any historical source, answer WHO, WHEN, PURPOSE, AUDIENCE, CLAIM, and WHAT IT CANNOT PROVE.',
 'Georgia Archives',65,2),
('georgia-history-module','5.3 Historical Systems Capstone: Why Did This Place Grow?','history-place-capstone',11,14,
 'Construct a multi-factor explanation for the growth of a Georgia place using geography, transportation, economics, and evidence.',
 'Develop a defensible thesis; organize causal evidence; identify alternative explanations; state uncertainty.',
 '''This capstone asks a question historians and geographers often share: why did one place grow faster or become more influential than another? A defensible answer combines physical setting with transportation, institutions, economic specialization, demographic change, technology, and historical events.\n\nYou will be given a fictionalized evidence packet representing two Georgia places. Your job is to decide which factors mattered most and explain why. There is no credit for listing every factor without ranking or connecting them.\n\nStrong reasoning uses causal chains: factor → mechanism → observable consequence. It also names evidence that would challenge the conclusion.''',
 '''Worked example: Rail junction → lower transfer cost and more route options → firms locate nearby → employment and population rise. But if a competing city had similar rail access and did not grow, that comparison tells us rail alone may be insufficient.''',
 'Write one causal chain with arrows, then one alternative explanation. Your final answer must explain why your preferred explanation is stronger.',
 'Georgia Archives',75,3),

('georgia-economics-module','6.1 Why Industries Cluster in Different Parts of Georgia','industry-location',9,14,
 'Connect industry location to inputs, workers, infrastructure, customers, land, and specialized networks.',
 'Identify location factors; distinguish correlation from cause; compare industry requirements; defend a site choice.',
 '''Georgia’s economy includes agribusiness, manufacturing, logistics, technology, film, aerospace, tourism, and other sectors. These industries do not need identical locations. A distribution center values transportation access differently from a farm, data center, film production, or food-processing plant.\n\nLocation decisions can involve labor, land price, water, power, suppliers, customers, universities, airports, ports, highways, rail, tax structure, and existing clusters. A cluster can become self-reinforcing when specialized workers and suppliers gather near related firms.\n\nEconomic geography therefore asks both “what is nearby?” and “why does nearby matter to this industry?”''',
 '''Worked example: A food processor may value proximity to farm inputs, cold storage, water, labor, highways, and customers. A technology firm may weigh skilled labor, research institutions, connectivity, and office costs more heavily. The same site can be strong for one and weak for another.''',
 'Choose two different industries and list five location factors for each. Circle factors that overlap and underline factors that differ.',
 'Georgia Industries',55,1),
('georgia-economics-module','6.2 Economic Impact: Jobs Are Important, But Not the Whole Calculation','economic-impact-tradeoffs',10,14,
 'Evaluate development proposals using benefits, costs, opportunity cost, and uncertainty.',
 'Calculate simple cost per job; identify direct versus indirect claims; explain opportunity cost; request missing evidence.',
 '''Economic-development announcements often emphasize jobs and investment. Those are relevant, but responsible analysis also asks about public costs, infrastructure needs, wages, timing, environmental effects, displacement, tax revenue, and what else the community could do with the same resources.\n\nOpportunity cost means the value of the best alternative forgone. If a county spends $12 million on infrastructure for one project, that money cannot simultaneously fund another project. That does not make the investment bad; it means the comparison should be explicit.\n\nA simple “public cost per announced job” can be calculated, but students must not mistake it for a complete cost-benefit analysis. Announced jobs may differ from filled jobs, and public assets can have uses beyond one company.''',
 '''Worked example: A fictional incentive package costs $9 million and the project announces 600 jobs. Simple public cost per announced job = $15,000. A strong analysis then asks about wages, tax revenue, infrastructure lifespan, probability of job creation, alternative uses, and clawback provisions.''',
 'Compute cost per announced job, then write at least four reasons that number alone is not enough to approve or reject a project.',
 'Georgia Manufacturing',70,2),
('georgia-economics-module','6.3 Georgia Business Capstone: Choose an Expansion Strategy','business-expansion-capstone',12,14,
 'Compare three Georgia expansion strategies using weighted criteria and defend a recommendation under uncertainty.',
 'Build a weighted score; test sensitivity to changed assumptions; integrate qualitative evidence; defend a recommendation.',
 '''Real decisions combine quantitative and qualitative evidence. In this capstone, a fictional company compares three Georgia locations using transportation, labor, land, water/power, customer access, and supplier access. You will assign or use weights, calculate scores, and then test whether changing one important assumption changes the winner.\n\nThis is sensitivity analysis: a recommendation is more robust when reasonable changes in assumptions do not reverse it. If a tiny change flips the result, the decision is fragile and more research is valuable.\n\nThe strongest response explains the math, the assumptions, and the missing evidence. It does not hide judgment behind a spreadsheet.''',
 '''Worked example: If transportation has weight 40% and labor 30%, a logistics-heavy site can win. If the company automates and labor becomes only 10% while power reliability becomes 30%, rankings may change. The decision depends on business strategy, not a universal “best city.”''',
 'Before answering, list your weights and make sure they total 100%. Then change the largest weight by 10 percentage points and see whether the recommendation changes.',
 'Georgia Industries',80,3),
]

ITEMS = {
'five-regions-constraints': [
 ('mcq','A site has steep slopes, high relief, and many small headwater streams. Which evidence-based conclusion is strongest?','It must be in the Coastal Plain.','It is more consistent with a mountain region than a low-relief region.','It must be inside Atlanta.','It proves the site cannot be developed.','B',None,0,'The clues support a mountain-region hypothesis without overclaiming.',None,2,1),
 ('mcq','Why is “this county is Piedmont” sometimes too simple for physical analysis?','Counties have no landforms.','Physical transition zones do not have to follow political boundaries.','Piedmont is a city.','County boundaries control geology.','B',None,0,'Physical and political boundaries are different systems.',None,2,2),
 ('constructed','Choose two Georgia physiographic regions. Compare at least three physical characteristics, then predict one transportation or land-use consequence for each. Explain the mechanism, not just the prediction.',None,None,None,None,None,None,0,'Strong answers connect physical evidence to consequences.','4: accurate comparison, mechanisms, and caveat/transition reasoning; 3: solid comparison and mechanisms; 2: partial; 1: minimal; 0: missing/off-topic.',4,3)],
'mountains-headwaters': [
 ('numeric','A road rises 528 feet over a horizontal distance of 2 miles. Using 5,280 feet per mile, what is the average grade as a percent?',None,None,None,None,None,5.0,0.1,'Grade = rise/run × 100 = 528/10,560 ×100 = 5%.',None,3,1),
 ('mcq','Why can a longer mountain route be preferable to a shorter one?','Distance never matters.','It may reduce grade, engineering difficulty, or safety risk.','Long routes always cost less.','Mountains have no roads.','B',None,0,'Route choice balances distance with grade and other constraints.',None,2,2),
 ('constructed','A county proposes two mountain road routes: Route A is 8 miles and steep; Route B is 12 miles and much flatter. Identify at least four pieces of evidence needed before choosing and explain one tradeoff.',None,None,None,None,None,None,0,'A strong response considers construction, safety, travel, environment, maintenance, and cost.','4: 4+ relevant evidence needs plus explicit tradeoff and uncertainty; 3: adequate evidence and tradeoff; 2: partial; 1: minimal; 0: missing.',4,3)],
'fall-line-systems': [
 ('mcq','Which explanation best uses the Fall Line as one factor rather than a deterministic cause?','Cities had to exist there.','Changes in river gradient could create transfer or power opportunities that interacted with roads, markets, and policy.','The Fall Line is a county boundary.','Every Fall Line city developed identically.','B',None,0,'Multi-cause explanation is stronger than inevitability.',None,2,1),
 ('constructed','Explain a causal chain by which a river-gradient transition could influence settlement. Then name two non-geographic factors that could strengthen or weaken that pattern.',None,None,None,None,None,None,0,'The response should identify mechanism and alternative factors.','4: clear causal chain + 2 relevant modifying factors + limitation; 3: chain + factors; 2: partial; 1: minimal; 0: missing.',4,2)],
'fourteen-basins': [
 ('mcq','Georgia EPD identifies how many major river basins in Georgia?','5','10','14','159','C',None,0,'Georgia has 14 major river basins in the cited EPD material.',None,2,1),
 ('mcq','Two towns are in the same river basin. What can you conclude with confidence?','Water from each town reaches every other point in the basin.','Both lie within land draining to the same major river system, but exact flow paths still require tributary tracing.','They are in the same county.','They use the same water utility.','B',None,0,'Same basin does not mean identical tributary path.',None,2,2),
 ('constructed','A proposed facility lies near a basin boundary. Explain why a planner should verify the exact drainage path before predicting downstream effects, and name at least three data layers that would help.',None,None,None,None,None,None,0,'Strong answers combine topography/hydrography with infrastructure and land use.','4: drainage logic + 3+ useful layers + uncertainty; 3: sound logic + layers; 2: partial; 1: minimal; 0: missing.',4,3)],
'reservoir-tradeoffs': [
 ('numeric','A reservoir has 500,000 acre-feet of usable storage and declines to 410,000. What percentage of the starting usable storage was drawn down?',None,None,None,None,None,18.0,0.1,'90,000 / 500,000 ×100 = 18%.',None,3,1),
 ('mcq','Why is an 18% drawdown not enough by itself to declare an emergency?','Percentages are useless.','Season, inflow forecast, demand, operating rules, and required releases affect interpretation.','Reservoirs never change level.','Only population matters.','B',None,0,'Context determines risk.',None,2,2),
 ('constructed','A drought is forecast while a reservoir also provides recreation, downstream flow, and water supply. Propose a decision framework that balances at least three objectives and identifies two measurements you would monitor weekly.',None,None,None,None,None,None,0,'Strong response explains tradeoffs and monitoring.', '4: 3+ objectives, 2+ metrics, explicit tradeoffs and trigger logic; 3: adequate; 2: partial; 1: minimal; 0: missing.',4,3)],
'water-quality-evidence': [
 ('numeric','Turbidity at a downstream station rises from 10 to 95 units after a storm. By how many units did it increase?',None,None,None,None,None,85.0,0.01,'95 - 10 = 85.',None,2,1),
 ('mcq','The downstream increase is much larger than upstream. What is the strongest immediate conclusion?','A construction site is proven guilty.','Conditions changed more downstream, but source attribution needs additional sampling and context.','The data are meaningless.','Wastewater caused it.','B',None,0,'Observation is not the same as causal attribution.',None,2,2),
 ('constructed','Design a four-part sampling plan to test whether one construction site is contributing storm-related turbidity. Include locations, timing, comparison logic, and one confounding factor.',None,None,None,None,None,None,0,'The plan should allow comparison and avoid single-sample overclaiming.','4: locations + timing + comparisons + confounder + repeatability; 3: mostly complete; 2: partial; 1: minimal; 0: missing.',4,3)],
'history-geography-causation': [
 ('mcq','Which statement is the strongest historical reasoning?','A port automatically creates a large city.','Port access can lower transport costs, but growth also depends on investment, policy, labor, markets, technology, and events.','Geography never matters.','One cause explains every city.','B',None,0,'Historical causation is usually multi-factor.',None,2,1),
 ('constructed','Choose a Georgia city or region. Write a multi-cause explanation for one historical development using one geographic factor and at least three non-geographic factors. Rank which factor you think mattered most and defend the ranking.',None,None,None,None,None,None,0,'Strong responses rank and connect factors rather than list them.','4: 4+ factors, mechanisms, ranking, counterpoint; 3: sound multi-cause explanation; 2: partial; 1: list only; 0: missing.',4,2)],
'source-detective': [
 ('mcq','A 1920s promotional brochure calls a town “Georgia’s greatest investment opportunity.” What does that source establish most directly?','The town objectively had the strongest economy.','Promoters wanted to persuade an audience to invest.','Every resident agreed.','Later census data must show growth.','B',None,0,'Purpose and audience are direct evidence; economic superiority needs corroboration.',None,2,1),
 ('constructed','A newspaper editorial, census table, photograph, and government report disagree about whether a community was prospering. Explain how you would use all four without assuming one source is automatically correct.',None,None,None,None,None,None,0,'Strong answer addresses purpose, type, corroboration, time, and different measures of prosperity.','4: evaluates each type, corroborates, contextualizes, and defines claim; 3: solid comparison; 2: partial; 1: minimal; 0: missing.',4,2)],
'history-place-capstone': [
 ('mcq','What makes a causal chain stronger than a list of factors?','It contains more words.','It explains the mechanism linking a factor to an outcome.','It avoids evidence.','It uses only geography.','B',None,0,'Mechanism is central to causal reasoning.',None,2,1),
 ('constructed','Place A has a river landing, later gains a rail junction, and grows rapidly. Place B has a river landing but no rail junction and grows slowly. Build a defensible explanation, state what this comparison suggests, and name two pieces of evidence needed before claiming rail caused the difference.',None,None,None,None,None,None,0,'Strong answer uses comparison while avoiding causal overclaiming.','4: mechanism + comparison + 2 evidence needs + alternative explanation; 3: solid; 2: partial; 1: minimal; 0: missing.',4,2)],
'industry-location': [
 ('mcq','Why might a food-processing plant and a software company prefer different Georgia locations?','Only one uses workers.','Their relative needs for inputs, transport, water/power, skilled labor, suppliers, and customers differ.','Software cannot operate in Georgia.','All industries choose the cheapest land.','B',None,0,'Location factors depend on business model.',None,2,1),
 ('constructed','Compare site-selection priorities for a food processor and a technology firm. Give five factors for each, identify two overlaps, and explain why the weights should differ.',None,None,None,None,None,None,0,'Strong answer distinguishes factors from their weights.','4: 5+ each, overlaps, weighting logic, tradeoff; 3: good comparison; 2: partial; 1: minimal; 0: missing.',4,2)],
'economic-impact-tradeoffs': [
 ('numeric','A fictional public infrastructure package costs $12,000,000 and a project announces 800 jobs. What is the simple public cost per announced job in dollars?',None,None,None,None,None,15000.0,1.0,'12,000,000 / 800 = 15,000.',None,3,1),
 ('mcq','Why should $15,000 per announced job not be treated as a complete cost-benefit analysis?','Because division is invalid.','It omits wages, tax revenue, job realization, asset life, spillovers, alternatives, and other costs/benefits.','Jobs have no value.','Infrastructure is always free.','B',None,0,'The ratio is one metric, not the full decision.',None,2,2),
 ('constructed','A county is considering the $12 million package above. Write a recommendation framework with at least five additional metrics and explain the opportunity cost question the county should ask.',None,None,None,None,None,None,0,'Strong response includes benefits, costs, risk, and alternative use of funds.','4: 5+ metrics + opportunity cost + risk/conditions; 3: adequate; 2: partial; 1: minimal; 0: missing.',4,3)],
'business-expansion-capstone': [
 ('numeric','A site scores 80 on transportation with a 40% weight, 70 on labor with a 30% weight, and 90 on utilities with a 30% weight. What is its weighted score?',None,None,None,None,None,80.0,0.1,'80×0.4 + 70×0.3 + 90×0.3 = 80.',None,3,1),
 ('mcq','What does sensitivity analysis test?','Whether the spreadsheet has colors.','Whether reasonable changes in assumptions or weights change the recommendation.','Whether one score is above zero.','Whether all sites are identical.','B',None,0,'Sensitivity analysis measures robustness to assumptions.',None,2,2),
 ('constructed','Three Georgia sites score closely in a weighted model. Explain how you would perform sensitivity analysis, identify two qualitative factors the model may miss, and state when you would delay the decision to collect more evidence.',None,None,None,None,None,None,0,'Strong response tests changed weights and acknowledges unmodeled evidence.','4: clear sensitivity method + 2 factors + decision threshold/uncertainty; 3: adequate; 2: partial; 1: minimal; 0: missing.',4,3)],
}

LESSON_SKILLS = {
'five-regions-constraints':['physical-regions','map-reasoning','critical-thinking'],
'mountains-headwaters':['mountains-relief','quantitative','critical-thinking'],
'fall-line-systems':['fall-line','historical-causation','critical-thinking'],
'fourteen-basins':['watersheds','rivers','map-reasoning'],
'reservoir-tradeoffs':['lakes-reservoirs','quantitative','critical-thinking'],
'water-quality-evidence':['water-quality','source-analysis','critical-thinking'],
'history-geography-causation':['historical-causation','civics-history','critical-thinking'],
'source-detective':['source-analysis','historical-causation','critical-thinking'],
'history-place-capstone':['historical-causation','source-analysis','critical-thinking'],
'industry-location':['industry','economics','critical-thinking'],
'economic-impact-tradeoffs':['economics','quantitative','critical-thinking'],
'business-expansion-capstone':['economics','quantitative','industry','critical-thinking'],
# existing deep lessons also receive skill tags
'watersheds-control-flow':['watersheds','rivers','critical-thinking'],
'reservoir-to-tap':['lakes-reservoirs','quantitative','critical-thinking'],
'wastewater-stormwater-risk':['water-quality','watersheds','critical-thinking'],
'water-capstone':['quantitative','watersheds','critical-thinking'],
'ga-network-thinking':['transportation','map-reasoning','critical-thinking'],
'savannah-port-connections':['transportation','economics','map-reasoning'],
'logistics-word-problems':['transportation','quantitative','economics'],
'logistics-capstone':['transportation','economics','critical-thinking'],
}


def _add_column(db, table, column, ddl):
    cols = {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}
    if column not in cols:
        db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}')


def current_academic_year_id(db=None):
    db = db or get_db()
    row = db.execute('SELECT id FROM academic_years WHERE active=1 ORDER BY id DESC LIMIT 1').fetchone()
    return row['id'] if row else None


def init_phase5():
    db = get_db()
    db.executescript(PHASE5_SCHEMA)
    _add_column(db, 'grade_events', 'academic_year_id', 'INTEGER REFERENCES academic_years(id)')
    _add_column(db, 'game_attempts', 'academic_year_id', 'INTEGER REFERENCES academic_years(id)')
    db.execute("INSERT OR IGNORE INTO academic_years(name,starts_on,ends_on,active) VALUES ('2026–2027','2026-07-01','2027-06-30',0)")
    if not db.execute('SELECT 1 FROM academic_years WHERE active=1 LIMIT 1').fetchone():
        db.execute("UPDATE academic_years SET active=1 WHERE name='2026–2027'")
    year_id = current_academic_year_id(db)
    db.execute('UPDATE grade_events SET academic_year_id=? WHERE academic_year_id IS NULL', (year_id,))
    db.execute('UPDATE game_attempts SET academic_year_id=? WHERE academic_year_id IS NULL', (year_id,))
    for row in SKILLS:
        db.execute('INSERT OR IGNORE INTO skills(skill_key,label,category,description) VALUES (?,?,?,?)', row)
    for row in SOURCES:
        db.execute('INSERT OR IGNORE INTO sources(name,agency,url,category,verified_on,refresh_days) VALUES (?,?,?,?,?,?)', row)
    for row in COURSES:
        db.execute('INSERT OR IGNORE INTO courses(title,slug,description,sort_order) VALUES (?,?,?,?)', row)
    db.commit()
    course_ids={r['slug']:r['id'] for r in db.execute('SELECT id,slug FROM courses')}
    for cslug,title,slug,desc,eq,sort_order in MODULES:
        db.execute('INSERT OR IGNORE INTO modules(course_id,title,slug,description,essential_question,sort_order) VALUES (?,?,?,?,?,?)',
                   (course_ids[cslug],title,slug,desc,eq,sort_order))
    db.commit()
    source_ids={r['name']:r['id'] for r in db.execute('SELECT id,name FROM sources')}
    module_ids={r['slug']:r['id'] for r in db.execute('SELECT id,slug FROM modules')}
    for mod,title,slug,min_age,max_age,summary,obj,content,worked,remediation,source_name,xp,sort_order in LESSONS:
        db.execute('''INSERT OR IGNORE INTO lessons(module_id,title,slug,min_age,max_age,summary,learning_objectives,content,worked_example,remediation,source_id,xp,sort_order)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (module_ids[mod],title,slug,min_age,max_age,summary,obj,content,worked,remediation,source_ids[source_name],xp,sort_order))
    db.commit()
    lesson_ids={r['slug']:r['id'] for r in db.execute('SELECT id,slug FROM lessons')}
    for slug, items in ITEMS.items():
        lid=lesson_ids[slug]
        if not db.execute('SELECT 1 FROM assessment_items WHERE lesson_id=? LIMIT 1',(lid,)).fetchone():
            for item in items:
                typ,prompt,a,b,c,d,correct,numeric,tolerance,explanation,rubric,points,sort_order=item
                db.execute('''INSERT INTO assessment_items(lesson_id,item_type,prompt,choice_a,choice_b,choice_c,choice_d,correct_text,numeric_answer,numeric_tolerance,explanation,rubric,points,sort_order)
                              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (lid,typ,prompt,a,b,c,d,correct,numeric,tolerance,explanation,rubric,points,sort_order))
    skill_ids={r['skill_key']:r['id'] for r in db.execute('SELECT id,skill_key FROM skills')}
    for slug, keys in LESSON_SKILLS.items():
        lid=lesson_ids.get(slug)
        if not lid: continue
        for k in keys:
            db.execute('INSERT OR IGNORE INTO lesson_skills(lesson_id,skill_id,weight) VALUES (?,?,1)',(lid,skill_ids[k]))
    db.commit()


def skill_stats(student_id):
    db=get_db()
    rows=db.execute('''SELECT s.skill_key,s.label,s.category,s.description,
      COUNT(DISTINCT CASE WHEN p.attempts>0 THEN l.id END) attempted_lessons,
      COALESCE(AVG(CASE WHEN p.attempts>0 THEN COALESCE(p.final_score,p.best_auto_score) END),0) lesson_score
      FROM skills s LEFT JOIN lesson_skills ls ON ls.skill_id=s.id
      LEFT JOIN lessons l ON l.id=ls.lesson_id
      LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=?
      GROUP BY s.id ORDER BY s.category,s.label''',(student_id,)).fetchall()
    game={r['skill_key']:r for r in db.execute('''SELECT skill_key,COUNT(*) attempts,AVG(score) score FROM game_skill_attempts
      WHERE user_id=? GROUP BY skill_key''',(student_id,)).fetchall()}
    result=[]
    for r in rows:
        lesson_n=r['attempted_lessons'] or 0
        lesson_score=float(r['lesson_score'] or 0)
        g=game.get(r['skill_key'])
        game_n=(g['attempts'] if g else 0) or 0
        game_score=float(g['score'] if g else 0)
        if lesson_n and game_n:
            score=(lesson_score*lesson_n + game_score*game_n)/(lesson_n+game_n)
        elif lesson_n: score=lesson_score
        elif game_n: score=game_score
        else: score=0
        result.append({'skill_key':r['skill_key'],'label':r['label'],'category':r['category'],'description':r['description'],
                       'score':score,'evidence_count':lesson_n+game_n})
    return result


def assignment_rows(student_id, include_archived=False):
    db=get_db()
    where='' if include_archived else 'AND a.archived=0'
    rows=db.execute(f'''SELECT a.*, ay.name academic_year,l.title lesson_title,l.slug lesson_slug,
      m.title module_title,m.slug module_slug
      FROM assignments a JOIN academic_years ay ON ay.id=a.academic_year_id
      LEFT JOIN lessons l ON l.id=a.lesson_id LEFT JOIN modules m ON m.id=a.module_id
      WHERE a.student_id=? {where} ORDER BY CASE WHEN a.due_date IS NULL THEN 1 ELSE 0 END,a.due_date,a.id DESC''',(student_id,)).fetchall()
    out=[]
    today=date.today().isoformat()
    for r in rows:
        if r['lesson_id']:
            p=db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?',(student_id,r['lesson_id'])).fetchone()
            score=float((p['final_score'] if p and p['final_score'] is not None else p['best_auto_score'] if p else 0) or 0)
            completed=bool(p and p['attempts']>0 and score>=r['min_score'])
            progress_text=f'{score:.0f}%'
        else:
            stats=db.execute('''SELECT COUNT(l.id) total,SUM(CASE WHEN p.attempts>0 AND COALESCE(p.final_score,p.best_auto_score)>=? THEN 1 ELSE 0 END) done
                FROM lessons l LEFT JOIN progress p ON p.lesson_id=l.id AND p.user_id=? WHERE l.module_id=?''',(r['min_score'],student_id,r['module_id'])).fetchone()
            total=stats['total'] or 0; done=stats['done'] or 0; completed=total>0 and done==total
            progress_text=f'{done}/{total} lessons'
        status='complete' if completed else ('overdue' if r['due_date'] and r['due_date'] < today else 'assigned')
        d=dict(r); d.update(status=status,progress_text=progress_text); out.append(d)
    return out
