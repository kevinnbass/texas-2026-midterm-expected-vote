"""Build the standalone web page for the two figures (site/template.html -> <out_dir>/index.html and artifact.html).

Every number on the page is computed here from the derived CSVs, using the same rounding as the figure labels, so the
page cannot disagree with the figures. The figures are copied next to the page (figures/, figures/panels/).

Usage: python3 build_page.py <expected_csv> <races_csv> <figures_dir> <out_dir>
"""
import csv
import html
import importlib.util
import math
import os
import re
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("expected_figs", os.path.join(HERE, "expected_figs.py"))
figs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figs)

MINUS = "−"


def sgn(x, nd=2):
    return f"{x:+.{nd}f}".replace("-", MINUS)


def mdiff(act, exp):
    """actual minus expected in millions, rounded as in the figure labels (no -0.00)"""
    return round(act / 1e6 - exp / 1e6, 2) + 0.0


def nice(name):
    n = re.sub(r"\s*\(I\)", "", name or "").strip()
    return n.title() if n.isupper() else n


def main():
    expected_csv, races_csv, fig_dir, out = sys.argv[1:5]
    E = list(csv.DictReader(open(expected_csv)))
    races = list(csv.DictReader(open(races_csv)))
    ex = {(r["office"], int(r["year"])): r for r in E}
    V = {}

    # 2026 as-of text, from the races file ("unofficial, updated Nov. 4, 2026, 10:48 pm")
    basis26 = next(r["basis"] for r in races if r["year"] == "2026")
    V["asof_long"] = basis26.split("updated ", 1)[1] + " Central"
    V["asof_short"] = "unofficial results"

    # per-race differences, rounded as in the figure
    def rows_for(year, inc):
        pre = "expected_inc_" if inc else "expected_"
        out_rows = []
        for r in races:
            if int(r["year"]) != year:
                continue
            e = ex[(figs.office_of(r["race_2026"]), year)]
            ra, da, re_, de = int(r["rep_votes"]), int(r["dem_votes"]), float(e[pre + "rep"]), float(e[pre + "dem"])
            out_rows.append(dict(race=r["race_2026"], basis=r["basis"], rn=r["rep_nominee"], dn=r["dem_nominee"],
                                 ra=ra, da=da, re=re_, de=de, rd=mdiff(ra, re_), dd=mdiff(da, de)))
        return out_rows

    p26, i26 = rows_for(2026, False), rows_for(2026, True)
    V["n26"] = str(len(p26))
    dd = [x["dd"] for x in p26]
    rd = [x["rd"] for x in p26]
    V["d_lo"], V["d_hi"] = f"{min(dd):.2f}", f"{max(dd):.2f}"
    rlo = min(p26, key=lambda x: x["rd"])
    V["r_lo_abs"], V["r_hi"] = f"{abs(rlo['rd']):.2f}", f"{max(rd):.2f}"
    V["r_lo_race"] = "the " + rlo["race"] + " race" if rlo["race"].startswith("U.S.") else rlo["race"]
    V["d_range_pm"] = f"{sgn(min(dd))} to {sgn(max(dd))}"
    V["r_range_pm"] = f"{sgn(min(rd))} to {sgn(max(rd))}"
    assert min(dd) > 0, "dek says Democrats were above expected in every race"
    above, below, even = sum(x > 0 for x in rd), sum(x < 0 for x in rd), sum(x == 0 for x in rd)
    V["r_above"], V["r_below"] = str(above), str(below)
    V["r_even"] = f", within 5,000 votes in {even}" if even else ""
    di, ri = [x["dd"] for x in i26], [x["rd"] for x in i26]
    V["di_range_pm"], V["ri_range_pm"] = f"{sgn(min(di))} to {sgn(max(di))}", f"{sgn(min(ri))} to {sgn(max(ri))}"
    V["di_lo"], V["di_hi"] = f"{min(di):.2f}", f"{max(di):.2f}"
    V["ri_lo_abs"], V["ri_hi"] = f"{abs(min(ri)):.2f}", f"{max(ri):.2f}"
    assert min(ri) < 0 < max(ri), "Figure 2 text says Republicans ranged from below to above"

    # midterm vote vs the party's presidential vote two years earlier
    e26 = [r for r in E if r["year"] == "2026"]
    hist = [r for r in E if int(r["year"]) <= 2022]
    V["n_off26"], V["n_hist"] = str(len(e26)), str(len(hist))
    V["d_above_pres"] = str(sum(float(r["ratio_dem"]) > 1 for r in e26))
    V["r_above_pres"] = str(sum(float(r["ratio_rep"]) > 1 for r in e26))
    V["d_above_hist"] = str(sum(float(r["ratio_dem"]) > 1 for r in hist))
    V["r_above_hist"] = str(sum(float(r["ratio_rep"]) > 1 for r in hist))
    avgs = []
    for key in {r["office"] for r in hist}:
        h = [r for r in hist if r["office"] == key]
        for p in ("rep", "dem"):
            avgs.append(100 * (1 - sum(float(r[f"ratio_{p}"]) for r in h) / len(h)))
    assert min(avgs) > 0, "text says the averages are below the presidential vote"
    V["hist_avg_lo"], V["hist_avg_hi"] = f"{min(avgs):.0f}", f"{max(avgs):.0f}"
    r26 = [100 * (1 - float(r["ratio_rep"])) for r in e26]
    d26 = [100 * (float(r["ratio_dem"]) - 1) for r in e26]
    assert min(r26) > 0 and min(d26) > 0, "text says R below and D above their 2024 presidential totals"
    V["r26_lo"], V["r26_hi"] = f"{min(r26):.0f}", f"{max(r26):.0f}"
    V["d26_lo"], V["d26_hi"] = f"{min(d26):.0f}", f"{max(d26):.0f}"
    V["trump24"], V["harris24"] = f"{int(e26[0]['pres_rep']):,}", f"{int(e26[0]['pres_dem']):,}"

    # president's-party slope
    bs = {int(r["year"]): 100 * float(r["inc_b"]) for r in E}
    V["b26"] = f"{bs[2026]:.1f}".replace("-", MINUS)
    V["b26_abs"] = f"{abs(bs[2026]):.1f}"
    lo_mag, hi_mag = max(bs.values()), min(bs.values())  # least and most negative
    V["b_lo"], V["b_hi"] = f"{lo_mag:.1f}".replace("-", MINUS), f"{hi_mag:.1f}".replace("-", MINUS)

    # figures: copy next to the page, with sizes and alt text
    os.makedirs(os.path.join(out, "figures", "panels"), exist_ok=True)

    def fig(rel):
        shutil.copy2(os.path.join(fig_dir, rel), os.path.join(out, "figures", rel))
        w, h = Image.open(os.path.join(fig_dir, rel)).size
        return "figures/" + rel, w, h

    summary = (f"In 2026 Democratic nominees are {V['d_lo']} to {V['d_hi']} million votes above expected; Republican "
               f"nominees range from {V['r_lo_abs']} million below to {V['r_hi']} million above.")
    alt1 = ("Two-part chart. Left: for ten Texas statewide offices, each party's midterm vote as a percent change from its "
            "presidential vote two years earlier, 1994 to 2026, with 1994 to 2022 averages. Right: actual and expected "
            "Republican and Democratic votes in 2018, 2022 and 2026 for the 15 races on the 2026 ballot. " + summary)
    alt2 = ("Two-part chart, with the expectation adjusted for the president's party. Left: actual and expected percent "
            "change from the presidential vote two years earlier, 1994 to 2026. Right: actual and adjusted expected votes "
            f"for the 15 races. In 2026 Democratic nominees are {V['di_lo']} to {V['di_hi']} million votes above "
            f"expected; Republican nominees range from {V['ri_lo_abs']} million below to {V['ri_hi']} million above.")
    views = {
        1: [("Whole figure", "texas_history_and_expected.png", alt1, "Figure 1"),
            ("Left: 1994–2026", "panels/texas_midterm_vs_presidential_history.png",
             "For ten Texas statewide offices, each party's midterm vote as a percent change from its presidential vote "
             "two years earlier, 1994 to 2026, with 1994 to 2022 averages.", "Figure 1, left: 1994–2026"),
            ("Right: 15 races", "panels/texas_statewide_expected_2018_2026.png",
             "Actual and expected Republican and Democratic votes in 2018, 2022 and 2026 for the 15 races on the 2026 "
             "ballot. " + summary, "Figure 1, right: actual vs. expected votes")],
        2: [("Whole figure", "texas_incumbency_history_and_expected.png", alt2, "Figure 2"),
            ("Left: 1994–2026", "panels/texas_midterm_vs_presidential_history_incumbency.png",
             "Actual and expected percent change from the presidential vote two years earlier, 1994 to 2026, with the "
             "expectation adjusted for the president's party.", "Figure 2, left: 1994–2026"),
            ("Right: 15 races", "panels/texas_statewide_expected_incumbency_2018_2026.png",
             "Actual and expected votes for the 15 races, expectation adjusted for the president's party.",
             "Figure 2, right: actual vs. adjusted expected votes")],
    }
    for k, vs in views.items():
        tabs = []
        for i, (label, rel, alt, cap) in enumerate(vs):
            src, w, h = fig(rel)
            if i == 0:
                V[f"fig{k}_src"], V[f"fig{k}_w"], V[f"fig{k}_h"] = src, str(w), str(h)
                V[f"fig{k}_alt"] = html.escape(alt, quote=True)
            tabs.append(f'<button type="button" role="tab" aria-selected="{"true" if i == 0 else "false"}" '
                        f'tabindex="{0 if i == 0 else -1}" data-src="{src}" data-w="{w}" data-h="{h}" '
                        f'data-alt="{html.escape(alt, quote=True)}" data-cap="{html.escape(cap, quote=True)}">'
                        f'{html.escape(label)}</button>')
        V[f"fig{k}_tabs"] = "".join(tabs)

    # tables: one per year x expectation; bars on one scale across all of them
    all_rows = {(y, inc): rows_for(y, inc) for y in (2026, 2022, 2018) for inc in (False, True)}
    scale = math.ceil(max(max(abs(x["rd"]), abs(x["dd"])) for rs in all_rows.values() for x in rs) * 10) / 10

    def bar(d, cls, title):
        w = 50 * abs(d) / scale
        pos = f"left:50%;width:{w:.2f}%" if d >= 0 else f"right:50%;width:{w:.2f}%"
        return (f'<div class="dcell" title="{html.escape(title, quote=True)}"><div class="dbar"><span class="ax"></span>'
                f'<span class="b {cls}" style="{pos}"></span></div><span class="dv">{sgn(d)}</span></div>')

    out_tables = []
    for (y, inc), rs in all_rows.items():
        cap = f"{y}{' (unofficial)' if y == 2026 else ''}, " + ("expectation adjusted for the president's party" if inc
                                                                 else "plain expectation")
        body = []
        for x in rs:
            if x["rn"]:
                who = f"{html.escape(nice(x['rn']))} (R) · {html.escape(nice(x['dn']))} (D)"
            else:
                n = x["basis"].count(",") + 1
                court = "Supreme Court" if x["race"].startswith("Supreme") else "Court of Criminal Appeals"
                who = f"Average of {n} {court} races ({html.escape(x['basis'].replace('average of ', ''))})"
            t_r = f"Republican, {x['race']}, {y}: {x['ra']:,} actual vs. {x['re']:,.0f} expected"
            t_d = f"Democrat, {x['race']}, {y}: {x['da']:,} actual vs. {x['de']:,.0f} expected"
            body.append(f'<tr><td class="race"><span class="rn">{html.escape(x["race"])}</span><span class="who">{who}</span></td>'
                        f'<td class="v">{x["ra"] / 1e6:.2f}</td><td class="v e">{x["re"] / 1e6:.2f}</td>'
                        f'<td class="diff">{bar(x["rd"], "r", t_r)}</td>'
                        f'<td class="v sep">{x["da"] / 1e6:.2f}</td><td class="v e">{x["de"] / 1e6:.2f}</td>'
                        f'<td class="diff">{bar(x["dd"], "d", t_d)}</td></tr>')
        out_tables.append(
            f'<table data-year="{y}" data-exp="{"inc" if inc else "plain"}"{"" if (y, inc) == (2026, False) else " hidden"}>'
            f'<caption class="sr">Actual vs. expected votes, millions: {cap}</caption>'
            '<thead><tr class="grp"><th></th><th colspan="3"><span class="sw r"></span>Republican</th>'
            '<th colspan="3" class="sep"><span class="sw d"></span>Democrat</th></tr>'
            '<tr><th class="race">Race</th><th>Actual</th><th>Expected</th><th>Actual − expected</th>'
            '<th class="sep">Actual</th><th>Expected</th><th>Actual − expected</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')
    V["tables"] = "\n".join(out_tables)
    V["year_btns"] = "".join(f'<button type="button" data-v="{y}" aria-pressed="{"true" if y == 2026 else "false"}">'
                             f'{y}</button>' for y in (2026, 2022, 2018))
    V["table_note"] = (f"Millions of votes. 2026 counts are unofficial. Bars run from −{scale:.1f} to +{scale:.1f} million. "
                       "Court rows for 2018 and 2022 average that year's races for the same court; court seats use the "
                       "court-wide expected vote. No U.S. Senate race in 2022. Hover over a bar for exact votes.")

    tpl = open(os.path.join(ROOT, "site", "template.html"), encoding="utf-8").read()
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: V[m.group(1)], tpl)
    assert "{{" not in page
    # artifact.html: the page body as claude.ai artifacts take it (the host adds doctype, head and body).
    open(os.path.join(out, "artifact.html"), "w", encoding="utf-8").write(page)
    # index.html: the same page as a self-contained document, for opening locally or any other host.
    head, body = page.split("<!-- page -->", 1)
    doc = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           + head.strip() + "\n</head>\n<body>" + body.rstrip() + "\n</body>\n</html>\n")
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(doc)
    print(os.path.join(out, "index.html"), f"{len(doc):,} bytes; artifact.html {len(page):,} bytes;", "values:",
          {k: v for k, v in V.items() if len(v) < 40})


if __name__ == "__main__":
    main()
