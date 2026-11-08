# The 50-state pool for the president's-party slope

`pool_rows_TX.csv` holds the office-year ratios (party's midterm vote ÷ its presidential vote in the state two years earlier)
that join Texas's own offices in estimating the president's-party slope *b*. They never enter a Texas office's baseline *a*.

- U.S. Senate races in all 50 states, 1994–2022 midterms (MIT Election Data and Science Lab, U.S. Senate statewide 1976–2024).
- Governor races in every state that elected one in those midterms (Wikipedia election pages, cross-checked against official files
  and MIT 2018/2022 precinct returns where available).
- Every statewide office in Alaska, Iowa, Indiana, Kansas, Mississippi, Ohio and South Carolina (official state files where they
  could be obtained; each row's source is in that repository).
- Presidential baselines: MIT Election Data and Science Lab, U.S. President 1976–2024.

Exported from https://github.com/kevinnbass/red-states-2026-midterm-expected-vote with
`python3 tools/export_pool_rows.py data/inputs TX pool_rows_TX.csv` (all raw files, sources and checks are in that repository).
`pool_rows_TX_info.json` lists what went in. Remove this folder to get the earlier Texas-only slope back.
