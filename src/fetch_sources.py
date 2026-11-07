"""Download every source file listed in data/SOURCES.csv again, into a new folder, and check it against the copy
committed here.

- 2020-2024 JSON (results.texas-election.com): final results; compared byte for byte (sha256).
- 1992-2018 pages (elections.sos.state.tx.us): served through Cloudflare, which rewrites an obfuscated e-mail link and
  adds a script tag on every request, so the bytes never match. The check is on the parsed results instead: the new
  pages are parsed with parse_elchist.py and parse_2018.py and compared with data/intermediate/.
- 2026 (goelect.txelections.civixapps.com): unofficial and updated by the Secretary of State until the canvass, so a
  difference means newer numbers, not an error. The new file is decoded and its LastUpdatedTime printed.
Both sites refuse requests without a browser-style User-Agent (HTTP 403), so one is sent.

Usage: python3 fetch_sources.py <new_empty_folder> [--pause SECONDS]   (default pause 3 s between requests)
"""
import csv
import hashlib
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
UA = "Mozilla/5.0 (compatible; texas-2026-midterm-expected-vote/1.0)"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(*args):
    subprocess.run([sys.executable, "-I", *args], check=True, stdout=subprocess.DEVNULL)


def main():
    out = sys.argv[1]
    pause = float(sys.argv[sys.argv.index("--pause") + 1]) if "--pause" in sys.argv else 3.0
    if os.path.exists(out) and os.listdir(out):
        sys.exit(f"{out} is not empty; give a new folder so nothing is overwritten")
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "SOURCES.csv"))))
    failed = 0
    for i, r in enumerate(rows):
        if i:
            time.sleep(pause)
        dest = os.path.join(out, os.path.relpath(r["file"], "data/raw"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        hdr = {"User-Agent": UA, "Accept-Encoding": "identity"}
        if not r["url"].endswith(".htm"):
            hdr["Accept"] = "application/json"
        try:
            with urllib.request.urlopen(urllib.request.Request(r["url"], headers=hdr), timeout=60) as resp:
                body = resp.read()
        except Exception as e:  # report and go on to the next source
            print(f"ERROR    {r['url']}: {e}")
            failed += 1
            continue
        open(dest, "wb").write(body)
        if r["url"].endswith(".htm"):
            status = "fetched "
        elif sha(body) == r["sha256"]:
            status = "SAME    "
        elif "53815" in r["url"]:
            status = "NEWER?  "
        else:
            status = "CHANGED "
            failed += 1
        print(f"{status} {r['file']}  ({len(body):,} bytes)")

    def same(a, b):
        return os.path.exists(a) and open(a, "rb").read() == open(b, "rb").read()

    pages = os.path.join(out, "sos_elchist_1992_2018")
    parsed = os.path.join(out, "_parsed")
    if os.path.exists(os.path.join(pages, "elchist331_state.htm")):
        run(os.path.join(SRC, "parse_elchist.py"), pages, os.path.join(parsed, "elchist_parsed.json"))
        run(os.path.join(SRC, "parse_2018.py"), os.path.join(pages, "elchist331_state.htm"),
            os.path.join(parsed, "tx2018_races.json"))
        for f in ("elchist_parsed.json", "tx2018_races.json"):
            ok = same(os.path.join(parsed, f), os.path.join(ROOT, "data", "intermediate", f))
            failed += not ok
            print(f"{'SAME    ' if ok else 'CHANGED '} parsed 1992-2018 results: {f}")
    enr = os.path.join(out, "sos_enr_2026", "election_53815.json")
    if os.path.exists(enr):
        print(subprocess.run([sys.executable, "-I", os.path.join(SRC, "decode_2026.py"), enr, parsed],
                             check=True, capture_output=True, text=True).stdout.strip())
        for f in ("tx2026_StateWide.json", "tx2026_Federal.json"):
            ok = same(os.path.join(parsed, f), os.path.join(ROOT, "data", "intermediate", f))
            print(f"{'SAME    ' if ok else 'NEWER   '} 2026 unofficial results: {f}")
    print("fetch:", "OK" if not failed else f"{failed} problem(s)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
