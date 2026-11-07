"""Parse the Texas Secretary of State "Race Summary Report" pages (elchist<id>_state.htm, general elections 1992-2018)
into {year: {race name: [[candidate, party, votes], ...]}}.

Each page is an HTML table: a race starts with a row whose first cell spans two columns and whose other cells are
empty; candidate rows have the name, party and vote count in cells 2-4. All races on the page are kept; the analysis
picks statewide offices later.

Usage: python3 parse_elchist.py <folder with elchist*_state.htm> <out_json>
"""
import glob
import html
import json
import os
import re
import sys


def cells(tr):
    return [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'(?is)<td[^>]*>(.*?)</td>', tr)]


def main():
    src, out_json = sys.argv[1], sys.argv[2]
    out = {}
    for f in sorted(glob.glob(os.path.join(src, 'elchist*_state.htm'))):
        s = open(f, encoding='latin-1').read()
        t = html.unescape(re.sub(r'<[^>]+>', ' ', s))
        y = int(re.search(r'((?:19|20)\d\d) General Election', t).group(1))
        races, cur = {}, None
        for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>', s):
            c = cells(tr)
            if not c:
                continue
            if re.search(r'(?i)<td colspan=2', tr) and c[0] and not any(c[1:]):
                cur = re.sub(r'\s+', ' ', c[0])
                races[cur] = []
                continue
            if cur and len(c) >= 4 and c[2] and re.fullmatch(r'[\d,]+', c[3] or 'x') and c[1]:
                races[cur].append((re.sub(r'\s+', ' ', c[1]), c[2], int(c[3].replace(',', ''))))
        out[y] = races
        print(y, os.path.basename(f), len(races), 'races')
    os.makedirs(os.path.dirname(out_json) or '.', exist_ok=True)
    json.dump(out, open(out_json, 'w'), indent=1)


if __name__ == '__main__':
    main()
