#!/usr/bin/env python3
"""Import a small, resumable batch of monster detail fields from Woodus."""
import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path("data/woodus")
FIELDS = {
    "Japanese Name": "japanese_name",
    "Location": "location",
    "Hit Points": "hit_points",
    "Magic Points": "magic_points",
    "Attack": "attack",
    "Defense": "defense",
    "Gold Dropped": "gold_dropped",
    "Experience Earned": "experience_earned",
    "Book Number": "book_number",
    "Monster Abilites": "abilities_raw",
    "Monster Abilities": "abilities_raw",
    "Japan Appearance": "japan_appearance",
}
NUMERIC = {"hit_points", "magic_points", "attack", "defense", "gold_dropped", "experience_earned", "book_number", "japan_appearance"}

class Cells(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.current = None
        self.row = []
        self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and tag in ("td", "th"):
            self.current = ""
    def handle_data(self, data):
        if self.current is not None:
            self.current += data
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.current is not None:
            self.row.append(re.sub(r"\s+", " ", self.current).strip())
            self.current = None
        elif tag == "tr" and self.depth == 1 and self.row:
            self.rows.append(self.row)
            self.row = []
        elif tag == "table":
            self.depth -= 1

def parse_fields(html):
    parser = Cells()
    parser.feed(html)
    fields = {}
    for row in parser.rows:
        if len(row) < 2:
            continue
        label = row[0].rstrip(":").strip()
        field = FIELDS.get(label)
        if field is None:
            continue
        value = row[1].strip()
        if field in NUMERIC:
            fields[field] = int(value) if value.isdecimal() else None
        elif field == "abilities_raw":
            fields[field] = value
        else:
            fields[field] = value or None
    if not all(field in fields for field in ("hit_points", "magic_points", "attack", "defense")):
        raise ValueError("Missing expected stats; source layout may have changed")
    return fields

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=["all", "dwm1gbc", "dwm2gbc"], default="all")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 10:
        parser.error("--batch-size must be 1 to 10")
    games = ["dwm1gbc", "dwm2gbc"] if args.game == "all" else [args.game]
    for game in games:
        manifest = json.loads((ROOT / f"{game}-monsters.json").read_text(encoding="utf-8"))
        destination = ROOT / f"{game}-details.json"
        existing = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else {"game": game, "record_type": "source_listed_monster_details", "records": []}
        by_id = {r["id"]: r for r in existing["records"]}
        pending = [m for m in manifest["monsters"] if m["id"] not in by_id and m.get("detail_url")]
        for i, monster in enumerate(pending[:args.batch_size]):
            url = monster["detail_url"]
            if urlparse(url).hostname not in {"www.woodus.com", "woodus.com"}:
                raise RuntimeError("Unexpected detail URL host")
            request = Request(url, headers={"User-Agent": "PersonalDQMResearch/0.1 (small manual batch)"})
            with urlopen(request, timeout=30) as response:
                if urlparse(response.geturl()).hostname not in {"www.woodus.com", "woodus.com"}:
                    raise RuntimeError("Unexpected redirect host")
                html = response.read(5_000_000).decode("utf-8", errors="replace")
            by_id[monster["id"]] = {
                "id": monster["id"], "name": monster["name"],
                "source_monster_id": monster["source_monster_id"],
                "source_url": url, "values_are": "source_listed_unclassified",
                **parse_fields(html),
            }
            print(f"{game}: imported {monster['name']}")
            if i < min(args.batch_size, len(pending)) - 1:
                time.sleep(3)
        existing["records"] = sorted(by_id.values(), key=lambda x: x["id"])
        existing["imported_count"] = len(existing["records"])
        existing["total_monsters"] = len(manifest["monsters"])
        destination.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{game}: {existing['imported_count']}/{existing['total_monsters']} detail records")

if __name__ == "__main__":
    main()
