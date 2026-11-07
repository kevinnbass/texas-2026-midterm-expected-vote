#!/usr/bin/env bash
# Rebuild everything from the raw Texas SOS files in data/raw/ into build/ (or the folder given), then compare the
# result with the committed data and figures. Needs Python 3.10+, matplotlib and Pillow.
#   ./build.sh            build into ./build and verify
#   ./build.sh out --strict   build into ./out; figures must match byte for byte too
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-build}
STRICT=${2:-}
ASOF="updated Nov. 4, 2026, 10:48 pm"   # SOS LastUpdatedTime of data/raw/sos_enr_2026/election_53815.json
RAW=data/raw
PY="python3 -I"

$PY src/parse_elchist.py $RAW/sos_elchist_1992_2018 "$OUT/intermediate/elchist_parsed.json"
$PY src/parse_2018.py $RAW/sos_elchist_1992_2018/elchist331_state.htm "$OUT/intermediate/tx2018_races.json"
$PY src/decode_2026.py $RAW/sos_enr_2026/election_53815.json "$OUT/intermediate"
$PY src/build_races_csv.py "$OUT/intermediate" $RAW/sos_results_2020_2024 \
    "$OUT/derived/texas_statewide_2018_2022_2026.csv" --asof "$ASOF"
$PY src/expected_midterm.py "$OUT/intermediate" $RAW/sos_results_2020_2024 "$OUT/derived" > "$OUT/derived/expected_midterm.log"
$PY src/expected_figs.py "$OUT/derived/texas_midterm_vs_presidential.csv" \
    "$OUT/derived/texas_statewide_2018_2022_2026.csv" "$OUT/figures/panels" --asof "$ASOF"
$PY src/splice.py "$OUT/derived/texas_midterm_vs_presidential.csv" "$OUT/figures/panels" "$OUT/figures"
$PY src/results_table.py "$OUT/derived/texas_midterm_vs_presidential.csv" \
    "$OUT/derived/texas_statewide_2018_2022_2026.csv" > "$OUT/RESULTS.md"
$PY src/build_page.py "$OUT/derived/texas_midterm_vs_presidential.csv" \
    "$OUT/derived/texas_statewide_2018_2022_2026.csv" "$OUT/figures" "$OUT/site" > /dev/null
$PY src/verify.py "$OUT" $STRICT
