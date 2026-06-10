#!/bin/bash
set -euo pipefail

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
# prd.json schema: see prd.schema.json at the repo root.
# ============================================================

MAX_ITERATIONS=${1:-10}
PROMPT_DIR="$HOME/.config/opencode/commands"
CONTAINER="${PWD##*/}_ci"

# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------

is_done() {
    grep -q "<promise>COMPLETE</promise>" log.txt || return 1
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
    echo "See prd.schema.json for the schema and examples/prd.json for a sample." >&2
    exit 1
fi

# ------------------------------------------------------------------
# Initialize environment and log
# ------------------------------------------------------------------

echo "[init] Initializing environment..."
date > log.txt
docker exec "$CONTAINER" make init >> log.txt 2>&1

echo "[acceptance] Evaluating acceptance criteria..."
echo "--- Acceptance ---" >> log.txt
pi --print @"$PROMPT_DIR/acceptance-afk.md" 2>&1 | tee --append log.txt

ALL_DONE=false
if is_done ; then
    ALL_DONE=true
    echo ""
    echo "Completed all tasks!"
    echo "" >> log.txt
    echo "=== COMPLETED ALL TASKS ===" >> log.txt
    date >> log.txt
fi

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
        pi --print @"$PROMPT_DIR/red-afk.md" 2>&1 | tee --append log.txt

        echo "[green] Implementing minimal code..."
        echo "--- Green ---" >> log.txt
        pi --print @"$PROMPT_DIR/green-afk.md" 2>&1 | tee --append log.txt

        echo "[refactor] Improving structure..."
        echo "--- Refactor ---" >> log.txt
        pi --print @"$PROMPT_DIR/refactor-afk.md" 2>&1 | tee --append log.txt

        echo "[tests] Running test suite..."
        echo "--- Tests ---" >> log.txt
        docker exec "$CONTAINER" make tests >> log.txt 2>&1

        echo "[acceptance] Evaluating acceptance criteria..."
        echo "--- Acceptance ---" >> log.txt
        pi --print @"$PROMPT_DIR/acceptance-afk.md" 2>&1 | tee --append log.txt

        if is_done ; then
            ALL_DONE=true
            echo ""
            echo "Completed all tasks!"
            echo "" >> log.txt
            echo "=== COMPLETED ALL TASKS ===" >> log.txt
            date >> log.txt
            break
        fi
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
