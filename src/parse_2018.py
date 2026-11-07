"""Parse the 2018 general election Race Summary Report (elchist331_state.htm) from its text into
{race name: [[candidate, party, votes], ...]}.

The 2018 page is laid out as preformatted text blocks separated by dashed lines rather than one row per candidate, so
it gets its own text parser. The first block keeps the report header in front of the first race name; the analysis
strips it (everything up to "PERCENT").

Usage: python3 parse_2018.py <elchist331_state.htm> <out_json>
"""
import html
import json
import os
import re
import sys


def main():
    src, out_json = sys.argv[1], sys.argv[2]
    s = open(src, encoding='latin-1').read()
    t = html.unescape(re.sub(r'<[^>]+>', ' ', s))
    t = re.sub(r'[ \t\r]+', ' ', t)
    races = {}
    for b in re.split(r'-{20,}', t):
        m = re.match(r'\s*(.+?) - (.+?)----------- Race Total ([\d,]+)', b, re.S)
        if not m:
            m = re.match(r'\s*(.+?) - (.+?)Race Total ([\d,]+)', b, re.S)
        if not m:
            continue
        office, body = m.group(1).strip(), m.group(2)
        cands = re.findall(r'([A-Z][^\d]+?)\s+(REP|DEM|LIB|GRN|IND|W|[A-Z]{2,3})\s+([\d,]+)\s+([\d.]+)%', body)
        races[office] = [(n.strip(), p, int(v.replace(',', ''))) for n, p, v, _ in cands]
    print(len(races), 'races in 2018')
    os.makedirs(os.path.dirname(out_json) or '.', exist_ok=True)
    json.dump({o: races[o] for o in races}, open(out_json, 'w'), indent=1)


if __name__ == '__main__':
    main()
