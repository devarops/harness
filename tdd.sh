#!/bin/bash
set -euo pipefail

# ============================================================
# tdd.sh — Automated TDD cycle orchestrator
#
# Usage: ./tdd.sh [max_iterations]
#
# Requires:
#   - prd.json at repo root (see prd.schema.json)
#   - $HOME/.config/opencode/commands/{red,green,refactor,acceptance}-afk.md
#   - pi (AI coding assistant) in PATH
#   - Docker container named ${PWD##*/}_ci with make targets:
#     init, tests, mutants, check, format
#
# prd.json schema: see prd.schema.json at the repo root.
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
    jq -e '.tasks | any(.passes == false)' prd.json && return 1
    jq -e '.tasks | any(.gold == "current")' prd.json && return 1
    jq -e '.tasks | any(.gold == "backlog")' prd.json && return 1
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
    echo "See prd.schema.json for the schema and examples/prd.json for a sample." >&2
    exit 1
fi

echo "[pre-flight] Validating prd.json against prd.schema.json..."
jsonschema -i prd.json $HOME/repositorios/tdd/prd.schema.json 2>&1 || {
    echo "Error: prd.json failed schema validation." >&2
    echo "See prd.schema.json for the correct schema." >&2
    exit 1
}

# ------------------------------------------------------------------
# Initialize environment and log
# ------------------------------------------------------------------

echo "[init] Initializing environment..."
grep -q "^log.txt$" .git/info/exclude 2>/dev/null || echo "log.txt" >> .git/info/exclude
date > log.txt
docker exec "$CONTAINER" make init >> log.txt 2>&1

echo "[acceptance] Evaluating acceptance criteria..."
echo "--- Acceptance ---" >> log.txt
pi --models "$MODEL" --no-session --print @"$PROMPT_DIR/acceptance-afk.md" 2>&1 | tee --append log.txt
abort_on_fail

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

        echo "[red] Writing failing test..."
        echo "--- Red ---" >> log.txt
        pi --models "$MODEL" --no-session --print @"$PROMPT_DIR/red-afk.md" 2>&1 | tee --append log.txt
        abort_on_fail

        echo "[green] Implementing minimal code..."
        echo "--- Green ---" >> log.txt
        pi --models "$MODEL" --no-session --print @"$PROMPT_DIR/green-afk.md" 2>&1 | tee --append log.txt
        abort_on_fail

        echo "[refactor] Improving structure..."
        echo "--- Refactor ---" >> log.txt
        pi --models "$MODEL" --no-session --print @"$PROMPT_DIR/refactor-afk.md" 2>&1 | tee --append log.txt
        abort_on_fail

        echo "[tests] Running test suite..."
        echo "--- Tests ---" >> log.txt
        docker exec "$CONTAINER" make tests >> log.txt 2>&1

        echo "[acceptance] Evaluating acceptance criteria..."
        echo "--- Acceptance ---" >> log.txt
        pi --models "$MODEL" --no-session --print @"$PROMPT_DIR/acceptance-afk.md" 2>&1 | tee --append log.txt
        abort_on_fail

        terminate_on_success && break
        sleep 2
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
