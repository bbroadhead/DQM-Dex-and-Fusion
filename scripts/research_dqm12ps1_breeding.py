#!/usr/bin/env python3
"""Research-only comparison of GBC breeding charts to the PS1 collection roster.

This deliberately does NOT create PS1 breeding recipes. GBC rules may differ.
"""
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/woodus"
def read(name):
    return json.loads((DATA/name).read_text(encoding="utf-8"))
ps={x["id"].split(":",1)[1] for x in read("dqm12ps1-details.json")["records"]}
report={"game":"dqm12ps1","status":"research_only_not_verified_ps1_breeding","ps1_roster_count":len(ps),
 "notes":["The PS1 roster is confirmed; GBC breeding recipes are not PS1 evidence.",
          "Exact normalized English-name matches are preliminary and may not identify forms correctly.",
          "Do not load these comparison statistics as usable PS1 recipes."],
 "source_references":["https://www.woodus.com/den/games/dqm1_2psx/",
                      "https://www.woodus.com/forums/topic/8740-breeding-in-psx-ver/"],
 "gbc_chart_comparisons":{}}
for game in ("dwm1gbc","dwm2gbc"):
    source=read(game+"-breeding-normalized.json")
    rows=source["rows"]
    counts=Counter()
    for row in rows:
        child=row.get("offspring",{})
        if child.get("kind")!="monster":counts["non_monster_offspring"]+=1;continue
        key=child.get("id","").split(":",1)[-1]
        if key in ps:counts["offspring_name_in_ps1_roster"]+=1
        else:counts["offspring_name_not_in_ps1_roster"]+=1
        specs=[row.get("parent1",{}),row.get("parent2",{})]
        if all(p.get("kind") in ("monster","family") for p in specs):
            if all(p.get("kind")!="monster" or p.get("id","").split(":",1)[-1] in ps for p in specs):
                counts["both_parent_names_or_families_represented_in_ps1"]+=1
    report["gbc_chart_comparisons"][game]={"source_rows":len(rows),**dict(counts),
      "interpretation":"Name overlap only; zero recipes verified for PS1"}
out=DATA/"dqm12ps1-breeding-research.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["gbc_chart_comparisons"],indent=2))
