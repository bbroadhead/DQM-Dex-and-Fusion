#!/usr/bin/env python3
"""Import a small, resumable batch of monster detail fields from Woodus."""
import argparse
import json
import re
import time
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
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

def normalize_detail_url(url):
    """Encode query values such as 'Anteater (M1)' before HTTP requests."""
    parts = urlsplit(url)
    if parts.hostname not in {"www.woodus.com", "woodus.com"}:
        raise RuntimeError("Unexpected detail URL host")
    if not parts.path.endswith("/monsters-details.php"):
        raise RuntimeError("Unexpected detail URL path")
    query = urlencode(parse_qsl(parts.query, keep_blank_values=True))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=["all", "dwm1gbc", "dwm2gbc"], default="all")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--delay", type=float, default=4.0)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 530:
        parser.error("--batch-size must be 1 to 530")
    if args.delay < 3:
        parser.error("--delay must be at least 3 seconds")
    games = ["dwm1gbc", "dwm2gbc"] if args.game == "all" else [args.game]
    for game in games:
        manifest = json.loads((ROOT / f"{game}-monsters.json").read_text(encoding="utf-8"))
        destination = ROOT / f"{game}-details.json"
        existing = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else {"game": game, "record_type": "source_listed_monster_details", "records": []}
        by_id = {r["id"]: r for r in existing["records"]}
        pending = [m for m in manifest["monsters"] if m["id"] not in by_id and m.get("detail_url")]
        failures = []
        selected = pending[:args.batch_size]
        for i, monster in enumerate(selected):
            url = normalize_detail_url(monster["detail_url"])
            try:
                for attempt in range(3):
                    try:
                        request = Request(url, headers={"User-Agent": "PersonalDQMResearch/0.1 (manual rate-limited batch)"})
                        with urlopen(request, timeout=30) as response:
                            if urlsplit(response.geturl()).hostname not in {"www.woodus.com", "woodus.com"}:
                                raise RuntimeError("Unexpected redirect host")
                            html = response.read(5_000_000).decode("utf-8", errors="replace")
                        fields = parse_fields(html)
                        break
                    except (HTTPError, URLError, TimeoutError) as exc:
                        if isinstance(exc, HTTPError) and exc.code in (401, 403, 404):
                            raise
                        if attempt == 2:
                            raise
                        time.sleep(10 * (attempt + 1))
                by_id[monster["id"]] = {
                    "id": monster["id"], "name": monster["name"],
                    "source_monster_id": monster["source_monster_id"],
                    "source_url": monster["detail_url"],
                    "values_are": "source_listed_unclassified", **fields,
                }
                print(f"{game}: imported {monster['name']} ({i+1}/{len(selected)})", flush=True)
            except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
                failures.append({"id": monster["id"], "error": str(exc)[:200]})
                print(f"{game}: FAILED {monster['name']}: {exc}", flush=True)
                if isinstance(exc, HTTPError) and exc.code in (403, 429):
                    print("Access restricted or rate limited; stopping this game early.", flush=True)
                    break
            finally:
                existing["records"] = sorted(by_id.values(), key=lambda x: x["id"])
                existing["imported_count"] = len(existing["records"])
                existing["total_monsters"] = len(manifest["monsters"])
                destination.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                if i < len(selected) - 1:
                    time.sleep(args.delay)
        report = {
            "game": game, "imported": len(by_id),
            "total": len(manifest["monsters"]),
            "remaining": len(manifest["monsters"]) - len(by_id),
            "failures": failures,
        }
        (ROOT / f"{game}-import-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"{game}: {report['imported']}/{report['total']}; {len(failures)} failures", flush=True)

if __name__ == "__main__":
    main()
