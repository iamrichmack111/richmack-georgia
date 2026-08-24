# Maps and GIS

## Stack
- Leaflet: browser interaction and map engine
- OpenStreetMap: basemap
- GeoJSON: educational overlays

Leaflet is preferred over Folium because the app needs direct click events, custom labels, game state, scoring, layer control, and communication with Flask.

## Geometry Model
```text
City / airport / port / dam → point
River / highway / rail → line
Lake / watershed / physiographic region → polygon
```
Early versions reduced too many features to blue points; Phase 2 corrected this.

## Current Layers
Physiographic regions, mountains, rivers/lakes, transportation, infrastructure, and cities. Important infrastructure uses distinct symbols—for example, airports and ports should be immediately visible.

## Map Hunt
Map Hunt asks students to select a feature from a clue and records the score as a grade. Phase 3.1 expanded the prompt bank and reduced immediate repetition after student testing identified repeated questions.

## Planned GIS Expansion
- all 159 county polygons
- county seats
- official watershed boundaries
- fuller river networks
- reservoirs
- highways and rail
- airports and ports
- dams
- drinking-water and wastewater facilities

The curriculum data should remain independent of the basemap so changing map providers does not destroy the learning system.
