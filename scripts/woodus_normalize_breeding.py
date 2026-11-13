#!/usr/bin/env python3
"""Resolve Woodus breeding transcription aliases without inventing monsters.
Preserves original rows and alternatives; unmatched names remain explicit.
"""
import json,re
from pathlib import Path

ALIASES={
 "dwm1gbc":{"anteater":"Anteater (M1)","tortagon":"Tortragon","monnonja":"Mommonja","drool":"Droll","rouge nite":"RogueNite"},
 "dwm2gbc":{"orgodemir":"Orgodemir (1)","watabou (dwm1)":"Watabou","bigroost (dwm1)":"BigRoost"}
}
# Woodus breeding charts list alternatives separated by slash.
# A literal N/A or ----- is not a parent and must never become a monster.
EMPTY={"n/a","-----",""}
def key(s):return re.sub(r"[^a-z0-9]","",s.lower())
def main():
 for game in ("dwm1gbc","dwm2gbc"):
  path=Path(f"data/woodus/{game}-breeding-rows.json")
  raw=json.loads(path.read_text())
  manifest=json.loads(Path(f"data/woodus/{game}-monsters.json").read_text())
  lookup={}
  for m in manifest["monsters"]:
   lookup.setdefault(key(m["name"]),[]).append(m)
  rows=[];unresolved=[];fully_resolved=0;alternatives=0;unavailable=0
  invalid_offspring={"deathmore4","deathmore5","deathmore6","deathmore7","dracolord3","mirudraas3","orgodemir3"} if game=="dwm2gbc" else set()
  for index,row in enumerate(raw["rows"]):
   entry={k:row[k] for k in ("family","source","raw_cells")}
   entry["source_row_index"]=index
   for field in ("offspring","parent1","parent2"):
    original=row[field]
    if original["kind"]=="family":
     entry[field]=original
     continue
    label=original["label"].strip()
    if label.lower() in EMPTY:
     entry[field]={"kind":"unavailable","label":label}
     continue
    level_match=re.fullmatch(r"(.+?)\s*\+(\d+)",label)
    required_plus=int(level_match.group(2)) if level_match else None
    normalized_label=level_match.group(1) if level_match else label
    choices=[]
    for term in re.split(r"\s*/\s*",normalized_label):
     target=ALIASES[game].get(term.lower(),term)
     found=lookup.get(key(target),[])
     if len(found)==1:
      choices.append({"id":found[0]["id"],"name":found[0]["name"],"source_label":term})
     else:
      choices.append({"id":None,"source_label":term})
    if len(choices)>1:
     entry[field]={"kind":"alternatives","label":label,"options":choices}
     alternatives+=1
    elif choices[0]["id"]:
     entry[field]={"kind":"monster","label":label,"id":choices[0]["id"]}
     if required_plus is not None:entry[field]["minimum_plus"]=required_plus
    else:
     entry[field]={"kind":"unresolved","label":label}
   fields=[entry[f] for f in ("offspring","parent1","parent2")]
   if all(v["kind"] in ("monster","family") for v in fields):fully_resolved+=1
   if any(v["kind"] in ("unresolved","unavailable") or (v["kind"]=="alternatives" and any(not x["id"] for x in v["options"])) for v in fields):
    unresolved.append({"index":index,"offspring":entry["offspring"],"parent1":entry["parent1"],"parent2":entry["parent2"]})
   if key(row["offspring"]["label"]) in invalid_offspring:
    entry["breeding_available"]=False
    entry["exclusion_reason"]="Offspring name not present in the game roster; source breeding chart inconsistency"
   elif any(v["kind"]=="unavailable" for v in fields):
    entry["breeding_available"]=False
    unavailable+=1
   else:entry["breeding_available"]=True
   rows.append(entry)
  output={"game":game,"verified":False,"record_type":"normalized_breeding_chart_rows",
    "warning":"Source transcription and name matching only; breeding mechanics, variants and priority not independently verified.",
    "total_rows":len(rows),"simple_rows":fully_resolved,"alternative_fields":alternatives,"unavailable_rows":unavailable,
    "unresolved_rows":len(unresolved),"unresolved_details":unresolved,
    "source_file":str(path),"rows":rows}
  out=Path(f"data/woodus/{game}-breeding-normalized.json")
  out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
  print(game,"rows",len(rows),"simple",fully_resolved,"unresolved",len(unresolved),"unavailable",unavailable,"alternatives",alternatives)
if __name__=="__main__":main()
