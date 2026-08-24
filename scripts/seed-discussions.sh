#!/usr/bin/env bash
set -euo pipefail
OWNER="${OWNER:-iamrichmack111}"
REPO="${REPO:-richmack-georgia}"

repo_id=$(gh api graphql -f query='query($owner:String!,$name:String!){repository(owner:$owner,name:$name){id}}' -f owner="$OWNER" -f name="$REPO" --jq '.data.repository.id')

categories=$(gh api graphql -f query='query($owner:String!,$name:String!){repository(owner:$owner,name:$name){discussionCategories(first:50){nodes{id name}}}}' -f owner="$OWNER" -f name="$REPO")

category_id() {
  local wanted="$1"
  echo "$categories" | jq -r --arg wanted "$wanted" '.data.repository.discussionCategories.nodes[] | select(.name==$wanted) | .id' | head -1
}

GENERAL=$(category_id "General")
IDEAS=$(category_id "Ideas")
QANDA=$(category_id "Q&A")
[ -n "$GENERAL" ] || GENERAL=$(echo "$categories" | jq -r '.data.repository.discussionCategories.nodes[0].id')
[ -n "$IDEAS" ] || IDEAS="$GENERAL"
[ -n "$QANDA" ] || QANDA="$GENERAL"

create_discussion() {
  local cat="$1" title="$2" body="$3"
  gh api graphql -f query='mutation($repo:ID!,$cat:ID!,$title:String!,$body:String!){createDiscussion(input:{repositoryId:$repo,categoryId:$cat,title:$title,body:$body}){discussion{url}}}' \
    -f repo="$repo_id" -f cat="$cat" -f title="$title" -f body="$body" --jq '.data.createDiscussion.discussion.url'
}

create_discussion "$GENERAL" "Welcome to Richmack Georgia" "Richmack Georgia is an evergreen Georgia geography and Georgia Studies platform for ages 9–14. This discussion area is for curriculum feedback, student-testing observations, data-source suggestions, and platform ideas."
create_discussion "$IDEAS" "What should the next Georgia systems project be?" "Current roadmap candidates include a watershed planning project, Savannah-to-Atlanta freight challenge, county infrastructure planning, and a historical/economic evidence investigation. Share ideas for projects that require real reasoning rather than trivia."
create_discussion "$QANDA" "Curriculum and parent/admin questions" "Use this thread for questions about assignments, mastery thresholds, grade exports, parent/student access, academic years, constructed-response review, and skill analytics."
create_discussion "$GENERAL" "Student testing notes" "The platform has been iteratively improved from direct student testing: deeper coursework, reduced repeated prompts, clearer airport/infrastructure visualization, corrected grade aggregation, game grades in the gradebook, and stricter parent data isolation. Continue adding concrete observations here."
