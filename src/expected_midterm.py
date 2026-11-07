"""Texas statewide midterm votes vs. each party's presidential vote two years earlier, 1994-2026.

For every 2026 statewide office: ratio = party's midterm vote for that office / party's Texas presidential vote two
years earlier. Expected midterm vote = presidential vote x the office's average ratio over the 1994-2022 midterms
(for 2018 and 2022, the average leaves out that year's own ratio). Court offices use, each year, the average of that
court's races with both a Republican and a Democratic nominee; Railroad Commissioner averages that year's RRC races.

Inputs (Texas SOS): elchist pages 1992-2016 parsed to elchist_parsed.json; tx2018_races.json; 2020/2024 Federal.json
and 2022 StateWide/Federal.json from results.texas-election.com; 2026 unofficial StateWide/Federal (Civix ENR).
Usage: python3 expected_midterm.py <intermediate_dir> <results_2020_2024_dir> <out_dir>
  intermediate_dir: elchist_parsed.json, tx2018_races.json, tx2026_StateWide.json, tx2026_Federal.json
  results_2020_2024_dir: 44144_262_Federal.json, 47009_242_StateWide.json, 47009_242_Federal.json, 49664_1012_Federal.json
"""
import csv
import json
import re
import sys
from pathlib import Path

INTER = RTE = None  # set in main() from the command line
MIDTERMS = [1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]
OFFICES = [  # (key, title, matcher on normalized race name)
    ("us_senate", "U.S. Senate", lambda n: n in ("USSENATOR",)),
    ("governor", "Governor", lambda n: n == "GOVERNOR"),
    ("lieutenant_governor", "Lieutenant Governor", lambda n: n == "LIEUTENANTGOVERNOR"),
    ("attorney_general", "Attorney General", lambda n: n == "ATTORNEYGENERAL"),
    ("comptroller", "Comptroller", lambda n: n == "COMPTROLLEROFPUBLICACCOUNTS"),
    ("land_commissioner", "Land Commissioner", lambda n: n == "COMMISSIONEROFTHEGENERALLANDOFFICE"),
    ("agriculture_commissioner", "Agriculture Commissioner", lambda n: n == "COMMISSIONEROFAGRICULTURE"),
    ("railroad_commissioner", "Railroad Commissioner", lambda n: n.startswith("RAILROADCOMMISSIONER")),
    ("supreme_court", "Supreme Court (all seats)", lambda n: "SUPREMECOURT" in n),
    ("cca", "Court of Criminal Appeals (all seats)", lambda n: "COURTOFCRIMINALAPPEALS" in n),
]


def norm(s):
    return re.sub(r"[^A-Z]", "", s.upper().replace("U. S.", "US"))


def load():
    """{year: {race_name: [(name, party, votes)]}} for 1992-2026."""
    Y = {int(k): v for k, v in json.load(open(INTER / "elchist_parsed.json")).items() if v}
    y18 = json.load(open(INTER / "tx2018_races.json"))
    Y[2018] = {re.sub(r"^.*PERCENT\s+", "", k): v for k, v in y18.items()}

    def enr(files):
        out = {}
        for f in files:
            for r in json.load(open(f))["Races"]:
                out[r["N"].strip()] = [(c["N"], c["P"], c["V"]) for c in r["Candidates"]]
        return out
    Y[2020] = enr([RTE / "44144_262_Federal.json"])
    Y[2022] = enr([RTE / "47009_242_StateWide.json", RTE / "47009_242_Federal.json"])
    Y[2024] = enr([RTE / "49664_1012_Federal.json"])
    Y[2026] = enr([INTER / "tx2026_StateWide.json", INTER / "tx2026_Federal.json"])
    return Y


def rd(cands):
    r = [c for c in cands if c[1] == "REP"]
    d = [c for c in cands if c[1] == "DEM"]
    return (r[0][2], d[0][2]) if len(r) == 1 and len(d) == 1 else None


def pres(Y, y):
    for n, c in Y[y].items():
        if "PRESIDENT" in norm(n):
            return rd(c)
    raise KeyError(y)


def office_vote(Y, y, match):
    xs = [rd(c) for n, c in Y[y].items() if match(norm(n)) and "DISTRICT" not in n.upper()]
    xs = [x for x in xs if x]
    if not xs:
        return None
    return sum(x[0] for x in xs) / len(xs), sum(x[1] for x in xs) / len(xs), len(xs)


def build():
    Y = load()
    rows = []
    for key, title, match in OFFICES:
        for y in MIDTERMS:
            ov = office_vote(Y, y, match)
            if not ov:
                continue
            pr, pd = pres(Y, y - 2)
            rows.append({"office": key, "title": title, "year": y, "rep": ov[0], "dem": ov[1], "n_races": ov[2],
                         "pres_rep": pr, "pres_dem": pd, "ratio_rep": ov[0] / pr, "ratio_dem": ov[1] / pd})
    for key, title, _ in OFFICES:
        hist = [r for r in rows if r["office"] == key and r["year"] <= 2022]
        for r in (x for x in rows if x["office"] == key):
            base = [h for h in hist if h["year"] != r["year"]]  # leave own year out
            for p in ("rep", "dem"):
                avg = sum(h[f"ratio_{p}"] for h in base) / len(base)
                r[f"avg_ratio_{p}"] = avg
                r[f"expected_{p}"] = r[f"pres_{p}"] * avg
                r[f"dev_{p}"] = r[p] - r[f"expected_{p}"]
            r["n_hist"] = len(base)
    add_incumbency(rows)
    return rows


# party holding the White House at each midterm
PRES_PARTY = {1994: "D", 1998: "D", 2002: "R", 2006: "R", 2010: "D", 2014: "D", 2018: "R", 2022: "D", 2026: "R"}


def add_incumbency(rows):
    """Incumbency-adjusted expectation: ratio = a[office, party] + b * (party holds the White House).
    b is the pooled within-(office, party) slope; a is the office-party mean of (ratio - b * status). Both are
    estimated from the 1994-2022 midterms, leaving out the target year (2018, 2022) as for the plain expectation."""
    for target in sorted({r["year"] for r in rows}):
        hist = [r for r in rows if r["year"] <= 2022 and r["year"] != target]
        groups = {}
        for r in hist:
            for p, P in (("rep", "R"), ("dem", "D")):
                groups.setdefault((r["office"], p), []).append((1 if PRES_PARTY[r["year"]] == P else 0, r[f"ratio_{p}"]))
        num = den = 0.0
        for xs in groups.values():
            mx = sum(x for x, _ in xs) / len(xs)
            my = sum(v for _, v in xs) / len(xs)
            num += sum((x - mx) * (v - my) for x, v in xs)
            den += sum((x - mx) ** 2 for x, _ in xs)
        b = num / den
        for r in (x for x in rows if x["year"] == target):
            for p, P in (("rep", "R"), ("dem", "D")):
                xs = groups[(r["office"], p)]
                a = sum(v - b * x for x, v in xs) / len(xs)
                s = 1 if PRES_PARTY[target] == P else 0
                r[f"inc_b"] = b
                r[f"expected_inc_{p}"] = r[f"pres_{p}"] * (a + b * s)
                r[f"dev_inc_{p}"] = r[p] - r[f"expected_inc_{p}"]


def main():
    global INTER, RTE
    INTER, RTE, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    rows = build()
    cols = ["office", "title", "year", "n_races", "pres_rep", "pres_dem", "rep", "dem", "ratio_rep", "ratio_dem",
            "n_hist", "avg_ratio_rep", "avg_ratio_dem", "expected_rep", "expected_dem", "dev_rep", "dev_dem",
            "inc_b", "expected_inc_rep", "expected_inc_dem", "dev_inc_rep", "dev_inc_dem"]
    with open(out / "texas_midterm_vs_presidential.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) and ("ratio" in k or k == "inc_b") else
                            round(v) if isinstance(v, float) else v) for k, v in r.items() if k in cols})
    for r in rows:
        print(f"{r['office']:24} {r['year']} n={r['n_races']}  R {r['rep']:>10,.0f} ({100 * (r['ratio_rep'] - 1):+5.1f}% vs pres; "
              f"exp {r['expected_rep']:>10,.0f}, dev {r['dev_rep']:>+10,.0f})   D {r['dem']:>10,.0f} "
              f"({100 * (r['ratio_dem'] - 1):+5.1f}%; exp {r['expected_dem']:>10,.0f}, dev {r['dev_dem']:>+10,.0f})")


if __name__ == "__main__":
    main()
