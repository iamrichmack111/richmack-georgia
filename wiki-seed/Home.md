# Richmack Georgia

**Richmack Georgia** is an evergreen Georgia geography and Georgia Studies learning platform for ages **9–14**. It combines structured coursework, interactive mapping, map games, quantitative word problems, constructed responses, assignments, parent controls, academic-year gradebooks, CSV exports, usage analytics, and skill-level recommendations.

The platform is designed to teach **how Georgia works as a connected system**: physical geography influences settlement; rivers support water systems; transportation shapes trade; infrastructure supports cities; history changes places; and economics depends on geography, labor, resources, and networks.

## Production
- Website: https://georgia.richmackos.com
- Backend: `127.0.0.1:5075`
- Production path: `/home/ubuntu/richmack-georgia`
- Container/service: `richmack-georgia`
- Deployment: `git push` → GitHub Actions → `richdeploy georgia`

## Major Capabilities
### Learning
- Age-aware curriculum for ages 9–14
- Worked examples and guided reasoning
- Multi-step word problems
- Constructed responses
- 85% mastery target
- Remediation
- Assignments with due dates and target scores

### Geography
- Leaflet interactive map
- OpenStreetMap basemap
- GeoJSON overlays
- Cities, rivers, lakes, physiographic regions, mountains, transportation, airports, ports, and infrastructure study features

### Family / Administration
- Admin, parent, and student roles
- Deny-by-default parent access
- Family Link Codes
- Parent-created child accounts
- User restrictions
- Password reset/change workflows
- Grade export
- Academic years
- Skill analytics and improvement recommendations

## Wiki Navigation
### Product & Learning
- [[Curriculum]]
- [[Assessment-and-Mastery]]
- [[Analytics-and-Gradebook]]
- [[Parent-and-Student-Accounts]]
- [[Maps-and-GIS]]
- [[Data-Sources-and-Verification]]

### Engineering
- [[Architecture]]
- [[Deployment-and-CI-CD]]
- [[Development-and-Testing]]
- [[Security-and-Privacy]]
- [[Troubleshooting]]

### Project
- [[Project-History]]
- [[Roadmap]]

## Design Principles
1. Reasoning over recall.
2. Real Georgia context and attributable sources.
3. Mastery over completion.
4. Long-term use through academic years and persistent progress.
5. Family privacy through explicit parent/student relationships.
6. Persistent data outside disposable containers.
7. Push-to-deploy only after CI passes.
