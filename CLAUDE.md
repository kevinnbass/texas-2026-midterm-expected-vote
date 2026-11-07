# CLAUDE.md

Guidance for Claude (or any coding agent) working in this repository.

## What this is

Two published figures comparing each party's 2026 Texas statewide vote with its expected midterm vote:
- `figures/texas_history_and_expected.png`
- `figures/texas_incumbency_history_and_expected.png`

The repository also holds every Texas Secretary of State source file behind them and the code that rebuilds them.
Start with README.md, then METHODOLOGY.md.

## Rules

- **Never edit `data/raw/`.** Those files are the downloaded sources. A new download goes in as a new file, or
  replaces the 2026 file only during a deliberate update (README, "Updating after the canvass"), together with its
  row in `data/SOURCES.csv`.
- **Rebuild before committing.** `./build.sh` must end with `verify: OK`. If a change is meant to alter outputs, copy
  the new outputs over the committed ones in the same commit, regenerate `data/SHA256SUMS` and `RESULTS.md`, and say
  why in the commit message.
- **Numbers come from files.** Every number in README.md, METHODOLOGY.md or a reply must come from `RESULTS.md`,
  `data/derived/` or a command run on `data/`, never from memory.
- **Neutral wording.** Describe both parties the same way: "more Democratic votes than expected", "Republican votes
  within 0.1M of expected". List every race rather than picking examples, and do not attribute causes. The figures
  measure deviations from a pattern, not why they happened.
- **2026 is unofficial** until the state canvass. Keep the "unofficial" marks and the SOS update time (`ASOF` in
  build.sh) in step with the data.

## Commands

```bash
./build.sh                          # rebuild into build/ and compare (needs matplotlib, Pillow; Inter font for byte-identical figures)
./build.sh out --strict             # figures must match byte for byte too
python3 src/fetch_sources.py new/   # download every source again (paced 3 s apart) and check against data/raw/
sha256sum -c data/SHA256SUMS        # integrity of committed files
```

## Layout

- `data/raw/`: SOS downloads (see `data/SOURCES.csv`).
- `data/intermediate/`: parsed and decoded JSON.
- `data/derived/`: the two CSVs the figures are drawn from.
- `figures/panels/`: the four single figures.
- `figures/`: the two combined images.
- `src/`: one script per step, in the order `build.sh` runs them.
- `site/`: the web page's template (`template.html`, filled by `src/build_page.py`) and its browser test (`test_page.mjs`). The page is published as a claude.ai artifact with the figures beside it. After changing the page, run the test and look at its screenshots before publishing.
