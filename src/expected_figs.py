"""Figures for the Texas midterm-vs-presidential analysis.

A) texas_midterm_vs_presidential_history.png: for each statewide office, each party's midterm vote as % change from
   its Texas presidential vote two years earlier, 1994-2026, with the 1994-2022 average.
B) texas_statewide_expected_2018_2026.png: the 15-race grid of actual R/D votes in 2018, 2022, 2026 with a shadow
   bar for the vote expected from the presidential vote two years earlier x the office's average midterm ratio.

C) texas_midterm_vs_presidential_history_incumbency.png and texas_statewide_expected_incumbency_2018_2026.png: the
   same two figures with the expectation adjusted for the president's party (expected_inc_* in the CSV).

Usage: python3 expected_figs.py <expected_csv> <races_csv> <out_dir> --asof "<2026 update text>"
Fonts: Inter if installed (the published figures used Inter), else Noto Sans, else DejaVu Sans.
"""
import argparse
import csv
import textwrap
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#7a7974", "#e4e3df"
REP, DEM = "#e34948", "#2a78d6"
REP_L, DEM_L = "#f6c3c2", "#b7d3f6"
RACE_TO_OFFICE = {"U.S. Senate": "us_senate", "Governor": "governor", "Lieutenant Governor": "lieutenant_governor",
                  "Attorney General": "attorney_general", "Comptroller": "comptroller",
                  "Land Commissioner": "land_commissioner", "Agriculture Commissioner": "agriculture_commissioner",
                  "Railroad Commissioner": "railroad_commissioner"}


def office_of(race):
    if race in RACE_TO_OFFICE:
        return RACE_TO_OFFICE[race]
    return "supreme_court" if race.startswith("Supreme Court") else "cca"


def font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    return next((n for n in ("Inter", "Noto Sans", "DejaVu Sans") if n in names), "sans-serif")


def column(ax, fig, x, bottom, top, w, color, radius_px=3, **kw):
    """Column between bottom and top (data units); rounded at the end away from zero, square at the baseline."""
    if top == bottom:
        return
    fig.canvas.draw()
    (x0, y0), (x1, y1) = ax.transData.transform((0, 0)), ax.transData.transform((1, 1))
    ux, uy = 1 / abs(x1 - x0), 1 / abs(y1 - y0)
    lo, hi = min(bottom, top), max(bottom, top)
    ax.add_patch(FancyBboxPatch((x - w / 2, lo), w, hi - lo, boxstyle=f"round,pad=0,rounding_size={radius_px * ux}",
                                mutation_aspect=uy / ux, facecolor=color, edgecolor="none", **kw))
    sq = min(hi - lo, radius_px * 1.5 * uy)
    yb = lo if top >= bottom else hi - sq
    ax.add_patch(Rectangle((x - w / 2, yb), w, sq, facecolor=color, edgecolor="none", **kw))


def fig_history(E, out_png, dpi=170):
    offices = []
    for r in E:
        if r["office"] not in [o[0] for o in offices]:
            offices.append((r["office"], r["title"]))
    by = defaultdict(dict)
    for r in E:
        by[r["office"]][int(r["year"])] = r
    years = [1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]
    plt.rcParams.update({"font.family": font(), "font.size": 10})
    ncol, nrow = 2, (len(offices) + 1) // 2
    H = 3.3 * nrow + 2.0
    fig = plt.figure(figsize=(17, H), dpi=dpi, facecolor=SURFACE)
    top, bottom = 1 - 1.35 / H, 0.95 / H
    cell = (top - bottom) / nrow
    for k, (key, title) in enumerate(offices):
        r_, c_ = divmod(k, ncol)
        ax = fig.add_axes([0.05 + c_ * 0.48, top - (r_ + 1) * cell + cell * 0.2, 0.40, cell * 0.66], facecolor=SURFACE)
        ax.set_xlim(-0.6, len(years) - 0.4)
        ax.set_ylim(-72, 22)
        ax.yaxis.grid(True, color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left", "bottom"):
            ax.spines[sp].set_visible(False)
        ax.axhline(0, color="#9a9994", lw=0.9)
        ax.tick_params(axis="both", length=0, colors=INK2, labelsize=8.8)
        ax.set_yticks(range(-60, 21, 20))
        ax.set_yticklabels([(f"+{t}%" if t > 0 else f"{t}%".replace("-", "−")) if t else "0"
                            for t in range(-60, 21, 20)])
        w, gap = 0.34, 0.03
        hist = [by[key][y] for y in years if y in by[key] and y <= 2022]
        avg_r = 100 * (sum(float(h["ratio_rep"]) for h in hist) / len(hist) - 1)
        avg_d = 100 * (sum(float(h["ratio_dem"]) for h in hist) / len(hist) - 1)
        for i, y in enumerate(years):
            if y not in by[key]:
                ax.text(i, 3, "no race", ha="center", va="bottom", fontsize=7.5, color=MUTED)
                continue
            rr = by[key][y]
            for xc, v, col, light in ((i - w / 2 - gap / 2, 100 * (float(rr["ratio_rep"]) - 1), REP, REP_L),
                                      (i + w / 2 + gap / 2, 100 * (float(rr["ratio_dem"]) - 1), DEM, DEM_L)):
                if y == 2026:
                    column(ax, fig, xc, 0, v, w, light)
                    ax.add_patch(Rectangle((xc - w / 2, min(0, v)), w, abs(v), fill=False, edgecolor=col, lw=1.1,
                                           hatch="///"))
                    ax.text(xc, v + (1.5 if v >= 0 else -1.5), f"{v:+.0f}%".replace("-", "−"), ha="center",
                            va="bottom" if v >= 0 else "top", fontsize=8.2, fontweight="semibold", color=INK,
                            zorder=5, bbox=dict(boxstyle="round,pad=0.12", fc=SURFACE, ec="none"))
                else:
                    column(ax, fig, xc, 0, v, w, col)
        ax.axhline(avg_r, color=REP, lw=1.0, ls=(0, (4, 3)))
        ax.axhline(avg_d, color=DEM, lw=1.0, ls=(0, (4, 3)))
        ax.text(len(years) - 0.35, avg_r, f"R avg {avg_r:.0f}%".replace("-", "−"), fontsize=8.2, color=INK2,
                va="bottom" if avg_r > avg_d else "top", ha="left", clip_on=False)
        ax.text(len(years) - 0.35, avg_d, f"D avg {avg_d:.0f}%".replace("-", "−"), fontsize=8.2, color=INK2,
                va="bottom" if avg_d >= avg_r else "top", ha="left", clip_on=False)
        ax.set_xticks(range(len(years)))
        ax.set_xticklabels([f"{y}*" if y == 2026 else str(y) for y in years], fontsize=8.8, color=INK)
        ax.set_title(title, fontsize=12, fontweight="bold", color=INK, loc="left", pad=6)
    fig.text(0.05, 1 - 0.42 / H, "Texas statewide midterm votes vs. each party's presidential vote two years earlier",
             fontsize=19, fontweight="bold", color=INK)
    fig.text(0.05, 1 - 0.72 / H, "% change in each party's vote for the office from its Texas presidential vote two "
             "years earlier, 1994–2026. Dashed lines: 1994–2022 average. * 2026 unofficial.", fontsize=11.5,
             color=INK2)
    fig.legend(handles=[Rectangle((0, 0), 1, 1, color=REP), Rectangle((0, 0), 1, 1, color=DEM)],
               labels=["Republican", "Democrat"], loc="upper right", bbox_to_anchor=(0.93, 1 - 0.3 / H), ncol=2,
               frameon=False, fontsize=11.5, labelcolor=INK)
    note = ("Source: Texas Secretary of State (official results 1992–2024; 2026 unofficial). Republican and Democratic "
            "nominees only. Court panels average each year's races for that court with both nominees; Railroad "
            "Commissioner averages that year's RRC races. Comptroller 2010 had no Democratic nominee. Presidential "
            "baselines include 1992 (Perot took 22%) and the straight-ticket era (ended 2020).")
    fig.text(0.05, 0.3 / H, textwrap.fill(note, 220), fontsize=8.6, color=MUTED, va="bottom", linespacing=1.45)
    fig.savefig(out_png, dpi=dpi, facecolor=SURFACE)
    plt.close(fig)


PRES_PARTY = {1994: "D", 1998: "D", 2002: "R", 2006: "R", 2010: "D", 2014: "D", 2018: "R", 2022: "D", 2026: "R"}


def fig_history_inc(E, out_png, dpi=170):
    """History figure with a shadow bar per party-year: the incumbency-adjusted expected change, estimated with that
    year left out (expected_inc_* in the CSV)."""
    offices = []
    for r in E:
        if r["office"] not in [o[0] for o in offices]:
            offices.append((r["office"], r["title"]))
    by = defaultdict(dict)
    for r in E:
        by[r["office"]][int(r["year"])] = r
    years = [1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]
    bs = sorted({round(100 * float(r["inc_b"]), 1) for r in E if r.get("inc_b")})
    plt.rcParams.update({"font.family": font(), "font.size": 10})
    ncol, nrow = 2, (len(offices) + 1) // 2
    H = 3.45 * nrow + 2.1
    fig = plt.figure(figsize=(17, H), dpi=dpi, facecolor=SURFACE)
    top, bottom = 1 - 1.45 / H, 1.0 / H
    cell = (top - bottom) / nrow
    pct = lambda x: f"{x:+.0f}%".replace("-", "−")
    for k, (key, title) in enumerate(offices):
        r_, c_ = divmod(k, ncol)
        ax = fig.add_axes([0.05 + c_ * 0.48, top - (r_ + 1) * cell + cell * 0.24, 0.42, cell * 0.62], facecolor=SURFACE)
        ax.set_xlim(-0.6, len(years) - 0.4)
        ax.set_ylim(-72, 26)
        ax.yaxis.grid(True, color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left", "bottom"):
            ax.spines[sp].set_visible(False)
        ax.axhline(0, color="#9a9994", lw=0.9, zorder=4)
        ax.tick_params(axis="both", length=0, colors=INK2, labelsize=8.8)
        ax.set_yticks(range(-60, 21, 20))
        ax.set_yticklabels([(f"+{t}%" if t > 0 else f"{t}%".replace("-", "−")) if t else "0"
                            for t in range(-60, 21, 20)])
        w, gap, off = 0.28, 0.12, 0.09
        lab26 = {}
        for i, y in enumerate(years):
            if y not in by[key]:
                ax.text(i, 3, "no race", ha="center", va="bottom", fontsize=7.5, color=MUTED)
                continue
            rr = by[key][y]
            for xc, p, col, light in ((i - w / 2 - gap / 2, "rep", REP, REP_L), (i + w / 2 + gap / 2, "dem", DEM, DEM_L)):
                v = 100 * (float(rr[f"ratio_{p}"]) - 1)
                e = 100 * (float(rr[f"expected_inc_{p}"]) / float(rr[f"pres_{p}"]) - 1)
                column(ax, fig, xc + off, 0, e, w, light, zorder=1)
                ax.add_patch(Rectangle((xc + off - w / 2, min(0, e)), w, abs(e), fill=False, edgecolor=col, lw=0.8,
                                       ls=(0, (3, 2)), zorder=1.5))
                if y == 2026:
                    column(ax, fig, xc, 0, v, w, light, zorder=2)
                    ax.add_patch(Rectangle((xc - w / 2, min(0, v)), w, abs(v), fill=False, edgecolor=col, lw=1.1,
                                           hatch="///", zorder=2.5))
                    lab26[p] = (v, e)
                else:
                    column(ax, fig, xc, 0, v, w, col, zorder=2)
        ax.set_xticks(range(len(years)))
        ax.set_xticklabels([f"{y}{'*' if y == 2026 else ''}\n{PRES_PARTY[y]}" for y in years], fontsize=8.6, color=INK,
                           linespacing=1.3)
        ax.set_title(title, fontsize=12, fontweight="bold", color=INK, loc="left", pad=6)
        if lab26:
            ax.text(1.0, 1.03, f"2026: R {pct(lab26['rep'][0])} (expected {pct(lab26['rep'][1])})   "
                    f"D {pct(lab26['dem'][0])} (expected {pct(lab26['dem'][1])})", transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=9.2, color=INK, fontweight="semibold")
    fig.text(0.05, 1 - 0.40 / H, "Texas statewide midterm votes vs. each party's presidential vote two years earlier, "
             "adjusted for the president's party", fontsize=17, fontweight="bold", color=INK)
    fig.text(0.05, 1 - 0.64 / H, textwrap.fill("Solid bars: % change in the party's vote for the office from its Texas "
             "presidential vote two years earlier. Shadow bars: the change expected for that office and party given "
             "whether it held the White House, estimated without that year.", 150), fontsize=11, color=INK2,
             va="top", linespacing=1.35)
    fig.text(0.05, 1 - 1.12 / H, "Letter under each year: the president's party at the midterm. * 2026 unofficial.",
             fontsize=10.5, color=MUTED)
    shadow = Rectangle((0, 0), 1, 1, facecolor="#e4e3df", edgecolor="#7a7974", ls=(0, (3, 2)), lw=0.9)
    fig.legend(handles=[Rectangle((0, 0), 1, 1, color=REP), Rectangle((0, 0), 1, 1, color=DEM), shadow],
               labels=["Republican", "Democrat", "Expected (shadow)"], loc="upper right",
               bbox_to_anchor=(0.97, 1 - 0.58 / H), ncol=1, frameon=False, fontsize=11, labelcolor=INK)
    note = ("Expected change = the office's baseline ratio for that party + an adjustment when the party holds the "
            f"White House ({bs[0]:+.1f} to {bs[-1]:+.1f} points of the presidential vote, depending on the year left out), "
            "estimated from the 1994–2022 midterms of U.S. Senate races in all 50 states, governor races in every state that elected one, and every statewide office in Texas and seven other states (each Texas office keeps its own baseline), without the "
            "year shown. Source: Texas Secretary of State (official "
            "results 1992–2024; 2026 unofficial). Republican and Democratic nominees only. Court panels average each "
            "year's races for that court with both nominees; Railroad Commissioner averages that year's RRC races. "
            "Comptroller 2010 had no Democratic nominee. Presidential baselines include 1992 (Perot took 22%) and the "
            "straight-ticket era (ended 2020).")
    fig.text(0.05, 0.25 / H, textwrap.fill(note, 220), fontsize=8.6, color=MUTED, va="bottom", linespacing=1.45)
    fig.savefig(out_png, dpi=dpi, facecolor=SURFACE)
    plt.close(fig)


def fig_expected(E, races, asof, out_png, inc=False):
    pre = "expected_inc_" if inc else "expected_"
    ex = {(r["office"], int(r["year"])): r for r in E}
    order, groups = [], defaultdict(list)
    for r in races:
        if r["race_2026"] not in order:
            order.append(r["race_2026"])
        groups[r["race_2026"]].append(r)
    plt.rcParams.update({"font.family": font(), "font.size": 10})
    ncol, nrow = 3, (len(order) + 2) // 3
    H = 4.3 * nrow + 2.3
    fig = plt.figure(figsize=(18, H), dpi=170, facecolor=SURFACE)
    top, bottom = 1 - 1.35 / H, 0.95 / H
    cell = (top - bottom) / nrow
    for k, race in enumerate(order):
        r_, c_ = divmod(k, ncol)
        ax = fig.add_axes([0.045 + c_ * (0.94 / ncol), top - (r_ + 1) * cell + cell * 0.25, 0.94 / ncol - 0.035,
                           cell * 0.62], facecolor=SURFACE)
        g = sorted(groups[race], key=lambda x: int(x["year"]))
        n = len(g)
        ax.set_xlim(-0.6, n - 0.4)
        ax.set_ylim(0, 6.6)
        ax.yaxis.grid(True, color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color("#9a9994")
        ax.tick_params(axis="both", length=0, colors=INK2, labelsize=9)
        ax.set_yticks(range(0, 7, 2))
        ax.set_yticklabels([f"{t}M" if t else "0" for t in range(0, 7, 2)])
        w, gap, off = 0.30, 0.10, 0.11
        labels = []
        for x, row in enumerate(g):
            y = int(row["year"])
            e = ex[(office_of(race), y)]
            for xc, act, exp, col, light in (
                    (x - w / 2 - gap / 2, float(row["rep_votes"]) / 1e6, float(e[pre + "rep"]) / 1e6, REP, REP_L),
                    (x + w / 2 + gap / 2, float(row["dem_votes"]) / 1e6, float(e[pre + "dem"]) / 1e6, DEM, DEM_L)):
                # shadow: expected vote, offset right and behind the actual bar
                column(ax, fig, xc + off, 0, exp, w, light, zorder=1)
                ax.add_patch(Rectangle((xc + off - w / 2, 0), w, exp, fill=False, edgecolor=col, lw=0.9,
                                       ls=(0, (3, 2)), zorder=1.5))
                column(ax, fig, xc, 0, act, w, col, zorder=2)
                d = round(act - exp, 2) + 0.0  # no "-0.00"
                ax.text(xc + off / 2, max(act, exp) + 0.09, f"{act:.2f}", ha="center", va="bottom", fontsize=8.6,
                        fontweight="semibold", color=INK, zorder=3)
                ax.text(xc + off / 2, max(act, exp) + 0.42, f"{d:+.2f}".replace("-", "−"), ha="center",
                        va="bottom", fontsize=7.8, color=INK2, zorder=3)
            lab = row["label"] if "label" in row else str(y)
            labels.append(lab)
        ax.set_xticks(range(n))
        ax.set_xticklabels(labels, fontsize=8.2, color=INK, linespacing=1.25)
        ax.set_title(race, fontsize=12.5, fontweight="bold", color=INK, pad=8)
    title = "Texas Statewide Races, 2018–2026: Actual vs. Expected Votes"
    if inc:
        title += ", Adjusted for the President's Party"
    fig.text(0.5, 1 - 0.38 / H, title, ha="center", fontsize=22 if not inc else 20, fontweight="bold", color=INK)
    shadow = Rectangle((0, 0), 1, 1, facecolor="#e4e3df", edgecolor="#7a7974", ls=(0, (3, 2)), lw=0.9)
    fig.legend(handles=[Rectangle((0, 0), 1, 1, color=REP), Rectangle((0, 0), 1, 1, color=DEM), shadow],
               labels=["Republican (actual)", "Democrat (actual)", "Expected (shadow, same color, lighter)"],
               loc="center", bbox_to_anchor=(0.5, 1 - 0.82 / H), ncol=3, frameon=False, fontsize=12.5,
               labelcolor=INK, handlelength=1.4, handleheight=0.9, columnspacing=2)
    fig.text(0.5, 1 - 1.1 / H, "Votes in millions. Above each pair: actual votes (bold) and actual minus expected. "
             "* 2026 results are unofficial.", ha="center", fontsize=11, color=INK2)
    note = ("Expected vote = the party's Texas presidential vote two years earlier × the office's average ratio of "
            "midterm vote to prior presidential vote in the 1994–2022 midterms (for 2018 and 2022, the average leaves "
            "out that year). Court offices use the average ratio of each year's races for that court; Railroad "
            "Commissioner uses that year's RRC races. Source: Texas Secretary of State; 2026 unofficial results "
            f"({asof}). Actual bars as in the earlier figure: court bars for 2018 and 2022 average that year's races "
            "for the same court with both nominees; no U.S. Senate race in 2022.")
    if inc:
        bs = {int(r["year"]): float(r["inc_b"]) for r in E if r.get("inc_b")}
        note = ("Expected vote = the party's Texas presidential vote two years earlier × (the office's baseline ratio for "
                "that party + an adjustment when the party holds the White House). The adjustment is the average "
                "difference, within each office and party, between midterms when the party held the presidency and "
                f"when it did not, pooled over the 1994–2022 midterms of U.S. Senate races in all 50 states, governor races in every state that elected one, and every statewide office in Texas and seven other states: {100 * bs[2026]:+.1f} points of the presidential "
                f"vote for 2026 ({100 * bs[2018]:+.1f} for 2018 and {100 * bs[2022]:+.1f} for 2022, which leave out their "
                "own year). President's party: Republicans in 2018 and 2026, Democrats in 2022. " + note[note.find("Court offices"):])
    fig.text(0.5, 0.25 / H, textwrap.fill(note, 230), ha="center", va="bottom", fontsize=9, color=MUTED,
             linespacing=1.45)
    fig.savefig(out_png, dpi=170, facecolor=SURFACE)
    plt.close(fig)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("expected_csv")
    a.add_argument("races_csv")
    a.add_argument("out_dir")
    a.add_argument("--asof", required=True)
    o = a.parse_args()
    E = list(csv.DictReader(open(o.expected_csv)))
    races = list(csv.DictReader(open(o.races_csv)))
    for r in races:  # x labels matching the earlier figure
        y = int(r["year"])
        base = "2026*" if y == 2026 else str(y)
        if r["rep_nominee"]:
            def sur(n):
                import re
                n = re.sub(r"\(I\)", "", n).strip()
                p = [x for x in n.split() if x.upper().rstrip(".,") not in ("JR", "SR", "II", "III", "IV")]
                return p[-1].rstrip(",").title() if p[-1].isupper() else p[-1].rstrip(",")
            rn, dn = sur(r["rep_nominee"]), sur(r["dem_nominee"])
            if rn == dn:
                rn, dn = r["rep_nominee"].replace("(I)", "").strip().title(), r["dem_nominee"].strip().title()
                r["label"] = f"{base}\n{rn} (R)\nvs. {dn} (D)"
            else:
                m = f"{rn} (R) vs. {dn} (D)"
                r["label"] = f"{base}\n" + (m.replace(" vs. ", "\nvs. ") if len(m) > 27 else m)
        else:
            n = r["basis"].count(",") + 1
            r["label"] = f"{base}\navg. of {n} court races"
    out = Path(o.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fig_history(E, out / "texas_midterm_vs_presidential_history.png")
    fig_history_inc(E, out / "texas_midterm_vs_presidential_history_incumbency.png")
    fig_expected(E, races, o.asof, out / "texas_statewide_expected_2018_2026.png")
    fig_expected(E, races, o.asof, out / "texas_statewide_expected_incumbency_2018_2026.png", inc=True)


if __name__ == "__main__":
    main()
