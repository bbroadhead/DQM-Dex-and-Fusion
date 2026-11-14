#!/usr/bin/env python3
"""Import Caravan Heart star levels and stat growth from Slartifer's Monster FAQ.
Only exact normalized name matches are accepted. Unmatched entries remain unverified.
"""
import json,re
from pathlib import Path
import argparse
from html.parser import HTMLParser
URL="https://gamefaqs.gamespot.com/gba/916688-dragon-quest-monsters-caravan-heart/faqs/62549"
ROOT=Path("data/woodus")
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.in_pre=False
 def handle_starttag(self,tag,attrs):
  if tag=="pre":self.in_pre=True
 def handle_endtag(self,tag):
  if tag=="pre":self.in_pre=False
 def handle_data(self,data):
  if self.in_pre:self.parts.append(data)
def norm(s):return re.sub(r"[^a-z0-9]","",s.casefold())
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--source-file",type=Path,default=Path("data/sources/caravan-heart-monster-faq.txt"))
 args=ap.parse_args()
 if not args.source_file.is_file():
  raise SystemExit("Source guide not found: "+str(args.source_file)+". Save the guide as UTF-8 plain text at this path, then rerun.")
 page=args.source_file.read_text(encoding="utf-8")
 if "<pre" in page.lower():
  parser=Text();parser.feed(page);source="\n".join(parser.parts)
 else:source=page
 if source.count("MONSTER STATS CHART")<2:raise RuntimeError("FAQ stats section not found; no files modified")
 source=source.rsplit("MONSTER STATS CHART",1)[1].split("EASY MONSTER GOODIES",1)[0]
 # FAQ lines contain six growth pairs, one average pair, two resistance scores,
 # then the monster name. Asterisks mark special-only species.
 pattern=re.compile(r"^\\s*([1-6])\\s+(\\d+)\\s+(\\d+)\\s+((?:\\d+/\\d+\\s+){6})(\\d+/\\d+)\\s+(\\d+)\\s+(\\d+)\\s+\\*?(.+?)\\s*$")
 found={}
 for line in source.splitlines():
  m=pattern.match(line)
  if not m:continue
  stars,weight,xp,gains,avg,direct,status,name=m.groups()
  name=name.strip()
  pairs=gains.split()
  if len(pairs)!=6:continue
  key=norm(name)
  if key in found:raise RuntimeError("Duplicate FAQ stat entry: "+name)
  found[key]={"stars":int(stars),"weight":int(weight),"xp_to_level_10":int(xp),
   "growth":dict(zip(["hp","mp","attack","defense","speed","wisdom"],
    [dict(zip(["level_2","level_1_to_99"],map(int,x.split("/")))) for x in pairs])),
   "average_growth":dict(zip(["level_2","level_1_to_99"],map(int,avg.split("/")))),
   "resistance_average":{"direct_damage":int(direct),"status":int(status)},
   "special_reform_only":bool(re.search(r"\\s\\*"+re.escape(name)+r"\\s*$",line)),"source":URL}
 if len(found)<150:raise RuntimeError(f"Only {len(found)} parsed stat records; source format may have changed")
 path=ROOT/"dqm3gba-details.json"
 data=json.loads(path.read_text(encoding="utf-8"))
 matched=0
 conflicts=[]
 for monster in data["records"]:
  entry=found.get(norm(monster["name"]))
  if not entry:continue
  existing=monster.get("stats")
  if existing:
   comparable=("stars","weight","xp_to_level_10","growth","average_growth","resistance_average")
   if any(existing.get(k)!=entry.get(k) for k in comparable):
    conflicts.append(monster["name"])
    continue
  if monster.get("star_level") is not None and monster["star_level"]!=entry["stars"]:
   conflicts.append(monster["name"]+" (star classification)")
   continue
  monster["stats"]=entry
  matched+=1
 if conflicts:raise RuntimeError("Conflicting existing metadata; no files modified: "+", ".join(conflicts))
 report={"game":"dqm3gba","source":URL,"parsed_stat_names":len(found),"matched_roster":matched,"roster_total":len(data["records"]),"unmatched":[m["name"] for m in data["records"] if "stats" not in m]}
 if matched<140:raise RuntimeError(f"Only {matched} roster matches; refusing write")
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (ROOT/"dqm3gba-stats-import-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
