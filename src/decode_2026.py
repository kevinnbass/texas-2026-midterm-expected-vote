"""Decode the 2026 general election results file from the Texas SOS results site (Civix ENR, election 53815).

The file is JSON whose fields (StateWide, Federal, Home, ...) each hold base64-encoded JSON. This writes the decoded
StateWide and Federal parts as tx2026_StateWide.json and tx2026_Federal.json, and prints the SOS update time (Home).

Usage: python3 decode_2026.py <election_53815.json> <out_dir>
"""
import base64
import json
import os
import sys


def main():
    src, out = sys.argv[1], sys.argv[2]
    d = json.load(open(src))
    dec = lambda k: json.loads(base64.b64decode(d[k]))
    home = dec('Home')
    print('SOS LastUpdatedTime:', home['LastUpdatedTime'], '| counties reporting:', home['CountiesReporting'])
    os.makedirs(out, exist_ok=True)
    for k in ('StateWide', 'Federal'):
        json.dump(dec(k), open(os.path.join(out, f'tx2026_{k}.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
