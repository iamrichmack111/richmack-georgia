const map=L.map('map').setView([32.75,-83.35],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
const groups={regions:L.layerGroup().addTo(map),water:L.layerGroup().addTo(map),cities:L.layerGroup().addTo(map),infra:L.layerGroup().addTo(map)};
fetch('/static/data/georgia_features.geojson').then(r=>r.json()).then(data=>{
  L.geoJSON(data,{pointToLayer:(feature,latlng)=>L.circleMarker(latlng,{radius:8,weight:2,fillOpacity:.8}),onEachFeature:(f,l)=>{
    l.bindPopup(`<strong>${f.properties.name}</strong><br>${f.properties.lesson}<br><small>${f.properties.kind}</small>`);
    const group=groups[f.properties.layer]; if(group) group.addLayer(l);
  }});
});
document.querySelectorAll('[data-layer]').forEach(btn=>btn.addEventListener('click',()=>{const g=groups[btn.dataset.layer];if(map.hasLayer(g)){map.removeLayer(g);btn.style.opacity=.45}else{g.addTo(map);btn.style.opacity=1}}));
