#!/usr/bin/env python3
"""Validate imported PS1 roster, source references and GBC-derived family provenance."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((root/"data/woodus"/name).read_text(encoding="utf-8"))
ps=read("dqm12ps1-details.json")["records"]
images=read("dqm12ps1-image-report.json")["images"]
families=read("dqm12ps1-monsters.json")["monsters"]
gbc={}
for game in ("dwm1gbc","dwm2gbc"):
    gbc[game]={m["id"].split(":",1)[1]:m.get("family") for m in read(game+"-monsters.json")["monsters"]}
assert len(ps)==317, f"Expected 317 PS1 entries, got {len(ps)}"
assert len({m["id"] for m in ps})==317,"Duplicate PS1 monster ID"
assert len(images)==317, f"Expected 317 PS1 images, got {len(images)}"
assert len(families)==317,"PS1 family index mismatch"
by_id={m["id"]:m for m in ps}
for record in ps:
    ident=record["id"];key=ident.split(":",1)[1]
    assert record["name"] and record.get("japanese_name"),ident
    assert record["source_url"].startswith("https://www.woodus.com/den/games/dqm1_2psx/"),ident
    image=images[ident]
    assert image["local_path"].startswith("assets/monsters/dqm12ps1/"),ident
    assert (root/image["local_path"]).is_file(),f"Missing image file for {ident}"
    matching={game:items[key] for game,items in gbc.items() if items.get(key)}
    assert len(set(matching.values()))<=1, f"Conflicting GBC families for {ident}"
    if matching:
        assert record.get("family")==next(iter(matching.values())),f"Family mismatch: {ident}"
        assert record.get("family_verification")=="inferred_from_corresponding_GBC_species_not_PS1_verified",ident
        assert set(record.get("family_source_games",[]))==set(matching),ident
    else:
        assert record.get("family") is None,f"Unverified family assigned to {ident}"
for item in families:
    assert item["id"] in by_id,item["id"]
    assert item["family"]==by_id[item["id"]].get("family"),item["id"]
print(f"PS1 data valid: {len(ps)} monsters, {len(images)} local images, {sum(bool(m.get('family')) for m in ps)} cross-referenced families")
