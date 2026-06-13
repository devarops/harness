#!/bin/bash
set -euo pipefail

# ============================================================
# evolve.sh — Continuous improvement daemon
#
# Usage: ./evolve.sh [max_iterations]
#
# Requires:
#   - acceptance.json at repo root (see acceptance.schema.json)
#   - $HOME/.config/opencode/commands/{refactor,acceptance,score}-afk.md
#   - pi (AI coding assistant) in PATH
#   - goodtables (Frictionless Data) in PATH
#   - Docker container named ${PWD##*/}_ci with make targets:
#     init, tests, mutants, check, format
# ============================================================

MAX_ITERATIONS=${1:-10}
MODEL="deepseek/deepseek-v4-flash"
MODEL_1="github-copilot/gemini-3-flash-preview"
MODEL_2="opencode/deepseek-v4-flash-free"
MODEL_3="openrouter/qwen/qwen3-coder:free"
PROMPT_DIR="$HOME/.config/opencode/commands"
CONTAINER="${PWD##*/}_ci"
DETAIL_CSV="score_detail.csv"
AGGREGATE_CSV="score_aggregate.csv"

# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------

offspring_died() {
    git reset --hard HEAD~1
    OFFSPRING_SURVIVED=false
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
jsonschema -i acceptance.json "$HOME/repositorios/tdd/acceptance.schema.json" 2>&1 || {
    echo "Error: acceptance.json failed schema validation." >&2
    echo "See acceptance.schema.json for the correct schema." >&2
    exit 1
}

# ------------------------------------------------------------------
# Initialize environment and log
# ------------------------------------------------------------------

echo "[init] Initializing environment..."
for exclude_file in log.txt "$DETAIL_CSV" "$AGGREGATE_CSV"; do
    grep -q "^${exclude_file}$" .git/info/exclude 2>/dev/null || echo "$exclude_file" >> .git/info/exclude
done
rm -f "$DETAIL_CSV" "$AGGREGATE_CSV" acceptance.tmp
date > log.txt
echo "--- Init ---" >> log.txt
docker exec "$CONTAINER" make init >> log.txt 2>&1

# ------------------------------------------------------------------
# Initialize CSV files
# ------------------------------------------------------------------

echo "[init] Creating evolution CSV files..."
echo "sha,reviewer,bloaters,object_orientation_abusers,change_preventers,dispensables,couplers" > "$DETAIL_CSV"
echo "sha,bloaters_median,object_orientation_abusers_median,change_preventers_median,dispensables_median,couplers_median,mean" > "$AGGREGATE_CSV"

# ------------------------------------------------------------------
# Pre-loop baseline scoring
# ------------------------------------------------------------------

echo ""
echo "==============================================================="
echo "  Baseline scoring (pre-loop)"
echo "==============================================================="
echo "" >> log.txt
echo "=== Baseline scoring ===" >> log.txt

SHA=$(git rev-parse --short HEAD)
echo "[score] Baseline SHA: $SHA" | tee --append log.txt

for ((j=1; j<=3; j++)); do
    model_var="MODEL_$j"
    echo "$SHA,${!model_var},,,,,," >> "$DETAIL_CSV"
    pi --models "$model_var" --no-session --print "$(<"$PROMPT_DIR/score-afk.md")" 2>&1 | tee --append log.txt
    goodtables "$DETAIL_CSV" 2>&1 | tee --append log.txt || {
        sed -i '$ d' "$DETAIL_CSV"
        j=$((j - 1))
    }
done

echo "[score] Computing aggregate from baseline..." | tee --append log.txt
tail -3 "$DETAIL_CSV" | awk -F, -v OFS=, '
{
    for (k = 3; k <= 7; k++) {
        vals[k][NR] = $k
    }
    sha = $1
}
END {
    sum = 0
    for (k = 3; k <= 7; k++) {
        n = asort(vals[k])
        if (n % 2 == 1) {
            med = vals[k][(n + 1) / 2]
        } else {
            med = int((vals[k][n / 2] + vals[k][n / 2 + 1]) / 2)
        }
        printf "%s%s", (k == 3 ? sha OFS : ""), med
        if (k < 7) printf OFS
        sum += med
    }
    mean = int((sum / 5) + 0.5)
    printf OFS "%d\n", mean
}
' >> "$AGGREGATE_CSV"

goodtables "$AGGREGATE_CSV" 2>&1 | tee --append log.txt

# ------------------------------------------------------------------
# Main Evolution loop
# ------------------------------------------------------------------

CONVERGED=false

for ((i=1; i<=MAX_ITERATIONS; i++)); do
    [ "$CONVERGED" = true ] && break

    OFFSPRING_SURVIVED=true

    echo ""
    echo "==============================================================="
    echo "  Evolution cycle $i of $MAX_ITERATIONS"
    echo "==============================================================="
    echo "" >> log.txt
    echo "=== Evolution cycle $i of $MAX_ITERATIONS ===" >> log.txt

    # --- Refactor phase ---

    echo "[refactor] Resetting acceptance.json to HEAD..." | tee --append log.txt
    git checkout -- acceptance.json 2>&1 | tee --append log.txt

    echo "[refactor] Running refactor prompt..." | tee --append log.txt
    echo "--- Refactor ---" >> log.txt
    pi --models "$MODEL" --no-session --print "$(<"$PROMPT_DIR/refactor-afk.md")" 2>&1 | tee --append log.txt

    echo "[refactor] Running test suite..." | tee --append log.txt
    echo "--- Tests ---" >> log.txt
    docker exec "$CONTAINER" make tests >> log.txt 2>&1 || offspring_died
    [ "$OFFSPRING_SURVIVED" = false ] && continue

    echo "[refactor] Checking working tree is clean..." | tee --append log.txt
    [ -z "$(git status --porcelain)" ] || offspring_died
    [ "$OFFSPRING_SURVIVED" = false ] && continue

    # --- Acceptance phase ---

    echo "[acceptance] Resetting acceptance.json passes to false..." | tee --append log.txt
    jq '.tasks |= map(.passes = false)' acceptance.json > /tmp/acceptance.tmp && mv /tmp/acceptance.tmp acceptance.json

    echo "[acceptance] Running acceptance prompt..." | tee --append log.txt
    echo "--- Acceptance ---" >> log.txt
    pi --models "$MODEL" --no-session --print "$(<"$PROMPT_DIR/acceptance-afk.md")" 2>&1 | tee --append log.txt

    echo "[acceptance] Checking for failing acceptance criteria..." | tee --append log.txt
    jq -e '.tasks | any(.passes == false)' acceptance.json && offspring_died
    [ "$OFFSPRING_SURVIVED" = false ] && continue

    # --- Mutation phase ---

    echo "[mutants] Running mutation tests..." | tee --append log.txt
    echo "--- Mutation tests ---" >> log.txt
    docker exec "$CONTAINER" make mutants >> log.txt 2>&1 || offspring_died
    [ "$OFFSPRING_SURVIVED" = false ] && continue

    # --- Score phase ---

    echo "[score] Scoring current commit..." | tee --append log.txt
    echo "--- Score ---" >> log.txt

    SHA=$(git rev-parse --short HEAD)
    echo "[score] SHA: $SHA" | tee --append log.txt

    for ((j=1; j<=3; j++)); do
        model_var="MODEL_$j"
        echo "$SHA,${!model_var},,,,,," >> "$DETAIL_CSV"
        pi --models "${!model_var}" --no-session --print "$(<"$PROMPT_DIR/score-afk.md")" 2>&1 | tee --append log.txt
        goodtables "$DETAIL_CSV" 2>&1 | tee --append log.txt || {
            sed -i '$ d' "$DETAIL_CSV"
            j=$((j - 1))
        }
    done

    echo "[score] Computing aggregate..." | tee --append log.txt
    tail -3 "$DETAIL_CSV" | awk -F, -v OFS=, '
    {
        for (k = 3; k <= 7; k++) {
            vals[k][NR] = $k
        }
        sha = $1
    }
    END {
        sum = 0
        for (k = 3; k <= 7; k++) {
            n = asort(vals[k])
            if (n % 2 == 1) {
                med = vals[k][(n + 1) / 2]
            } else {
                med = int((vals[k][n / 2] + vals[k][n / 2 + 1]) / 2)
            }
            printf "%s%s", (k == 3 ? sha OFS : ""), med
            if (k < 7) printf OFS
            sum += med
        }
        mean = int((sum / 5) + 0.5)
        printf OFS "%d\n", mean
    }
    ' >> "$AGGREGATE_CSV"

    goodtables "$AGGREGATE_CSV" 2>&1 | tee --append log.txt

    # --- Score trend check ---

    AGG_COUNT=$(tail -n +2 "$AGGREGATE_CSV" | wc -l)
    if [ "$AGG_COUNT" -ge 2 ]; then
        LAST_SCORE=$(tail -1 "$AGGREGATE_CSV" | awk -F, '{print $NF}')
        PREV_SCORE=$(tail -2 "$AGGREGATE_CSV" | head -1 | awk -F, '{print $NF}')
        if [ "$LAST_SCORE" -lt "$PREV_SCORE" ]; then
            echo "[score] Score decreased ($LAST_SCORE < $PREV_SCORE), rolling back..." | tee --append log.txt
            sed -i '$ d' "$AGGREGATE_CSV"
            DETAIL_LINES=$(wc -l < "$DETAIL_CSV")
            sed -i "$((DETAIL_LINES - 2)),${DETAIL_LINES}d" "$DETAIL_CSV"
            offspring_died
        fi
    fi
    [ "$OFFSPRING_SURVIVED" = false ] && continue

    # --- Convergence check ---

    ROW_COUNT=$(tail -n +2 "$AGGREGATE_CSV" | wc -l)
    if [ "$ROW_COUNT" -ge 3 ]; then
        MEANS=$(tail -3 "$AGGREGATE_CSV" | awk -F, '{print $NF}')
        UNIQUE=$(echo "$MEANS" | sort -u | wc -l)
        if [ "$UNIQUE" -eq 1 ]; then
            echo ""
            echo "Convergence achieved! Three consecutive equal means: $MEANS" | tee --append log.txt
            CONVERGED=true
            break
        fi
    fi

    echo ""
    echo "Evolution cycle $i completed. Mean this cycle: $(tail -1 "$AGGREGATE_CSV" | awk -F, '{print $NF}')"
    echo "Starting next cycle after a short break..."
    sleep 60
    date >> log.txt
done

# ------------------------------------------------------------------
# Final output
# ------------------------------------------------------------------

echo "Done." >> log.txt

if [ "$CONVERGED" = true ]; then
    echo ""
    echo "Convergence achieved!"
    exit 0
else
    echo ""
    echo "Reached max iterations ($MAX_ITERATIONS) without achieving convergence."
    echo "Check log.txt and CSV files for status."
    exit 1
fi
