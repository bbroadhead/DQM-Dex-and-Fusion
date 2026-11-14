#!/usr/bin/env python3
"""Extract research-only rows from official PS1 DQM 1+2 breeding pages.

No extracted row is treated as a verified recipe until manually mapped and reviewed.
"""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/woodus/dqm12ps1-official-breeding-raw.json"
BASE = "https://www.jp.square-enix.com/dragonquest/psdqm12/slash/haigouhyou/"
FAMILIES = ("slime", "dragon", "beast", "bird", "plant", "bug", "devil", "zombie", "material", "water", "boss")

class TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.row = None
        self.cell = None
        self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")
    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(self.row):
                self.rows.append(self.row)
            self.row = None

def decode(raw):
    for enc in ("shift_jis", "cp932", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    raise ValueError("Unable to decode official page; do not use lossy text")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", action="append", choices=FAMILIES)
    args = parser.parse_args()
    results = []
    for family in args.family or ("slime", "dragon"):
        url = BASE + "haigou_rare5_" + family + ".html"
        try:
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as response:
                page = decode(response.read())
            reader = TableReader()
            reader.feed(page)
            results.append({"family": family, "source_url": url, "status": "raw_unmapped_not_verified", "table_rows": reader.rows, "row_count": len(reader.rows)})
            print(f"{family}: {len(reader.rows)} table rows")
        except Exception as exc:
            results.append({"family": family, "source_url": url, "status": "fetch_failed", "error": str(exc)})
            print(f"{family}: fetch failed: {exc}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"game": "dqm12ps1", "status": "research_only", "sources": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
