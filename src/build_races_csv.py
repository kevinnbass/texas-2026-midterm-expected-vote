"""Actual Republican and Democratic votes in 2018, 2022 and 2026 for each of the 15 statewide offices on the 2026
Texas ballot (the bars in the right-hand panels).

For court seats (six-year staggered terms, so the same seat was not on the 2018 or 2022 ballot), the 2018 and 2022
values are the average of that court's races that year with exactly one Republican and one Democratic nominee.
Railroad Commissioner: the commission's seats rotate, so each year is a different seat.

Usage: python3 build_races_csv.py <intermediate_dir> <results_2020_2024_dir> <out_csv> --asof "<2026 update text>"
  intermediate_dir: tx2018_races.json, tx2026_StateWide.json, tx2026_Federal.json
  results_2020_2024_dir: 47009_242_StateWide.json, 47009_242_Federal.json (2022 general, final)
"""
import argparse
import csv
import json
import os
import re
from pathlib import Path

# 2026 race name (SOS) -> (short title, file slug, office key in 2018/2022 or court key)
RACES_2026 = [
    ("U. S. SENATOR", "U.S. Senate", "us_senate", "U. S. Senator"),
    ("GOVERNOR", "Governor", "governor", "Governor"),
    ("LIEUTENANT GOVERNOR", "Lieutenant Governor", "lieutenant_governor", "Lieutenant Governor"),
    ("ATTORNEY GENERAL", "Attorney General", "attorney_general", "Attorney General"),
    ("COMPTROLLER OF PUBLIC ACCOUNTS", "Comptroller", "comptroller", "Comptroller of Public Accounts"),
    ("COMMISSIONER OF THE GENERAL LAND OFFICE", "Land Commissioner", "land_commissioner",
     "Commissioner of the General Land Office"),
    ("COMMISSIONER OF AGRICULTURE", "Agriculture Commissioner", "agriculture_commissioner",
     "Commissioner of Agriculture"),
    ("RAILROAD COMMISSIONER", "Railroad Commissioner", "railroad_commissioner", "Railroad Commissioner"),
    ("CHIEF JUSTICE, SUPREME COURT", "Supreme Court Chief Justice", "supreme_court_chief_justice", "SC"),
    ("JUSTICE, SUPREME COURT, PLACE 2 - UNEXPIRED TERM", "Supreme Court, Place 2 (unexpired term)",
     "supreme_court_place_2", "SC"),
    ("JUSTICE, SUPREME COURT, PLACE 7", "Supreme Court, Place 7", "supreme_court_place_7", "SC"),
    ("JUSTICE, SUPREME COURT, PLACE 8", "Supreme Court, Place 8", "supreme_court_place_8", "SC"),
    ("JUDGE, COURT OF CRIMINAL APPEALS, PLACE 3", "Court of Criminal Appeals, Place 3", "cca_place_3", "CCA"),
    ("JUDGE, COURT OF CRIMINAL APPEALS, PLACE 4", "Court of Criminal Appeals, Place 4", "cca_place_4", "CCA"),
    ("JUDGE, COURT OF CRIMINAL APPEALS, PLACE 9", "Court of Criminal Appeals, Place 9", "cca_place_9", "CCA"),
]
COURT_NAME = {"SC": "Supreme Court", "CCA": "Court of Criminal Appeals"}


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def rd(cands):
    """(rep_name, rep_votes, dem_name, dem_votes) from [(name, party, votes)]; None unless exactly one of each."""
    r = [c for c in cands if c[1] == "REP"]
    d = [c for c in cands if c[1] == "DEM"]
    if len(r) != 1 or len(d) != 1:
        return None
    return r[0][0], r[0][2], d[0][0], d[0][2]


def load(inter, rte):
    y18 = json.load(open(inter / "tx2018_races.json"))
    # the first block of the SOS page carries the report header before the first race name
    y18 = {re.sub(r"^.*PERCENT\s+", "", k): [tuple(c) for c in v] for k, v in y18.items()}
    y22 = {}
    for f in (rte / "47009_242_StateWide.json", rte / "47009_242_Federal.json"):
        for r in json.load(open(f))["Races"]:
            y22[r["N"].strip()] = [(c["N"], c["P"], c["V"]) for c in r["Candidates"]]
    y26 = {}
    for f in (inter / "tx2026_StateWide.json", inter / "tx2026_Federal.json"):
        for r in json.load(open(f))["Races"]:
            y26[r["N"].strip()] = [(c["N"], c["P"], c["V"]) for c in r["Candidates"]]
    return y18, y22, y26


def court_avg(year_races, court):
    pat = r"SUPREMECOURT" if court == "SC" else r"COURTOFCRIMINALAPPEALS"
    picked = []
    for name, cands in year_races.items():
        if re.search(pat, norm(name)) and "DISTRICT" not in name.upper():
            x = rd(cands)
            if x:
                picked.append((name, x))
    if not picked:
        return None
    rv = sum(p[1][1] for p in picked) / len(picked)
    dv = sum(p[1][3] for p in picked) / len(picked)
    return rv, dv, [p[0] for p in picked]


def find(year_races, key):
    for name, cands in year_races.items():
        if norm(name) == norm(key):
            return rd(cands)
    return None


def main():
    a = argparse.ArgumentParser()
    a.add_argument("intermediate_dir")
    a.add_argument("results_2020_2024_dir")
    a.add_argument("out_csv")
    a.add_argument("--asof", required=True)
    o = a.parse_args()
    y18, y22, y26 = load(Path(o.intermediate_dir), Path(o.results_2020_2024_dir))
    rows = []
    for n26, short, slug, key in RACES_2026:
        r26 = find(y26, n26)
        assert r26, n26
        for year, yr in ((2018, y18), (2022, y22)):
            if key in COURT_NAME:
                ca = court_avg(yr, key)
                if ca:
                    places = ", ".join(re.sub(r".*?(PLACE \d+|PRESIDING JUDGE|CHIEF JUSTICE).*", r"\1", p.upper())
                                       .title() for p in ca[2])
                    rows.append([short, year, "", round(ca[0]), "", round(ca[1]), f"average of {places}"])
            else:
                x = find(yr, key)
                if x:
                    rows.append([short, year, x[0], x[1], x[2], x[3], "official canvass"])
        rows.append([short, 2026, r26[0], r26[1], r26[2], r26[3], f"unofficial, {o.asof}"])
    os.makedirs(os.path.dirname(o.out_csv) or ".", exist_ok=True)
    with open(o.out_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["race_2026", "year", "rep_nominee", "rep_votes", "dem_nominee", "dem_votes", "basis"])
        w.writerows(rows)
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
