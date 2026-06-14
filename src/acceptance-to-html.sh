#!/bin/bash
set -euo pipefail

INPUT_FILE="${1:?Usage: $0 <input.json>}"
OUTPUT_FILE="acceptance.html"

[ -f "$INPUT_FILE" ]

{
printf '%s\n' '<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Acceptance Criteria</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
</head>
<body>
  <main class="container">'

jq -r '
  def esc: gsub("&"; "&amp;") | gsub("<"; "&lt;") | gsub(">"; "&gt;") | gsub("\""; "&quot;");

  def gold_badge:
    if . == "current" then "🥇 CURRENT"
    elif . == "done" then "✅ DONE"
    else "📋 BACKLOG"
    end;

  def passes_badge:
    if . then "🟢 Passing" else "🔴 Failing" end;

  "<hgroup>
    <h1>" + (.project | esc) + "</h1>
    <p>" + (.description | esc) + "</p>
  </hgroup>

  <h3>Tasks (" + (.tasks | length | tostring) + ")</h3>

" + (.tasks | map(
    "<article>
      <header>
        <h2>" + .id + ". " + (.title | esc) + "</h2>
        <p>" + (.gold | gold_badge) + " &mdash; " + (.passes | passes_badge) + "</p>
      </header>
      <p>" + (.description | esc) + "</p>
      <h3>Acceptance Criteria</h3>
      <ul>
        " + (.acceptance_criteria | map("<li>" + esc + "</li>") | join("\n        ")) + "
      </ul>
    </article>"
  ) | join("\n\n"))
' "$INPUT_FILE"

printf '%s\n' '  </main>
</body>
</html>'
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
