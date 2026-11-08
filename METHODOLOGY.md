# Methodology

This file describes exactly what the code in `src/` computes. When the two disagree, the code governs. Every number
quoted here is in `RESULTS.md` or `data/derived/`.

## 1. Which votes are counted

**Offices.** These are the ten offices compared over time, matched on the race name with case, spaces and punctuation
removed (`OFFICES` in `src/expected_midterm.py`):

| Key | Race names matched |
|---|---|
| `us_senate` | U.S. Senator |
| `governor` | Governor |
| `lieutenant_governor` | Lieutenant Governor |
| `attorney_general` | Attorney General |
| `comptroller` | Comptroller of Public Accounts |
| `land_commissioner` | Commissioner of the General Land Office |
| `agriculture_commissioner` | Commissioner of Agriculture |
| `railroad_commissioner` | every race starting "Railroad Commissioner" (including unexpired terms) |
| `supreme_court` | every race containing "Supreme Court" (Chief Justice and all places) |
| `cca` | every race containing "Court of Criminal Appeals" (Presiding Judge and all places) |

Any race with "District" in its name is excluded. This keeps out, for example, courts of appeals districts.

**Nominees.** A race counts only if it has exactly one candidate with party `REP` and exactly one with party `DEM`.
Only those two vote totals are used; Libertarian, Green, independent and write-in votes are left out.

**Several races for one office in one year.** The Supreme Court, Court of Criminal Appeals and Railroad Commission
often have more than one race in a year. Their value for that year is the plain average of the qualifying races (the
CSV column `n_races` gives the count).

**Missing races.** There was no U.S. Senate race in 1998, 2010 or 2022. Comptroller 2010 had no Democratic nominee,
so it has no row. A missing office-year is left out of every average.

## 2. The presidential baseline

For midterm year *y*, the baseline for party *p* is that party's presidential nominee's Texas vote in *y* − 2. The
values are:

| Presidential year | Republican | Democrat |
|---|---:|---:|
| 1992 | 2,496,071 | 2,281,815 |
| 1996 | 2,736,167 | 2,459,683 |
| 2000 | 3,799,639 | 2,433,746 |
| 2004 | 4,526,917 | 2,832,704 |
| 2008 | 4,479,328 | 3,528,633 |
| 2012 | 4,569,843 | 3,308,124 |
| 2016 | 4,685,047 | 3,877,868 |
| 2020 | 5,890,347 | 5,259,126 |
| 2024 | 6,393,597 | 4,835,250 |

## 3. The ratio

For office *o*, party *p* and midterm *y*:

  r(o, p, y) = V(o, p, y) / P(p, y − 2)

Here *V* is the party's vote for the office (averaged as in section 1) and *P* is the presidential baseline. The left
panels show 100 × (r − 1), the % change from the presidential vote.

## 4. Plain expectation (figure 1)

  E(o, p, y) = P(p, y − 2) × mean{ r(o, p, y′) : y′ ∈ 1994–2022, y′ ≠ y, office *o* had a race in y′ }

Leaving out year *y* means 2018 and 2022 are not compared against averages that already contain them. For 2026, all
eight midterms from 1994 to 2022 are used.

The dashed lines in the left panel of figure 1 are 100 × (mean r − 1) over 1994–2022, with every available year
included.

## 5. President's-party expectation (figure 2)

Let s(p, y) = 1 if party *p* held the White House at midterm *y*, otherwise 0:

| Midterm | 1994 | 1998 | 2002 | 2006 | 2010 | 2014 | 2018 | 2022 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| President's party | D | D | R | R | D | D | R | D | R |

The model is

  r(o, p, y) = a(o, p) + b × s(p, y)

The intercept *a* is separate for each office and party. The slope *b* is shared by all of them. For each target year
*Y*, both are estimated from the 1994–2022 midterms other than *Y*:

- *b* is the pooled within-group slope. Each office and party pair is a group, and *s̄* and *r̄* are that group's means:

  b = Σ_groups Σ (s − s̄)(r − r̄) / Σ_groups Σ (s − s̄)²

- a(o, p) = mean over the group of (r − b × s).

- E_inc(o, p, Y) = P(p, Y − 2) × (a(o, p) + b × s(p, Y)).

*b* is estimated from Texas's offices together with the 50-state pool in `data/pool/` (U.S. Senate races in all 50
states, governor races in every state that elected one, and every statewide office in seven other states); those rows
enter only *b*, never a Texas office's *a*. Estimated this way, *b* (in points of the presidential vote) is −11.0 for
2026. With one year left out it is −10.4 (1994), −10.8 (1998), −12.8 (2002), −9.2 (2006), −10.5 (2010), −11.3 (2014),
−11.1 (2018) and −11.5 (2022). In words: in a given office, the party holding the White House kept about 11 fewer points
of its presidential vote at the midterm than the same party did in midterms when it was out of power. Estimated from
Texas's offices alone (the first version of these figures; delete `data/pool/` to reproduce it), *b* was −7.5 for 2026.

The shadow bars in the left panel of figure 2 are 100 × (E_inc / P − 1).

## 6. The 15-race grids (right panels)

The races are the 15 statewide races on the 2026 general election ballot, with their SOS names:

1. U.S. Senator
2. Governor
3. Lieutenant Governor
4. Attorney General
5. Comptroller of Public Accounts
6. Commissioner of the General Land Office
7. Commissioner of Agriculture
8. Railroad Commissioner
9. Chief Justice, Supreme Court
10. Justice, Supreme Court, Place 2 (unexpired term)
11. Justice, Supreme Court, Place 7
12. Justice, Supreme Court, Place 8
13. Judge, Court of Criminal Appeals, Place 3
14. Judge, Court of Criminal Appeals, Place 4
15. Judge, Court of Criminal Appeals, Place 9

- **Actual bars** (`data/derived/texas_statewide_2018_2022_2026.csv`):
  - 2026 uses the race itself.
  - 2018 and 2022 use the same office. For court seats, which have six-year staggered terms, they use the average of
    that court's races that year with both nominees; the `basis` column names the seats averaged.
  - The Railroad Commission's seats rotate, so each year is a different seat.
- **Shadow bars:** the expected vote for the office from section 4 (figure 1) or section 5 (figure 2). Court seats use
  the court-wide expectation.
- **Labels:** the actual vote in millions (two decimals) and actual minus expected, rounded to 0.01M.

## 7. The 2018 page

The 1992–2016 Race Summary Reports are HTML tables, which `src/parse_elchist.py` reads row by row. The 2018 report
(`elchist331_state.htm`) is laid out as preformatted text, so `src/parse_2018.py` reads it from the text: races are
separated by dashed lines, and candidate lines are name, party, votes and percent.

The first race name on the 2018 page arrives with the report header in front of it, so everything up to "PERCENT" is
stripped. `parse_elchist.py` also reads the 2018 page, but the analysis uses `parse_2018.py`'s output for 2018.

## 8. Combining the figures

`src/splice.py` puts each history figure (left) beside the matching 15-race grid (right). The left figure is drawn
again at a resolution chosen to make its pixel height equal the grid's:

  dpi = 170 × grid height ÷ (left figure height at 170 dpi)

The two are then placed side by side with a 120-pixel gap on the chart background color `#fcfcfb`.

## 9. Checks run before publishing

- **Rebuild.** Rebuilding from `data/raw/` gives files byte-identical to the committed intermediate and derived data:
  `src/verify.py`, run by `build.sh`.
- **Re-download** (`src/fetch_sources.py`, run 2026-11-07):
  - The 2020–2024 JSON and the 2026 file were byte-identical to the committed copies; the 2026 count was still the
    Nov. 4, 10:48 pm update.
  - The 1992–2018 pages differ in bytes on every download because Cloudflare rewrites an e-mail link and adds a script
    tag, but they parse to identical results.
- **Spot checks against the raw files:**
  - 2024 President: Trump 6,393,597, Harris 4,835,250.
  - 2020 President: Trump 5,890,347, Biden 5,259,126.
  - 2026 U.S. Senate: Paxton 4,249,373, Talarico 5,444,982.
  - 1992 President: Perot 1,354,781.
