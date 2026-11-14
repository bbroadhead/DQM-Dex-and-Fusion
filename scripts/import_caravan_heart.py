#!/usr/bin/env python3
"""Import Caravan Heart monster roster and original sprites from Woodus.
Run in GitHub Actions in batches. This does NOT invent breeding recipes:
Caravan Heart uses monster hearts and a different evolution system.
"""
import argparse, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

GAME="dqm3gba"
SOURCE="https://www.woodus.com/den/games/dqm3gba/monsters.php"
ROOT=Path("data/woodus")
ASSETS=Path("assets/monsters/dqm3gba")
def slug(s):
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
def get(session,url):
    r=session.get(url,timeout=35)
    r.raise_for_status()
    if urlparse(r.url).hostname not in ("woodus.com","www.woodus.com"):
        raise ValueError("Unexpected source host")
    return r
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--batch-size",type=int,default=50)
    args=ap.parse_args()
    if not 1<=args.batch_size<=50: ap.error("Batch size must be 1-50")
    ROOT.mkdir(parents=True,exist_ok=True)
    ASSETS.mkdir(parents=True,exist_ok=True)
    session=requests.Session()
    session.headers["User-Agent"]="DQM-Private-Roster-Importer/1.0"
    soup=BeautifulSoup(get(session,SOURCE).text,"html.parser")
    rows=[]
    for tr in soup.select("tr"):
        links=[a for a in tr.select("a[href]") if "monsters-detail" in a["href"] or "monsters-detail" in a["href"].replace("details","detail")]
        if not links:
            links=[a for a in tr.select("a[href]") if "monsters-details.php" in a["href"]]
        if not links:continue
        a=links[0]
        name=a.get_text(" ",strip=True)
        if not name:continue
        image=tr.find("img")
        img_url=urljoin(SOURCE,image.get("src","")) if image else ""
        cells=tr.find_all("td")
        japanese=cells[-1].get_text(" ",strip=True) if len(cells)>2 else ""
        rows.append({"name":name,"japanese_name":japanese,"detail_url":urljoin(SOURCE,a["href"]),"image_url":img_url})
    if len(rows)<150:
        raise RuntimeError(f"Only {len(rows)} rows discovered: refusing to overwrite roster; inspect Woodus markup")
    records=[]
    used=set()
    for i,item in enumerate(rows):
        key=slug(item["name"])
        if key in used:key+=f"-{i+1}"
        used.add(key)
        records.append({"id":GAME+":"+key,"name":item["name"],"family":None,"metadata_status":"pending_verification","source_url":item["detail_url"],"image_url":item["image_url"]})
    details_path=ROOT/(GAME+"-details.json")
    details_path.write_text(json.dumps({"game":GAME,"records":records,"source":SOURCE,"note":"Woodus monster list; Japanese names, rank, family and in-game numbering require separate verification."},ensure_ascii=False,indent=2)+"\n")
    (ROOT/(GAME+"-monsters.json")).write_text(json.dumps({"game":GAME,"monsters":[{"id":m["id"],"name":m["name"],"family":m["family"],"image_url":m["image_url"]} for m in records]},ensure_ascii=False,indent=2)+"\n")
    report_path=ROOT/(GAME+"-image-report.json")
    report=json.loads(report_path.read_text()) if report_path.exists() else {"images":{}}
    mapping=report.get("images",{})
    attempted=0
    for m in records:
        ident=m["id"]
        existing=mapping.get(ident,{}).get("local_path")
        if existing and Path(existing).is_file():continue
        if attempted>=args.batch_size:break
        attempted+=1
        url=m["image_url"]
        p=urlparse(url)
        if p.hostname not in ("woodus.com","www.woodus.com") or not p.path.startswith("/den/gallery/graphics/"):
            print("SKIP untrusted image",m["name"],url,flush=True);continue
        try:
            r=get(session,url)
            mime=r.headers.get("Content-Type","").split(";")[0].lower()
            ext={"image/webp":"webp","image/png":"png","image/gif":"gif","image/jpeg":"jpg"}.get(mime)
            data=r.content
            if not ext or not 10<len(data)<3_000_000:raise ValueError("Invalid image content")
            signature={"webp":b"RIFF","png":b"\x89PNG","gif":b"GIF8","jpg":b"\xff\xd8"}[ext]
            if not data.startswith(signature):raise ValueError("Image signature mismatch")
            dest=ASSETS/(ident.split(":",1)[1]+"."+ext)
            dest.write_bytes(data)
            mapping[ident]={"local_path":dest.as_posix(),"source_url":url}
            print("IMPORTED",m["name"],flush=True)
        except Exception as e:
            print("FAILED",m["name"],str(e)[:180],flush=True)
        time.sleep(1)
    report.update({"game":GAME,"total":len(records),"downloaded_total":sum(bool(x.get("local_path") and Path(x["local_path"]).is_file()) for x in mapping.values()),"images":mapping,"source":SOURCE})
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("SUMMARY",len(records),"monsters,",report["downloaded_total"],"images stored")
if __name__=="__main__":main()
