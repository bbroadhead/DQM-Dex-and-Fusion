#!/usr/bin/env python3
"""Extract reviewable breeding table rows, without guessing recipe semantics."""
import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SOURCES = {
    "dwm1gbc": "https://www.woodus.com/den/games/dwm1gbc/breeding.php",
    "dwm2gbc": "https://www.woodus.com/den/games/dwm2gbc/breeding.php",
}

class TableReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.depth = 0
        self.table = None
        self.row = None
        self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.depth == 0:
                self.table = []
            self.depth += 1
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and tag in ("td", "th") and self.row is not None:
            self.cell = {"header": tag == "th", "text": ""}
        elif tag == "br" and self.cell is not None:
            self.cell["text"] += " "
    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.cell["text"] = re.sub(r"\s+", " ", self.cell["text"]).strip()
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.depth == 1 and self.row is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.depth:
            self.depth -= 1
            if self.depth == 0 and self.table is not None:
                if self.table:
                    self.tables.append(self.table)
                self.table = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=["all", *SOURCES], default="all")
    args = parser.parse_args()
    games = list(SOURCES) if args.game == "all" else [args.game]
    output = Path("data/woodus")
    output.mkdir(parents=True, exist_ok=True)
    for index, game in enumerate(games):
        url = SOURCES[game]
        request = Request(url, headers={"User-Agent": "PersonalDQMResearch/0.1 (manual breeding table review)"})
        with urlopen(request, timeout=30) as response:
            if urlparse(response.geturl()).hostname not in {"woodus.com", "www.woodus.com"}:
                raise RuntimeError("Unexpected redirect host")
            html = response.read(5_000_000).decode("utf-8", errors="replace")
        reader = TableReader()
        reader.feed(html)
        if not reader.tables:
            raise RuntimeError(f"No tables found on {url}; inspect page before importing recipes")
        tables = [
            {"table_index": i, "row_count": len(table), "rows": table}
            for i, table in enumerate(reader.tables)
        ]
        document = {
            "game": game, "source": url, "record_type": "breeding_table_candidates",
            "verified": False, "warning": "Raw table cells only; NOT validated breeding recipes.",
            "tables": tables,
        }
        destination = output / f"{game}-breeding-candidates.json"
        destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{game}: {len(tables)} tables, {sum(len(t['rows']) for t in tables)} rows")
        if index < len(games) - 1:
            time.sleep(3)

if __name__ == "__main__":
    main()
