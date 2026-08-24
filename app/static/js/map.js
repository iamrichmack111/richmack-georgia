const map=L.map('map',{zoomControl:true}).setView([32.9,-83.45],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
const groups={regions:L.layerGroup().addTo(map),mountains:L.layerGroup().addTo(map),water:L.layerGroup().addTo(map),transport:L.layerGroup().addTo(map),infra:L.layerGroup().addTo(map),cities:L.layerGroup().addTo(map)};
const palette={regions:'#7c9a65',mountains:'#c29b6c',water:'#46a7dc',transport:'#f1c75b',infra:'#e57c73',cities:'#f0f3f5'};
const featureLayers=[];
let gameFeatures=[];
function styleFor(f){const p=f.properties; if(p.layer==='regions')return{color:'#9cbc7a',weight:1.5,fillColor:palette.regions,fillOpacity:.20}; if(p.layer==='water')return{color:palette.water,weight:p.kind==='river'?4:2,fillColor:palette.water,fillOpacity:.28}; if(p.layer==='transport')return{color:palette.transport,weight:p.kind==='rail'?3:5,dashArray:p.kind==='rail'?'8 7':null,opacity:.92}; return{color:palette[p.layer]||'#fff',weight:2,fillOpacity:.7};}
function pointFor(f,ll){const p=f.properties;if(p.layer==='mountains')return L.marker(ll,{icon:L.divIcon({className:'mountain-icon',html:'▲',iconSize:[24,24]})}); if(p.layer==='infra')return L.circleMarker(ll,{radius:8,color:'#fff',weight:2,fillColor:palette.infra,fillOpacity:.9}); if(p.layer==='cities')return L.circleMarker(ll,{radius:6,color:'#0c1117',weight:2,fillColor:'#fff',fillOpacity:1}); return L.circleMarker(ll,{radius:7,fillOpacity:.85});}
function showFeature(f){const p=f.properties;document.getElementById('feature-card').innerHTML=`<span class="tag">${p.kind.toUpperCase()}</span><h3>${p.name}</h3><p>${p.summary}</p><div class="why-box"><b>Why it matters</b><p>${p.why}</p></div>`;}
function addFeature(f){const layer=L.geoJSON(f,{style:()=>styleFor(f),pointToLayer:(_f,ll)=>pointFor(f,ll),onEachFeature:(_f,l)=>{l.on('click',()=>handleFeatureClick(f,l));l.bindTooltip(f.properties.name,{sticky:true,direction:'top'});}}); const target=groups[f.properties.layer]; if(target)target.addLayer(layer); featureLayers.push({feature:f,layer}); gameFeatures.push(f);}
fetch('/static/data/georgia_atlas.geojson').then(r=>r.json()).then(data=>data.features.forEach(addFeature));
document.querySelectorAll('.layer-toggle').forEach(btn=>btn.addEventListener('click',()=>{const g=groups[btn.dataset.layer];const on=map.hasLayer(g);if(on){map.removeLayer(g);btn.classList.remove('active')}else{g.addTo(map);btn.classList.add('active')}}));

let questions=[],qIndex=0,correct=0,answered=false,start=Date.now();
const challengeBank=[
{name:'Blue Ridge',prompt:'Select the mountainous physiographic region in northeast Georgia.',hint:'Look in the northeast corner of the state.'},
{name:'Chattahoochee River',prompt:'Select the river that begins in north Georgia and passes the Atlanta region before flowing along western Georgia.',hint:'It also connects to Lake Lanier.'},
{name:'I-16 corridor',prompt:'Which transportation corridor directly connects Macon and Savannah?',hint:'Think about port freight moving inland.'},
{name:'Port of Savannah',prompt:'Select Georgia’s major maritime freight gateway.',hint:'Look near the Atlantic coast.'},
{name:'Lake Lanier',prompt:'Select the major reservoir on the upper Chattahoochee system.',hint:'North of Atlanta.'},
{name:'Piedmont',prompt:'Select the physiographic region containing metro Atlanta and much of north-central Georgia.',hint:'It lies between mountain regions and the Coastal Plain.'},
{name:'Brasstown Bald',prompt:'Select Georgia’s highest natural point.',hint:'It is in the Blue Ridge of northeast Georgia.'},
{name:'I-75 corridor',prompt:'Select the major north–south interstate corridor through Macon and Atlanta.',hint:'It continues toward northwest Georgia.'},
{name:'Savannah River',prompt:'Select the river forming much of Georgia’s eastern boundary.',hint:'It reaches the Atlantic at Savannah.'},
{name:'Hartsfield–Jackson Atlanta International Airport',prompt:'Select the major airport just south of Atlanta.',hint:'It is a key air passenger and cargo node.'},
{name:'Coastal Plain',prompt:'Select the broad low-elevation region covering southern Georgia and the coast.',hint:'It includes extensive agricultural land and wetlands.'},
{name:'Macon',prompt:'Select the central Georgia city near the Ocmulgee River and major road corridors.',hint:'I-75 and I-16 connect here.'}
];
function shuffle(a){return [...a].sort(()=>Math.random()-.5)}
function beginGame(){questions=shuffle(challengeBank).slice(0,10);qIndex=0;correct=0;start=Date.now();renderQuestion();}
function renderQuestion(){answered=false;const q=questions[qIndex];document.getElementById('game-progress').textContent=`${qIndex+1} / ${questions.length}`;document.getElementById('game-score').textContent=`${correct} correct`;document.getElementById('challenge-prompt').textContent=q.prompt;document.getElementById('challenge-hint').textContent=q.hint;document.getElementById('game-feedback').innerHTML='';document.getElementById('next-challenge').hidden=true;}
function handleFeatureClick(f,l){showFeature(f);if(!window.RICHMACK_GAME_MODE||answered)return;answered=true;const q=questions[qIndex];const ok=f.properties.name===q.name;if(ok){correct++;document.getElementById('game-feedback').innerHTML='<div class="game-good">Correct. Now explain why that feature matters using the detail card above.</div>';if(l.setStyle)l.setStyle({weight:7});}else{document.getElementById('game-feedback').innerHTML=`<div class="game-bad">Not quite. You selected <b>${f.properties.name}</b>. The target was <b>${q.name}</b>.</div>`;}document.getElementById('game-score').textContent=`${correct} correct`;const b=document.getElementById('next-challenge');b.hidden=false;b.textContent=qIndex===questions.length-1?'Finish & save score':'Next challenge';}
async function nextChallenge(){if(qIndex<questions.length-1){qIndex++;renderQuestion();return;}const seconds=Math.round((Date.now()-start)/1000);const pct=Math.round(correct/questions.length*100);document.getElementById('challenge-panel').innerHTML=`<span class="tag">MAP HUNT COMPLETE</span><h2>${pct}%</h2><p>${correct} of ${questions.length} correct in ${seconds} seconds.</p><p class="muted">Your attempt is being saved to your student history.</p><a class="btn" href="/map?game=map-hunt">Play again</a>`;try{await fetch('/api/games/map-hunt/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({correct,total:questions.length,duration_seconds:seconds})});}catch(e){console.warn('score save failed',e);}}
if(window.RICHMACK_GAME_MODE){document.getElementById('next-challenge').addEventListener('click',nextChallenge);setTimeout(beginGame,300);}
