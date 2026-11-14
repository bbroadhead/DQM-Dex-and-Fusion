#!/usr/bin/env python3
"""Import PS1 DQM 1+2 roster and battle artwork from Woodus. No GBC substitutions."""
import json,re,time,html,urllib.request,urllib.parse
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
BASE="https://www.woodus.com/den/games/dqm1_2psx/"
USER_AGENT="DQM-Dex-and-Fusion/1.0 (personal fan reference; source attributed)"
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=35) as response:return response.read()
def slug(name):
    name=re.sub(r"\s*\((\d+)\)",r"-\1",name)
    return re.sub(r"[^a-z0-9]+","-",name.lower()).strip("-")
class Parser(HTMLParser):
    """Woodus omits closing </tr> tags: flush each row at the next <tr>."""
    def __init__(self):
        super().__init__()
        self.in_row=False;self.in_cell=False;self.cell=[];self.cells=[]
        self.rows=[];self.images=[];self.links=[];self.current_link=None
    def finish_cell(self):
        if self.in_cell:
            self.cells.append(html.unescape("".join(self.cell)).strip())
            self.in_cell=False;self.cell=[]
    def finish_row(self):
        self.finish_cell()
        if self.in_row and len(self.cells)>=3:
            self.rows.append((self.cells,self.images,self.links))
        self.in_row=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="tr":
            self.finish_row()
            self.in_row=True;self.cells=[];self.images=[];self.links=[]
        elif tag in ("td","th") and self.in_row:
            self.finish_cell();self.in_cell=True;self.cell=[]
        elif tag=="img" and self.in_row:
            self.images.append(a.get("src",""))
        elif tag=="a" and self.in_row:
            self.current_link=a.get("href","")
    def handle_data(self,data):
        if self.in_cell:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.in_row:
            if self.current_link:self.links.append(self.current_link)
            self.current_link=None
        elif tag in ("td","th"):
            self.finish_cell()
        elif tag=="tr":
            self.finish_row()
        elif tag in ("tbody","table"):
            self.finish_row()
    def close(self):
        super().close();self.finish_row()

def main():
    page=BASE+"monsters.php"
    raw=get(page);page_html=raw.decode("utf-8","replace")
    diagnostic=ROOT/"import-diagnostics";diagnostic.mkdir(exist_ok=True)
    (diagnostic/"woodus-ps1-roster.html").write_text(page_html,encoding="utf-8")
    parser=Parser();parser.feed(page_html);parser.close()
    print(f"Source diagnostics: HTTP response {len(raw)} bytes; {len(parser.rows)} table rows; {page_html.lower().count(chr(60)+chr(116)+chr(114))} <tr tags; first rows: {parser.rows[:3]}",flush=True)
    if not parser.rows:
        print("HTML sample:",repr(page_html[:1800]),flush=True)
    records=[];images={};seen=set()
    for cells,img,links in parser.rows:
        # The roster page exposes names as table text; detail links are optional.
        detail=next((urllib.parse.urljoin(page,x) for x in links if x and "monsters-details.php" in x),None)
        query=urllib.parse.parse_qs(urllib.parse.urlsplit(detail).query) if detail else {}
        name=cells[1].strip()
        japanese=cells[2].strip()
        if not name or not japanese or not re.search(r"[\u3040-\u30ff\u3400-\u9fff]",japanese):continue
        if name.lower() in ("name","monster","japanese name"):continue
        identifier="dqm12ps1:"+slug(name)
        if identifier in seen:continue
        seen.add(identifier)
        record={"id":identifier,"name":name,"japanese_name":japanese,"source_url":detail,"mode_verification":"PS1_collection_only; individual game membership not yet verified","family":None}
        records.append(record)
        image_url=next((urllib.parse.urljoin(page,x) for x in img if "monster" in x.lower() and not any(k in x.lower() for k in ("header","logo"))),None)
        if image_url:
            try:
                data=get(image_url)
                ext=".png" if data.startswith(b"\x89PNG") else ".gif" if data.startswith(b"GIF8") else ".webp" if data.startswith(b"RIFF") else None
                if ext:
                    local=ROOT/"assets/monsters/dqm12ps1"/(slug(name)+ext)
                    local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(data)
                    images[identifier]={"local_path":local.relative_to(ROOT).as_posix(),"source_url":image_url}
            except Exception as e:print("Image skipped:",name,str(e))
            time.sleep(.08)
    (diagnostic/"parse-summary.json").write_text(json.dumps({"url":page,"html_bytes":len(raw),"table_rows":len(parser.rows),"parsed_monsters":len(records),"first_rows":parser.rows[:5],"first_monsters":records[:5]},ensure_ascii=False,indent=2),encoding="utf-8")
    if len(records)<200:raise RuntimeError(f"Only {len(records)} PS1 monsters found; refusing incomplete import. Parsed {len(parser.rows)} table rows. First rows: {parser.rows[:2]}")
    folder=ROOT/"data/woodus";folder.mkdir(parents=True,exist_ok=True)
    (folder/"dqm12ps1-details.json").write_text(json.dumps({"game":"dqm12ps1","record_type":"PS1_collection_source_listed","source":page,"records":records},ensure_ascii=False,indent=2)+"\n")
    (folder/"dqm12ps1-image-report.json").write_text(json.dumps({"images":images,"source":page},ensure_ascii=False,indent=2)+"\n")
    (folder/"dqm12ps1-monsters.json").write_text(json.dumps({"monsters":[{"id":x["id"],"family":x["family"]} for x in records]},indent=2)+"\n")
    print(f"Imported {len(records)} PS1 monsters and {len(images)} images")
if __name__=="__main__":main()
