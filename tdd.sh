#!/bin/bash
set -eo pipefail

# ============================================================
# tdd.sh — Automated TDD cycle orchestrator
#
# Usage: ./tdd.sh [max_iterations]
#
# Requires:
#   - prd.json at repo root (see schema below)
#   - $HOME/.config/opencode/commands/{red,green,refactor,acceptance}.md
#   - pi (AI coding assistant) in PATH
#   - Docker container named ${PWD##*/}_ci with make targets:
#     init, tests, mutants, check, format
#
# prd.json schema:
# {
#   "project": "my_app",
#   "description": "...",
#   "tasks": [
#     {
#       "id": "01",
#       "title": "...",
#       "description": "...",
#       "acceptance_criteria": ["..."],
#       "gold": "current|done|backlog",
#       "passes": false,
#       "notes": ""
#     }
#   ]
# }
# ============================================================

MAX_ITERATIONS=${1:-10}
PROMPT_DIR="$HOME/.config/opencode/commands"
CONTAINER="${PWD##*/}_ci"

# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------

fix() {
    echo "[fix] Tests failed. Undoing last commits..."
    echo "--- Fix phase ---" >> log.txt 2>&1
    while ! docker exec "$CONTAINER" make tests >> log.txt 2>&1; do
        if [ "$(git rev-parse HEAD)" = "$CYCLE_HEAD" ]; then
            echo "[fix] Cannot undo further — reached cycle start." >&2
            echo "[fix] Tests still failing after undoing all cycle commits." >&2
            exit 1
        fi
        echo "[fix] Undoing: $(git log --oneline -1)"
        git reset --hard HEAD~1 >> log.txt 2>&1
    done
    echo "[fix] Tests pass after undoing commits."
}

is_done() {
    local output="$1"
    echo "$output" | grep -q "<promise>COMPLETE</promise>" || return 1
    jq -e '.tasks | any(.passes == false)' prd.json && return 1
    jq -e '.tasks | any(.gold == "current")' prd.json && return 1
    jq -e '.tasks | any(.gold == "backlog")' prd.json && return 1
    return 0
}

# ------------------------------------------------------------------
# Pre-flight checks
# ------------------------------------------------------------------

echo "[pre-flight] Checking working tree..."
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working tree is dirty. Commit or stash your changes first." >&2
    exit 1
fi

echo "[pre-flight] Checking prd.json..."
if [ ! -f prd.json ]; then
    echo "Error: prd.json not found in project root." >&2
    echo "" >&2
    echo "Create prd.json with the following schema:" >&2
    echo "{" >&2
    echo '  "project": "my_app",' >&2
    echo '  "description": "...",' >&2
    echo '  "tasks": [' >&2
    echo "    {" >&2
    echo '      "id": "01",' >&2
    echo '      "title": "...",' >&2
    echo '      "description": "...",' >&2
    echo '      "acceptance_criteria": ["..."],' >&2
    echo '      "gold": "current|done|backlog",' >&2
    echo '      "passes": false,' >&2
    echo '      "notes": ""' >&2
    echo "    }" >&2
    echo "  ]" >&2
    echo "}" >&2
    echo "See prd.schema.json for the full schema definition." >&2
    exit 1
fi

# ------------------------------------------------------------------
# Initialize environment and log
# ------------------------------------------------------------------

echo "[init] Initializing environment..."
> log.txt
docker exec "$CONTAINER" make init >> log.txt 2>&1

# ------------------------------------------------------------------
# Main TDD loop
# ------------------------------------------------------------------

for ((i=1; i<=MAX_ITERATIONS; i++)); do
    echo ""
    echo "==============================================================="
    echo "  TDD Cycle $i of $MAX_ITERATIONS"
    echo "==============================================================="
    echo "" >> log.txt
    echo "=== TDD Cycle $i of $MAX_ITERATIONS ===" >> log.txt

    CYCLE_HEAD=$(git rev-parse HEAD)

    echo "[red] Identifying next failing test..."
    echo "--- Red ---" >> log.txt
    pi --print @"$PROMPT_DIR/red.md" >> log.txt 2>&1

    echo "[green] Implementing minimal code..."
    echo "--- Green ---" >> log.txt
    pi --print @"$PROMPT_DIR/green.md" >> log.txt 2>&1

    echo "[refactor] Improving structure..."
    echo "--- Refactor ---" >> log.txt
    pi --print @"$PROMPT_DIR/refactor.md" >> log.txt 2>&1

    echo "[tests] Running test suite..."
    echo "--- Tests ---" >> log.txt
    docker exec "$CONTAINER" make tests >> log.txt 2>&1 || fix

    echo "[acceptance] Evaluating acceptance criteria..."
    echo "--- Acceptance ---" >> log.txt
    ACCEPTANCE_OUTPUT=$(pi --print @"$PROMPT_DIR/acceptance.md")
    echo "$ACCEPTANCE_OUTPUT" >> log.txt 2>&1

    if is_done "$ACCEPTANCE_OUTPUT"; then
        echo ""
        echo "Completed all tasks!"
        echo "" >> log.txt
        echo "=== COMPLETED ALL TASKS ===" >> log.txt
        break
    fi
    sleep 2
done

echo "[mutants] Running mutation tests..."
echo "--- Mutation tests ---" >> log.txt
docker exec "$CONTAINER" make mutants >> log.txt 2>&1

echo "Done." >> log.txt

if [ "$i" -le "$MAX_ITERATIONS" ]; then
    echo ""
    echo "Completed all tasks!"
    exit 0
else
    echo ""
    echo "Reached max iterations ($MAX_ITERATIONS) without completing all tasks."
    echo "Check log.txt for status."
    exit 1
fi
