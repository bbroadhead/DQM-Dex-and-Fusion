#!/usr/bin/env python3
"""Normalize verified Woodus monster image references into game-specific manifests."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("data/woodus")
for game in ("dwm1gbc", "dwm2gbc"):
    inventory = json.loads((ROOT / f"{game}-inventory.json").read_text(encoding="utf-8"))
    records = []
    seen = set()
    expected = f"/den/gallery/graphics/{game}/monster/"
    for item in inventory.get("image_references", []):
        url = item.get("src", "")
        alt = item.get("alt", "")
        parsed = urlparse(url)
        if parsed.hostname not in {"woodus.com", "www.woodus.com"}:
            continue
        if not parsed.path.startswith(expected) or not alt.startswith("Monster Image: "):
            continue
        name = alt.removeprefix("Monster Image: ").strip()
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if not name or not slug or url in seen:
            continue
        seen.add(url)
        records.append({
            "id": f"{game}:{slug}",
            "name": name,
            "image_url": url,
            "image_status": "reference_only",
            "source_page": inventory["source"],
        })
    if not records:
        raise RuntimeError(f"No monster image references found for {game}; page format may have changed")
    records.sort(key=lambda record: (record["name"].casefold(), record["image_url"]))
    output = {"game": game, "record_type": "monster_image_reference",
              "verified": False, "monsters": records}
    target = ROOT / f"{game}-monsters.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{game}: {len(records)} candidate monsters -> {target}")
