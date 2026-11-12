#!/usr/bin/env python3
"""Discover and download specifically labeled Woodus game logos/family icons.
No filename guessing; only explicit HTML image alt/title labels qualify.
Use locally for research; check permission before public redistribution.
"""
import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

BASE = "https://www.woodus.com/den/games/"
FAMILIES = ("beast","bird","boss","bug","devil","dragon","material","plant","slime","zombie")
MAX_BYTES = 3_000_000
MIMES = {"image/png": ("png", b"\x89PNG"), "image/webp": ("webp", b"RIFF"),
         "image/jpeg": ("jpg", b"\xff\xd8"), "image/gif": ("gif", b"GIF8")}

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img": return
        a = dict(attrs)
        self.images.append({"src": a.get("src", ""), "label": " ".join((a.get("alt",""),a.get("title",""))) .strip()})

def request(url):
    p = urlsplit(url)
    if p.scheme != "https" or p.hostname not in ("woodus.com", "www.woodus.com"):
        raise ValueError("Untrusted source URL")
    req = Request(url, headers={"User-Agent":"PersonalDQMResearch/0.1 (manual research asset import)"})
    with urlopen(req, timeout=30) as response:
        dest = urlsplit(response.geturl())
        if dest.hostname not in ("woodus.com","www.woodus.com"): raise ValueError("Untrusted redirect")
        content = response.read(MAX_BYTES + 1)
        if len(content)>MAX_BYTES: raise ValueError("Image too large")
        return content, response.headers.get("Content-Type","").split(";")[0].lower()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--game", choices=["all","dwm1gbc","dwm2gbc"], default="all")
    args=ap.parse_args()
    games=["dwm1gbc","dwm2gbc"] if args.game=="all" else [args.game]
    path=Path("assets/branding/manifest.json")
    manifest=json.loads(path.read_text())
    report={"discovered":[],"imported":[],"skipped":[],"errors":[]}
    for game in games:
        for section in ("","families.php"):
            page=BASE+game+"/"+section
            try:
                data,_=request(page)
                parser=Images()
                parser.feed(data.decode("utf-8",errors="replace"))
            except Exception as exc:
                report["errors"].append({"page":page,"error":str(exc)})
                continue
            for entry in parser.images:
                label=entry["label"].lower()
                family=next((f for f in FAMILIES if re.search(r"\b"+f+r"\s+famil(?:y|ies)\b",label)),None)
                is_logo=bool(re.search(r"\blogo\b",label)) and ("dragon" in label or "monster" in label)
                if not family and not is_logo: continue
                source=urljoin(page,entry["src"])
                target_key="family:"+family if family else "logo"
                report["discovered"].append({"game":game,"kind":target_key,"url":source,"label":entry["label"]})
                if family and manifest["families"].setdefault(game,{}).get(family):continue
                site_id={"dwm1gbc":"dwm","dwm2gbc":"dwm2"}[game]
                if is_logo and manifest["games"].get(site_id):continue
                try:
                    binary,mime=request(source)
                    if mime not in MIMES:raise ValueError("Unsupported image type "+mime)
                    ext,sig=MIMES[mime]
                    if not binary.startswith(sig):raise ValueError("Invalid image signature")
                    if ext=="webp" and binary[8:12]!=b"WEBP":raise ValueError("Invalid WebP")
                    output=Path("assets/branding")/game/(("family-"+family) if family else "logo")
                    output=output.with_suffix("."+ext)
                    output.parent.mkdir(parents=True,exist_ok=True)
                    output.write_bytes(binary)
                    if family:manifest["families"][game][family]=output.as_posix()
                    else:manifest["games"][site_id]=output.as_posix()
                    report["imported"].append({"game":game,"kind":target_key,"path":output.as_posix(),"source":source})
                except Exception as exc:
                    report["errors"].append({"game":game,"kind":target_key,"url":source,"error":str(exc)})
                finally:time.sleep(3)
            time.sleep(3)
    path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    Path("data/woodus/branding-import-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:len(v) for k,v in report.items()}))
if __name__=="__main__":main()
