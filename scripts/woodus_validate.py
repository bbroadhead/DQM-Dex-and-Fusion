#!/usr/bin/env python3
"""Check Woodus detail imports for duplicates, mismatched IDs and missing core fields."""
import argparse
import json
from pathlib import Path

ROOT = Path("data/woodus")
parser = argparse.ArgumentParser()
parser.add_argument("--game", choices=["all", "dwm1gbc", "dwm2gbc"], default="all")
args = parser.parse_args()
games = ["dwm1gbc", "dwm2gbc"] if args.game == "all" else [args.game]
for game in games:
    manifest = json.loads((ROOT / f"{game}-monsters.json").read_text(encoding="utf-8"))
    details = json.loads((ROOT / f"{game}-details.json").read_text(encoding="utf-8"))
    indexed = {m["id"]: m for m in manifest["monsters"]}
    records = details["records"]
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{game}: duplicate monster IDs")
    if len(records) != details["imported_count"]:
        raise ValueError(f"{game}: imported_count mismatch")
    if len(indexed) != details["total_monsters"]:
        raise ValueError(f"{game}: total_monsters mismatch")
    for record in records:
        source = indexed.get(record["id"])
        if source is None:
            raise ValueError(f"{game}: unknown monster {record['id']}")
        for field in ("name", "source_monster_id"):
            if record[field] != source[field]:
                raise ValueError(f"{game}: mismatched {field} for {record['id']}")
        if record["source_url"] != source["detail_url"]:
            raise ValueError(f"{game}: mismatched source URL for {record['id']}")
        for field in ("hit_points", "magic_points", "attack", "defense"):
            if not isinstance(record.get(field), int) or record[field] < 0:
                raise ValueError(f"{game}: invalid {field} for {record['id']}")
    print(f"{game}: validated {len(records)} records; {len(indexed)-len(records)} remain")
