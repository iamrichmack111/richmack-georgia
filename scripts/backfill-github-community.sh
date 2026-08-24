#!/usr/bin/env bash
set -euo pipefail
OWNER="${OWNER:-iamrichmack111}"
REPO="${REPO:-richmack-georgia}"
R="$OWNER/$REPO"

create_closed_issue() {
  local title="$1" body="$2"
  local url number
  url=$(gh issue create --repo "$R" --title "$title" --body "$body" --label bug)
  number=${url##*/}
  gh issue comment "$number" --repo "$R" --body "Resolved in the reconstructed Phase 0.1–0.5 development history. This issue was backfilled to document tested user feedback and the resulting fix."
  gh issue close "$number" --repo "$R" --reason completed
}

create_closed_issue "Map atlas rendered geography as generic point markers" "Early map content reduced rivers, regions, and infrastructure to generic markers. Fixed by introducing layered GeoJSON with lines, polygons, feature groups, legends, and a richer systems-atlas presentation."
create_closed_issue "Map Hunt repeated questions too frequently" "Student testing found repeated prompts. Fixed by expanding the challenge bank and avoiding immediate reuse of prior game prompts where possible."
create_closed_issue "Airport was not visually prominent on the atlas" "Student testing found Hartsfield-Jackson difficult to identify. Fixed with a larger airport symbol and permanent label, plus clearer infrastructure symbols."
create_closed_issue "Provisional 100% lesson grade did not appear in admin grades" "A completed objective assessment could show 100% on the lesson page without appearing in the student grade summary. Fixed by correcting grade aggregation and preventing admin accounts from accidentally submitting student coursework."
create_closed_issue "Map Hunt scores were missing from the gradebook" "Game attempts were stored separately and did not appear alongside coursework. Fixed by merging game attempts into gradebook/export views while preserving their Game type."
create_closed_issue "Parent invite could expose multiple students" "An earlier invite option could grant access to all current students. Fixed with deny-by-default parent/student links, no parent-facing student directory, and server-side authorization checks."
create_closed_issue "Parents needed a safe way to add or link children" "Added parent-created child accounts and one-time admin-generated Family Link Codes for existing students."
create_closed_issue "Admin needed user restrictions and password reset controls" "Added account activation controls, per-student course/map/game permissions, individual password resets, forced password changes, and bulk temporary-password reset CSV export."
create_closed_issue "Analytics needed actionable improvement recommendations" "Added course/game usage statistics, skill-level analytics, evidence counts, and performance-based recommendations."

# Roadmap issues remain open.
gh issue create --repo "$R" --title "feat: import official GIS coverage for all 159 Georgia counties" --body "Replace/extend simplified educational geometry with verified county boundaries and scalable official GIS ingestion." --label enhancement || true
gh issue create --repo "$R" --title "feat: add project-based Georgia systems capstones" --body "Add multi-session projects involving water, transportation, economics, history, infrastructure, and evidence-based recommendations." --label enhancement || true

echo 'Issues backfilled.'
