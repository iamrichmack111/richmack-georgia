const map=L.map('map',{zoomControl:true}).setView([32.9,-83.45],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
const groups={regions:L.layerGroup().addTo(map),mountains:L.layerGroup().addTo(map),water:L.layerGroup().addTo(map),transport:L.layerGroup().addTo(map),infra:L.layerGroup().addTo(map),cities:L.layerGroup().addTo(map)};
const palette={regions:'#7c9a65',mountains:'#c29b6c',water:'#46a7dc',transport:'#f1c75b',infra:'#e57c73',cities:'#f0f3f5'};
const featureLayers=[];
let gameFeatures=[];
function styleFor(f){const p=f.properties; if(p.layer==='regions')return{color:'#9cbc7a',weight:1.5,fillColor:palette.regions,fillOpacity:.20}; if(p.layer==='water')return{color:palette.water,weight:p.kind==='river'?4:2,fillColor:palette.water,fillOpacity:.28}; if(p.layer==='transport')return{color:palette.transport,weight:p.kind==='rail'?3:5,dashArray:p.kind==='rail'?'8 7':null,opacity:.92}; return{color:palette[p.layer]||'#fff',weight:2,fillOpacity:.7};}
function pointFor(f,ll){
  const p=f.properties;
  if(p.layer==='mountains') return L.marker(ll,{icon:L.divIcon({className:'mountain-icon',html:'▲',iconSize:[28,28],iconAnchor:[14,14]})});
  if(p.layer==='infra'){
    if(p.kind==='airport') return L.marker(ll,{zIndexOffset:1000,icon:L.divIcon({className:'infra-symbol airport-symbol',html:'✈<span>AIRPORT</span>',iconSize:[92,40],iconAnchor:[20,20]})});
    if(p.kind==='port') return L.marker(ll,{zIndexOffset:900,icon:L.divIcon({className:'infra-symbol port-symbol',html:'⚓<span>PORT</span>',iconSize:[72,38],iconAnchor:[18,19]})});
    if(p.kind==='dam') return L.marker(ll,{icon:L.divIcon({className:'infra-symbol dam-symbol',html:'▰<span>DAM</span>',iconSize:[66,36],iconAnchor:[16,18]})});
    return L.circleMarker(ll,{radius:10,color:'#fff',weight:3,fillColor:palette.infra,fillOpacity:.95});
  }
  if(p.layer==='cities')return L.circleMarker(ll,{radius:7,color:'#0c1117',weight:2,fillColor:'#fff',fillOpacity:1});
  return L.circleMarker(ll,{radius:8,fillOpacity:.9});
}
function showFeature(f){const p=f.properties;document.getElementById('feature-card').innerHTML=`<span class="tag">${p.kind.toUpperCase()}</span><h3>${p.name}</h3><p>${p.summary}</p><div class="why-box"><b>Why it matters</b><p>${p.why}</p></div>`;}
function addFeature(f){const layer=L.geoJSON(f,{style:()=>styleFor(f),pointToLayer:(_f,ll)=>pointFor(f,ll),onEachFeature:(_f,l)=>{l.on('click',()=>handleFeatureClick(f,l));l.bindTooltip(f.properties.name,{sticky:f.properties.kind!=='airport'&&f.properties.kind!=='port',permanent:f.properties.kind==='airport'||f.properties.kind==='port',direction:'top',offset:[0,-10]});}}); const target=groups[f.properties.layer]; if(target)target.addLayer(layer); featureLayers.push({feature:f,layer}); gameFeatures.push(f);}
fetch('/static/data/georgia_atlas.geojson').then(r=>r.json()).then(data=>data.features.forEach(addFeature));
document.querySelectorAll('.layer-toggle').forEach(btn=>btn.addEventListener('click',()=>{const g=groups[btn.dataset.layer];const on=map.hasLayer(g);if(on){map.removeLayer(g);btn.classList.remove('active')}else{g.addTo(map);btn.classList.add('active')}}));

let questions=[],qIndex=0,correct=0,answered=false,start=Date.now();
const challengeBank=[
{name:'Blue Ridge',prompt:'Select the physiographic region containing Georgia’s highest mountain terrain.',hint:'Northeast Georgia.'},
{name:'Blue Ridge',prompt:'Which region would best fit a lesson about steep relief, headwater streams, and northeast Georgia mountains?',hint:'Look northeast.'},
{name:'Piedmont',prompt:'Select the region containing metro Atlanta and much of Georgia’s rolling upland.',hint:'North-central Georgia.'},
{name:'Piedmont',prompt:'A company wants to study the heavily urbanized region around Atlanta. Select that physiographic region.',hint:'Between the mountains and Coastal Plain.'},
{name:'Coastal Plain',prompt:'Select the broad low-elevation region covering southern Georgia and the coast.',hint:'Largest physiographic region in Georgia.'},
{name:'Coastal Plain',prompt:'Which region would you investigate for extensive coastal wetlands and much of south Georgia agriculture?',hint:'South and southeast.'},
{name:'Ridge and Valley',prompt:'Select the northwest Georgia region characterized by long ridges and valleys.',hint:'Northwest, east of the Appalachian Plateau.'},
{name:'Appalachian Plateau',prompt:'Select Georgia’s smallest physiographic region in the extreme northwest.',hint:'Far northwest corner.'},
{name:'Brasstown Bald',prompt:'Select Georgia’s highest natural point.',hint:'Blue Ridge, northeast Georgia.'},
{name:'Chattahoochee River',prompt:'Select the river system tied to Lake Lanier and metro Atlanta’s water geography.',hint:'Runs from north Georgia toward the western side of the state.'},
{name:'Chattahoochee River',prompt:'A watershed planner is tracing water from Lake Lanier downstream toward Columbus. Select the river.',hint:'Western Georgia river system.'},
{name:'Savannah River',prompt:'Select the river forming much of Georgia’s eastern boundary.',hint:'Flows to the Atlantic near Savannah.'},
{name:'Savannah River',prompt:'Which river would matter most when studying the Georgia–South Carolina boundary?',hint:'Eastern border.'},
{name:'Flint River',prompt:'Select the Georgia river that flows southward through the western/central part of the state and joins the Chattahoochee system near Florida.',hint:'Southwest-flowing Georgia river.'},
{name:'Ocmulgee River',prompt:'Select the river associated with Macon and central Georgia.',hint:'Macon lies along it.'},
{name:'Lake Lanier',prompt:'Select the major reservoir on the upper Chattahoochee system.',hint:'North of Atlanta.'},
{name:'Lake Lanier',prompt:'Which reservoir would you connect to Buford Dam and Atlanta-region water-supply lessons?',hint:'Northeast of Atlanta.'},
{name:'I-16 corridor',prompt:'Select the interstate corridor directly linking Macon with Savannah.',hint:'Critical inland connection for Savannah freight.'},
{name:'I-16 corridor',prompt:'A container leaves the Port of Savannah for central Georgia by interstate. Which corridor is the most direct study route?',hint:'Savannah to Macon.'},
{name:'I-75 corridor',prompt:'Select the major north–south interstate corridor through Macon and Atlanta.',hint:'Runs through central/north Georgia.'},
{name:'I-75 corridor',prompt:'Which interstate would a northbound shipment from Macon use to reach metro Atlanta most directly?',hint:'Major north–south route.'},
{name:'I-85 corridor',prompt:'Select the interstate corridor running northeast from Atlanta toward the Carolinas.',hint:'Northeast from Atlanta.'},
{name:'I-20 corridor',prompt:'Select the major east–west interstate through Atlanta.',hint:'Crosses the state west to east.'},
{name:'Port of Savannah',prompt:'Select Georgia’s major maritime freight gateway.',hint:'Atlantic coast near Savannah.'},
{name:'Port of Savannah',prompt:'A logistics analyst is studying ocean containers entering Georgia. Select the infrastructure node that should anchor the analysis.',hint:'Coastal cargo gateway.'},
{name:'Hartsfield–Jackson Atlanta International Airport',prompt:'Select the major airport immediately south of Atlanta.',hint:'Look for the airplane symbol.'},
{name:'Hartsfield–Jackson Atlanta International Airport',prompt:'A time-sensitive air-cargo shipment needs Georgia’s largest aviation hub. Select it.',hint:'South of downtown Atlanta.'},
{name:'Buford Dam',prompt:'Select the dam controlling Lake Lanier at its downstream end.',hint:'Near the southern end of Lake Lanier.'},
{name:'Macon',prompt:'Select the central Georgia city where I-75 and I-16 connect.',hint:'Important inland crossroads.'},
{name:'Savannah',prompt:'Select the coastal city associated with Georgia’s major seaport.',hint:'Atlantic coast.'},
{name:'Atlanta',prompt:'Select Georgia’s largest metro transportation hub and state capital.',hint:'North-central Georgia.'},
{name:'Columbus',prompt:'Select the western Georgia city on the Chattahoochee River.',hint:'Near the Alabama border.'}
];
function shuffle(a){return [...a].sort(()=>Math.random()-.5)}
function beginGame(){const last=JSON.parse(sessionStorage.getItem('richmackLastMapQuestions')||'[]');const fresh=challengeBank.filter(q=>!last.includes(q.prompt));const pool=fresh.length>=10?fresh:challengeBank;questions=shuffle(pool).slice(0,10);sessionStorage.setItem('richmackLastMapQuestions',JSON.stringify(questions.map(q=>q.prompt)));qIndex=0;correct=0;start=Date.now();renderQuestion();}
function renderQuestion(){answered=false;const q=questions[qIndex];document.getElementById('game-progress').textContent=`${qIndex+1} / ${questions.length}`;document.getElementById('game-score').textContent=`${correct} correct`;document.getElementById('challenge-prompt').textContent=q.prompt;document.getElementById('challenge-hint').textContent=q.hint;document.getElementById('game-feedback').innerHTML='';document.getElementById('next-challenge').hidden=true;}
function handleFeatureClick(f,l){showFeature(f);if(!window.RICHMACK_GAME_MODE||answered)return;answered=true;const q=questions[qIndex];const ok=f.properties.name===q.name;if(ok){correct++;document.getElementById('game-feedback').innerHTML='<div class="game-good">Correct. Now explain why that feature matters using the detail card above.</div>';if(l.setStyle)l.setStyle({weight:7});}else{document.getElementById('game-feedback').innerHTML=`<div class="game-bad">Not quite. You selected <b>${f.properties.name}</b>. The target was <b>${q.name}</b>.</div>`;}document.getElementById('game-score').textContent=`${correct} correct`;const b=document.getElementById('next-challenge');b.hidden=false;b.textContent=qIndex===questions.length-1?'Finish & save score':'Next challenge';}
async function nextChallenge(){if(qIndex<questions.length-1){qIndex++;renderQuestion();return;}const seconds=Math.round((Date.now()-start)/1000);const pct=Math.round(correct/questions.length*100);document.getElementById('challenge-panel').innerHTML=`<span class="tag">MAP HUNT COMPLETE</span><h2>${pct}%</h2><p>${correct} of ${questions.length} correct in ${seconds} seconds.</p><p class="muted">Your attempt is being saved to your student history.</p><a class="btn" href="/map?game=map-hunt">Play again</a>`;try{await fetch('/api/games/map-hunt/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({correct,total:questions.length,duration_seconds:seconds})});}catch(e){console.warn('score save failed',e);}}
if(window.RICHMACK_GAME_MODE){document.getElementById('next-challenge').addEventListener('click',nextChallenge);setTimeout(beginGame,300);}
