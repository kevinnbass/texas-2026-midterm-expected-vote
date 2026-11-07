"""Make the two published images: history figure on the left, 15-race expected-vote grid on the right.

The left figure is drawn again at a higher resolution so that its height matches the right figure's; the two are set
side by side with a 120-pixel gap on the chart background color.

  texas_history_and_expected.png             = history (plain)        + expected grid (plain)
  texas_incumbency_history_and_expected.png  = history (incumbency)   + expected grid (incumbency)

Usage: python3 splice.py <expected_csv> <panels_dir> <out_dir>
  panels_dir holds the four figures written by expected_figs.py.
"""
import csv
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("expected_figs", os.path.join(HERE, "expected_figs.py"))
figs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figs)

PAIRS = [  # (left drawn by, left panel used for its size, right panel, output)
    (figs.fig_history, "texas_midterm_vs_presidential_history.png", "texas_statewide_expected_2018_2026.png",
     "texas_history_and_expected.png"),
    (figs.fig_history_inc, "texas_midterm_vs_presidential_history_incumbency.png",
     "texas_statewide_expected_incumbency_2018_2026.png", "texas_incumbency_history_and_expected.png"),
]


def main():
    expected_csv, panels, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    E = list(csv.DictReader(open(expected_csv)))
    for draw, left_name, right_name, out_name in PAIRS:
        R = Image.open(os.path.join(panels, right_name)).convert("RGB")
        L0 = Image.open(os.path.join(panels, left_name))
        os.makedirs(os.path.join(out, "_work"), exist_ok=True)
        tall = os.path.join(out, "_work", "tall_" + left_name)  # intermediate, not published
        draw(E, tall, dpi=170 * R.height / L0.height)
        L = Image.open(tall).convert("RGB")
        gut = 120
        W, H = L.width + gut + R.width, max(L.height, R.height)
        img = Image.new("RGB", (W, H), (252, 252, 251))
        img.paste(L, (0, (H - L.height) // 2))
        img.paste(R, (L.width + gut, (H - R.height) // 2))
        img.save(os.path.join(out, out_name), dpi=(170, 170))
        print(out_name, img.size)


if __name__ == "__main__":
    main()
