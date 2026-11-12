#!/usr/bin/env python3
"""Sample individual Woodus monster detail pages for schema inspection.

Fetches only one page per selected game. Data is not normalized or verified.
"""
import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path("data/woodus")

class DetailReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.table = None
        self.row = None
        self.cell = None
        self.tables = []
        self.headings = []
        self.heading = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.depth == 0:
                self.table = []
            self.depth += 1
        elif tag == "tr" and self.depth == 1:
            self.row = []
        elif tag in ("td", "th") and self.depth == 1 and self.row is not None:
            self.cell = {"header": tag == "th", "text": ""}
        elif tag in ("h1", "h2", "h3", "h4"):
            self.heading = {"level": tag, "text": ""}
        elif tag == "br" and self.cell is not None:
            self.cell["text"] += " "

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data
        if self.heading is not None:
            self.heading["text"] += data

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
            if self.depth == 0:
                if self.table:
                    self.tables.append(self.table)
                self.table = None
        elif self.heading is not None and tag == self.heading["level"]:
            self.heading["text"] = re.sub(r"\s+", " ", self.heading["text"]).strip()
            self.headings.append(self.heading)
            self.heading = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=["all", "dwm1gbc", "dwm2gbc"], default="all")
    args = parser.parse_args()
    games = ["dwm1gbc", "dwm2gbc"] if args.game == "all" else [args.game]
    for index, game in enumerate(games):
        manifest = json.loads((ROOT / f"{game}-monsters.json").read_text(encoding="utf-8"))
        sample = next((m for m in manifest["monsters"] if m.get("detail_url")), None)
        if sample is None:
            raise RuntimeError(f"No monster detail links for {game}")
        url = sample["detail_url"]
        parsed_url = urlparse(url)
        if parsed_url.hostname not in ("www.woodus.com", "woodus.com"):
            raise RuntimeError("Untrusted detail URL")
        request = Request(url, headers={"User-Agent": "PersonalDQMResearch/0.1 (one detail page per game)"})
        with urlopen(request, timeout=30) as response:
            if urlparse(response.geturl()).hostname not in ("www.woodus.com", "woodus.com"):
                raise RuntimeError("Unexpected redirect")
            html = response.read(5_000_000).decode("utf-8", errors="replace")
        reader = DetailReader()
        reader.feed(html)
        document = {
            "game": game, "monster_id": sample["id"], "name": sample["name"],
            "source": url, "verified": False,
            "note": "One sample detail page; raw headings and table cells for schema inspection only.",
            "headings": reader.headings,
            "tables": [{"table_index": i, "row_count": len(t), "rows": t} for i, t in enumerate(reader.tables)]
        }
        target = ROOT / f"{game}-detail-sample.json"
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{game}: sampled {sample['name']} with {len(reader.tables)} tables")
        if index < len(games) - 1:
            time.sleep(3)

if __name__ == "__main__":
    main()
