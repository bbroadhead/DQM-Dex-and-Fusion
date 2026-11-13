#!/usr/bin/env python3
"""Import reviewable breeding chart rows from Woodus family pages.
Explicitly preserve family-wide parents, variants and ambiguous cells.
Do not treat these as validated in-game breeding outcomes.
"""
import argparse,json,re,time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen

FAMILIES={"dwm1gbc":["beast","bird","boss","bug","devil","dragon","material","plant","slime","zombie"],
"dwm2gbc":["beast","bird","boss","bug","devil","dragon","material","plant","slime","water","zombie"]}

class TableReader(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.tables=[];self.table=None;self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=="table":
   if self.depth==0:self.table=[]
   self.depth+=1
  elif tag=="tr" and self.depth==1:self.row=[]
  elif tag in ("td","th") and self.depth==1 and self.row is not None:self.cell=""
  elif tag=="br" and self.cell is not None:self.cell+=" / "
 def handle_data(self,data):
  if self.cell is not None:self.cell+=data
 def handle_endtag(self,tag):
  if tag in ("td","th") and self.cell is not None:
   self.row.append(re.sub(r"\s+"," ",self.cell).strip());self.cell=None
  elif tag=="tr" and self.depth==1 and self.row is not None:
   if self.row:self.table.append(self.row)
   self.row=None
  elif tag=="table" and self.depth:
   self.depth-=1
   if self.depth==0:
    if self.table:self.tables.append(self.table)
    self.table=None

def main():
 p=argparse.ArgumentParser();p.add_argument("--game",choices=["all",*FAMILIES],default="all");a=p.parse_args()
 games=list(FAMILIES) if a.game=="all" else [a.game]
 for game in games:
  manifest=json.loads(Path(f"data/woodus/{game}-monsters.json").read_text())
  known={re.sub(r"[^a-z0-9]","",m["name"].lower()):m["id"] for m in manifest["monsters"]}
  rows=[];unmatched=[];family_stats={}
  for family in FAMILIES[game]:
   url=f"https://www.woodus.com/den/games/{game}/breeding-details.php?fam={family}"
   try:
    with urlopen(Request(url,headers={"User-Agent":"PersonalDQMResearch/0.1 (breeding research)"}),timeout=30) as res:
     if urlsplit(res.geturl()).hostname not in ("woodus.com","www.woodus.com"):raise ValueError("Unexpected redirect")
     html=res.read(3000000).decode("utf-8","replace")
    parser=TableReader();parser.feed(html)
    candidate=[t for t in parser.tables if any("Offspring" in " ".join(r) and "#1" in " ".join(r) for r in t[:3])]
    if not candidate:raise ValueError("No offspring table detected")
    table=candidate[0];count=0
    for line in table:
     if len(line)<5 or line[1]!="=" or line[3]!="+":continue
     child,left,right=line[0].strip(),line[2].strip(),line[4].strip()
     if not child or not left or not right or set(child)=={"-"}:continue
     def classify(value):
      m=re.fullmatch(r"Any\s+([A-Za-z]+)",value,re.I)
      if m:return {"kind":"family","family":m.group(1).lower(),"label":value}
      k=re.sub(r"[^a-z0-9]","",re.sub(r"\s*\+\d+\s*$","",value).lower())
      ident=known.get(k)
      return {"kind":"monster" if ident else "unresolved","id":ident,"label":value}
     output=classify(child);a1=classify(left);a2=classify(right)
     item={"family":family,"source":url,"offspring":output,"parent1":a1,"parent2":a2,"raw_cells":line,"verified":False}
     rows.append(item);count+=1
     if any(v["kind"]=="unresolved" for v in (output,a1,a2)):unmatched.append(item)
    family_stats[family]={"parsed_rows":count,"source":url}
   except Exception as exc:
    family_stats[family]={"error":str(exc),"source":url}
   time.sleep(3)
  document={"game":game,"record_type":"breeding_chart_rows","verified":False,
    "warning":"Unverified chart transcription. Family parents, level modifiers, alternative lines and precedence require review before enabling calculator.",
    "families":family_stats,"rows":rows,"unresolved_count":len(unmatched),
    "unresolved_samples":unmatched[:100]}
  out=Path(f"data/woodus/{game}-breeding-rows.json")
  out.write_text(json.dumps(document,indent=2,ensure_ascii=False)+"\n")
  print(game,len(rows),"rows",len(unmatched),"unresolved",sum("error" in x for x in family_stats.values()),"family errors",flush=True)
if __name__=="__main__":main()
