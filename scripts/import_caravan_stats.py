#!/usr/bin/env python3
"""Import Caravan Heart star levels and stat growth from Slartifer's Monster FAQ.
Only exact normalized name matches are accepted. Unmatched entries remain unverified.
"""
import json,re
from pathlib import Path
from urllib.request import Request,urlopen
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
 req=Request(URL,headers={"User-Agent":"Mozilla/5.0 (personal research importer)"})
 with urlopen(req,timeout=40) as r:page=r.read().decode("utf-8","replace")
 parser=Text();parser.feed(page)
 source="\n".join(parser.parts)
 if "MONSTER STATS CHART" not in source:raise RuntimeError("FAQ stats section not found; no files modified")
 source=source.split("MONSTER STATS CHART",1)[1].split("EASY MONSTER GOODIES",1)[0]
 pattern=re.compile(r"^\s*([1-6])\s+(\d+)\s+(\d+)\s+((?:\d+/\d+\s+){6})(\d+/\d+)\s+\d+\s+\d+\s+(.+?)\s*$")
 found={}
 for line in source.splitlines():
  m=pattern.match(line)
  if not m:continue
  stars,weight,xp,gains,avg,name=m.groups()
  name=name.strip().lstrip("*").strip()
  stats=gains.split()+[avg]
  if len(stats)!=7:continue
  found[norm(name)]={"stars":int(stars),"weight":int(weight),"xp_to_level_10":int(xp),"growth":dict(zip(["hp","mp","attack","defense","speed","wisdom"],[dict(zip(["level_2","level_1_to_99"],map(int,x.split("/")))) for x in stats[:6]])),"average_growth":avg,"source":URL}
 if len(found)<150:raise RuntimeError(f"Only {len(found)} parsed stat records; source format may have changed")
 path=ROOT/"dqm3gba-details.json"
 data=json.loads(path.read_text(encoding="utf-8"))
 matched=0
 for monster in data["records"]:
  entry=found.get(norm(monster["name"]))
  if entry:
   monster["stats"]=entry;matched+=1
 report={"game":"dqm3gba","source":URL,"parsed_stat_names":len(found),"matched_roster":matched,"roster_total":len(data["records"]),"unmatched":[m["name"] for m in data["records"] if "stats" not in m]}
 if matched<140:raise RuntimeError(f"Only {matched} roster matches; refusing write")
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (ROOT/"dqm3gba-stats-import-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
