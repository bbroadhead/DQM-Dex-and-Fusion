#!/usr/bin/env python3
"""Validate imported Caravan Heart data without changing source files."""
import json
from pathlib import Path

root=Path("data/woodus")
def read(name):
    return json.loads((root/name).read_text(encoding="utf-8"))

details=read("dqm3gba-details.json")["records"]
general=read("dqm3gba-reform-general.json")
reform=read("dqm3gba-reform.json")
ids={m["id"] for m in details}
errors=[]
if len(ids)!=len(details):errors.append("Duplicate monster IDs")
families=["Beast","Demon","Material","Animal","Slime","Nature","Elemental"]
for star in range(1,6):
    table=general["stars"].get(str(star),{})
    for influence in families:
        row=table.get(influence,{})
        for dominant in families:
            result=row.get(dominant)
            if result is None:
                if not any(x["star"]==star and x["influencing"]==influence and x["dominant"]==dominant for x in general.get("unmatched",[])):
                    errors.append(f"Undocumented missing matrix entry: {star}/{influence}/{dominant}")
            elif result not in ids:errors.append(f"Unknown matrix result: {result}")
for index,r in enumerate(reform["recipes"]):
    for field in ("base","heart1","result"):
        if r.get(field) not in ids:errors.append(f"Recipe {index} invalid {field}: {r.get(field)}")
    if r.get("heart2") is not None and r["heart2"] not in ids:errors.append(f"Recipe {index} invalid heart2")
    if r.get("minimum_plus",0)<0:errors.append(f"Recipe {index} negative plus")
for m in details:
    stats=m.get("stats")
    if not stats:continue
    if stats.get("stars") not in range(1,7):errors.append(f"Invalid stats stars for {m['name']}")
    for attr in ("hp","mp","attack","defense","speed","wisdom"):
        if attr not in stats.get("growth",{}):errors.append(f"Missing {attr} growth for {m['name']}")
    if m.get("star_level") is not None and stats["stars"]!=m["star_level"]:\n        errors.append(f"Star classification disagrees with growth chart for {m['name']}: {m['star_level']} vs {stats['stars']}")\n    for key in ("weight","xp_to_level_10","average_growth","resistance_average"):
        if key not in stats:errors.append(f"Missing {key} for {m['name']}")
# A recipe's optional heart2 is only valid if a documented wildcard is present.
for index,r in enumerate(reform["recipes"]):
    if r.get("heart2") is None and "Slime-family" not in r.get("notes",""):
        errors.append(f"Recipe {index} has undocumented wildcard heart")
    if r.get("heart2") is None and r.get("base")=="dqm3gba:slime":
        # This rule cannot be automatically matched until the heart family's verified.
        pass
report={"roster":len(details),"classified_stars":sum(m.get("star_class") is not None for m in details),"with_growth_stats":sum(bool(m.get("stats")) for m in details),"general_cells":5*7*7,"unresolved_cells":len(general.get("unmatched",[])),"special_recipes":len(reform["recipes"]),"errors":errors}
print(json.dumps(report,indent=2))
if errors:raise SystemExit(1)
