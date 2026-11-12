#!/usr/bin/env python3
"""Join Woodus monster detail-page references to existing monster manifests."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path("data/woodus")
parser = argparse.ArgumentParser()
parser.add_argument("--game", choices=["all", "dwm1gbc", "dwm2gbc"], default="all")
args = parser.parse_args()
games = ["dwm1gbc", "dwm2gbc"] if args.game == "all" else [args.game]

def key(name):
    return re.sub(r"[^a-z0-9]", "", name.casefold())

for game in games:
    inventory = json.loads((ROOT / f"{game}-inventory.json").read_text(encoding="utf-8"))
    manifest_path = ROOT / f"{game}-monsters.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    detail_by_name = {}
    for link in inventory.get("links", []):
        url = link.get("url", "")
        parsed = urlparse(url)
        if parsed.hostname not in {"woodus.com", "www.woodus.com"}:
            continue
        if parsed.path != f"/den/games/{game}/monsters-details.php":
            continue
        mid = parse_qs(parsed.query).get("mid", [None])[0]
        if not mid or not mid.isdecimal():
            continue
        detail_by_name.setdefault(key(link.get("text", "")), {"detail_url": url, "source_monster_id": mid})
    matched = 0
    for monster in manifest["monsters"]:
        detail = detail_by_name.get(key(monster["name"]))
        if detail:
            monster.update(detail)
            matched += 1
    manifest["detail_links_matched"] = matched
    manifest["detail_links_unmatched"] = len(manifest["monsters"]) - matched
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{game}: matched {matched}/{len(manifest['monsters'])} detail URLs")
    if matched < len(manifest["monsters"]) * 0.9:
        raise RuntimeError(f"{game}: insufficient detail URL matches; inspect inventory")
