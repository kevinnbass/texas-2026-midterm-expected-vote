"""Compare a fresh build (build.sh) with the committed data and figures.

Data files (JSON, CSV) must match byte for byte. Figures: a byte match is expected on a machine with the same
matplotlib, FreeType and Inter font as the original; elsewhere text rendering differs slightly, so for each figure
that is not byte-identical this reports the share of pixels that differ and the largest per-channel difference.

Usage: python3 verify.py <build_dir> [--strict]   (--strict: figures must also match byte for byte)
Exit code 0 when everything required matches, 1 otherwise.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = ["data/intermediate/elchist_parsed.json", "data/intermediate/tx2018_races.json",
        "data/intermediate/tx2026_StateWide.json", "data/intermediate/tx2026_Federal.json",
        "data/derived/texas_statewide_2018_2022_2026.csv", "data/derived/texas_midterm_vs_presidential.csv"]
FIGS = ["figures/panels/texas_midterm_vs_presidential_history.png",
        "figures/panels/texas_midterm_vs_presidential_history_incumbency.png",
        "figures/panels/texas_statewide_expected_2018_2026.png",
        "figures/panels/texas_statewide_expected_incumbency_2018_2026.png",
        "figures/texas_history_and_expected.png", "figures/texas_incumbency_history_and_expected.png"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def built_path(build, rel):
    return os.path.join(build, rel.replace("data/", "", 1))


def main():
    build = sys.argv[1]
    strict = "--strict" in sys.argv[2:]
    ok = True
    for rel in DATA:
        a, b = os.path.join(ROOT, rel), built_path(build, rel)
        same = os.path.exists(b) and sha(a) == sha(b)
        ok &= same
        print(f"{'MATCH' if same else 'DIFF '}  {rel}")
    for rel in FIGS:
        a, b = os.path.join(ROOT, rel), built_path(build, rel)
        if not os.path.exists(b):
            print(f"MISSING {rel}")
            ok = False
            continue
        if sha(a) == sha(b):
            print(f"MATCH  {rel}")
            continue
        from PIL import Image, ImageChops
        A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        if A.size != B.size:
            print(f"DIFF   {rel}: size {B.size} vs committed {A.size}")
        else:
            d = ImageChops.difference(A, B)
            px = sum(1 for p in d.getdata() if p != (0, 0, 0))
            print(f"DIFF   {rel}: {100 * px / (A.width * A.height):.3f}% of pixels differ, "
                  f"largest channel difference {max(hi for _, hi in d.getextrema())}")
        ok &= not strict
    print("verify:", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
