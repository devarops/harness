#!/bin/bash
set -euo pipefail

# ============================================================
# tdd.sh — Automated TDD cycle orchestrator
#
# Usage: ./tdd.sh [max_iterations]
#
# Requires:
#   - acceptance.json at repo root (see acceptance.schema.json)
#   - $HOME/.config/opencode/commands/{red,green,refactor,gold}-afk.md
#   - pi (AI coding assistant) in PATH
#   - Docker container named ${PWD##*/}_ci with make targets:
#     init, tests, mutants, check, format
#
# acceptance.json schema: see acceptance.schema.json at the repo root.
# ============================================================
MAX_ITERATIONS=${1:-10}
MODEL="opencode/*free"
PROMPT_DIR="$HOME/.config/opencode/commands"
CONTAINER="${PWD##*/}_ci"

# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------
terminate_on_success() {
    grep -q "<promise>COMPLETE</promise>" log.txt || { echo "... Acceptance ..." >> log.txt; return 1; }
    jq -e '.tasks | any(.passes == false)' acceptance.json && return 1
    jq -e '.tasks | any(.gold == "current")' acceptance.json && return 1
    jq -e '.tasks | any(.gold == "backlog")' acceptance.json && return 1
    ALL_DONE=true
    echo ""
    echo "Completed all tasks!"
    echo "" >> log.txt
    echo "=== COMPLETED ALL TASKS ===" >> log.txt
    date >> log.txt
    return 0
}
abort_on_fail() {
    if grep -q "<error>FAIL" log.txt; then
        echo "" >&2
        echo "Error: Phase reported failure. Check log.txt for details." >&2
        exit 1
    fi
    echo "... TDD phase ended successfully ..." >> log.txt
    date >> log.txt
}
tdd_phase() {
    local tag="$1"
    local description="$2"
    local label="${tag^}"
    echo "[$tag] $description"
    echo "--- $label ---" >> log.txt
    pi --models "$MODEL" --no-session --print "$(<"$PROMPT_DIR/${tag}-afk.md")" 2>&1 | tee --append log.txt
    abort_on_fail
}

# ------------------------------------------------------------------
# Pre-flight checks
# ------------------------------------------------------------------
echo "[pre-flight] Checking working tree..."
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working tree is dirty. Commit or stash your changes first." >&2
    exit 1
fi
echo "[pre-flight] Checking acceptance.json..."
if [ ! -f acceptance.json ]; then
    echo "Error: acceptance.json not found in project root." >&2
    echo "See acceptance.schema.json for the schema and examples/acceptance.json for a sample." >&2
    exit 1
fi
echo "[pre-flight] Validating acceptance.json against acceptance.schema.json..."
jsonschema -i acceptance.json $HOME/repositorios/tdd/acceptance.schema.json 2>&1 || {
    echo "Error: acceptance.json failed schema validation." >&2
    echo "See acceptance.schema.json for the correct schema." >&2
    exit 1
}

# ------------------------------------------------------------------
# Initialize environment and log
# ------------------------------------------------------------------
echo "[init] Initializing environment..."
grep -q "^log.txt$" .git/info/exclude 2>/dev/null || echo "log.txt" >> .git/info/exclude
date > log.txt
docker exec "$CONTAINER" make init >> log.txt 2>&1
tdd_phase "gold" "Evaluating acceptance criteria..."
ALL_DONE=false
terminate_on_success || true

# ------------------------------------------------------------------
# Main TDD loop
# ------------------------------------------------------------------
if [ "$ALL_DONE" != true ]; then
    for ((i=1; i<=MAX_ITERATIONS; i++)); do
        echo ""
        echo "==============================================================="
        echo "  TDD Cycle $i of $MAX_ITERATIONS"
        echo "==============================================================="
        echo "" >> log.txt
        echo "=== TDD Cycle $i of $MAX_ITERATIONS ===" >> log.txt
        tdd_phase "red" "Writing failing test..."
        tdd_phase "green" "Implementing minimal code..."
        tdd_phase "refactor" "Improving structure..."
        echo "[tests] Running test suite..."
        echo "--- Tests ---" >> log.txt
        docker exec "$CONTAINER" make tests >> log.txt 2>&1
        tdd_phase "gold" "Evaluating acceptance criteria..."
        terminate_on_success && break
        echo ""
        echo "TDD cycle $i completed. Starting next cycle after a short break..."
        sleep 60
        date >> log.txt
    done
fi
echo "[mutants] Running mutation tests..."
echo "--- Mutation tests ---" >> log.txt
docker exec "$CONTAINER" make mutants >> log.txt 2>&1
echo "Done." >> log.txt
if [ "$ALL_DONE" = true ]; then
    echo ""
    echo "Completed all tasks!"
    exit 0
else
    echo ""
    echo "Reached max iterations ($MAX_ITERATIONS) without completing all tasks."
    echo "Check log.txt for status."
    exit 1
fi
