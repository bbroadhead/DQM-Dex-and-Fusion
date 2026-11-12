#!/usr/bin/env python3
"""Import monster-family membership from Woodus family detail pages.
Uses existing downloaded monster sprites as representative family icons.
No additional image downloads. Unmatched names are reported, not guessed.
"""
import json,re,time
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
GAMES={"dwm1gbc":["beast","bird","boss","bug","devil","dragon","material","plant","slime","zombie"],"dwm2gbc":["beast","bird","boss","bug","devil","dragon","material","plant","slime","water","zombie"]}
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.names=[]
 def handle_starttag(self,tag,attrs):
  if tag!="img":return
  a=dict(attrs);label=a.get("alt","")
  if label.lower().startswith("monster sprite:"):self.names.append(label.split(":",1)[1].strip())
def norm(s):return re.sub(r"[^a-z0-9]","",s.lower())
def main():
 branding_path=Path("assets/branding/manifest.json");branding=json.loads(branding_path.read_text())
 report={}
 for game,families in GAMES.items():
  path=Path(f"data/woodus/{game}-monsters.json");data=json.loads(path.read_text())
  image_report=json.loads(Path(f"data/woodus/{game}-image-report.json").read_text())
  byname={}
  for m in data["monsters"]:byname.setdefault(norm(m["name"]),[]).append(m)
  assignments={};unmatched=[];errors=[];icons={}
  for fam in families:
   url=f"https://www.woodus.com/den/games/{game}/family-details.php?fam={fam}"
   try:
    with urlopen(Request(url,headers={"User-Agent":"PersonalDQMResearch/0.1"}),timeout=30) as res:
     if urlsplit(res.geturl()).hostname not in ("www.woodus.com","woodus.com"):raise ValueError("Unexpected redirect")
     html=res.read(2000000).decode("utf-8","replace")
    parser=Parser();parser.feed(html)
    matches=[]
    for name in parser.names:
     found=byname.get(norm(name),[])
     if len(found)!=1:
      unmatched.append({"family":fam,"name":name,"matches":len(found)});continue
     mid=found[0]["id"]
     if mid in assignments and assignments[mid]!=fam:errors.append({"id":mid,"families":[assignments[mid],fam]});continue
     assignments[mid]=fam;matches.append(mid)
    # Representative family artwork is an existing sprite, not a bespoke family emblem.
    for mid in matches:
     image=image_report.get("images",{}).get(mid,{}).get("local_path")
     if image and Path(image).is_file():icons[fam]=image;break
   except Exception as exc:errors.append({"family":fam,"error":str(exc)})
   time.sleep(3)
  for m in data["monsters"]:
   if m["id"] in assignments:m["family"]=assignments[m["id"]].title()
  path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
  branding.setdefault("families",{})[game]=icons
  report[game]={"assigned":len(assignments),"total":len(data["monsters"]),"family_icons":list(icons),"unmatched":unmatched,"errors":errors}
 branding_path.write_text(json.dumps(branding,indent=2)+"\n")
 Path("data/woodus/family-import-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({g:{"assigned":v["assigned"],"total":v["total"],"icons":len(v["family_icons"]),"errors":len(v["errors"])} for g,v in report.items()}))
if __name__=="__main__":main()
