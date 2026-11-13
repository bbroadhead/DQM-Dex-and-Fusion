#!/usr/bin/env python3
"""Import actual game title logos (not covers or box art) from Dragon Quest Wiki.

DWM1 and DWM2 are intentionally untouched. For other games, only MediaWiki
files with 'logo' in the filename and game-specific matching tokens qualify.
When no matching logo can be established, retain the text title instead.
"""
import json
import re
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import urljoin

API = "https://dragon-quest.org/w/api.php"
SEARCHES = {
    "dqm12": (["DQM 1 2 logo", "Dragon Quest Monsters 1 2 logo"], [["dqm", "1", "2"], ["monsters", "1", "2"]]),
    "caravan": (["DQMCH logo", "Caravan Heart logo"], [["dqmch"], ["caravan", "heart"]]),
    "joker": (["DQMJ logo", "Dragon Quest Monsters Joker logo"], [["dqmj"], ["monsters", "joker"]]),
    "joker2": (["DQMJ2 logo", "Dragon Quest Monsters Joker 2 logo"], [["dqmj2"], ["joker", "2"]]),
    "joker2pro": (["DQMJ2 Pro logo", "Joker 2 Professional logo"], [["dqmj2", "pro"], ["joker", "2", "professional"]]),
    "terry3d": (["Terry Wonderland 3D logo", "DQM Terry 3D logo"], [["terry", "3d"], ["wonderland", "3d"]]),
    "dqm2-3d": (["DQM2 3DS logo", "Iru Luca logo"], [["dqm2", "3ds"], ["iru", "luca"]]),
    "joker3": (["DQMJ3 logo", "Dragon Quest Monsters Joker 3 logo"], [["dqmj3"], ["joker", "3"]]),
    "joker3pro": (["DQMJ3 Pro Logo", "Joker 3 Professional logo"], [["dqmj3", "pro"], ["joker", "3", "professional"]]),
    "darkprince": (["DQM3 Logo", "Dark Prince logo"], [["dqm3"], ["dark", "prince"]]),
    "witheredworld": (["The Withered World logo", "DQM The Withered World logo"], [["withered", "world"]]),
}
# Dedicated logos gallery: unlike the series overview, these pages show logos, not covers.
WOODUS_LOGOS = {
    "dqm12": "https://www.woodus.com/den/games/dqmpsx/logos.php",
    "caravan": "https://www.woodus.com/den/games/dqm3gba/logos.php",
    "joker": "https://www.woodus.com/den/games/dqm4ds/logos.php",
    "joker2": "https://www.woodus.com/den/games/dqm5ds/logos.php",
    "joker2pro": "https://www.woodus.com/den/games/dqm5ds/logos.php",
    "terry3d": "https://www.woodus.com/den/games/dqm13ds/logos.php",
    "dqm2-3d": "https://www.woodus.com/den/games/dqm23ds/logos.php",
    "joker3": "https://www.woodus.com/den/games/dqm6/logos.php",
    "joker3pro": "https://www.woodus.com/den/games/dqm6/logos.php",
    "witheredworld": "https://www.woodus.com/den/games/dqm8/logos.php",
}
EXACT_FILES = {
    "darkprince": "File:DQM3 Logo.png",
}
BAD = ("box", "cover", "japan", "pack", "case", "artwork", "poster", "banner", "screenshot", "wallpaper")
def words(s):
    return re.findall(r"[a-z0-9]+", s.lower())
def valid(key, title):
    stem = title.removeprefix("File:").rsplit(".", 1)[0].lower()
    tokens = words(stem)
    if "logo" not in tokens or any(x in tokens for x in BAD):
        return False
    # Do not mix Professional and standard editions, or Joker sequel numbers.
    if key in ("joker", "joker2", "joker3") and (any(x in tokens for x in ("pro", "professional")) or any(x in stem for x in ("dqmj2pro","dqmj3pro"))):
        return False
    if key == "joker" and (any(x in tokens for x in ("2", "3")) or any("dqmj"+n in stem for n in ("2","3"))):
        return False
    if key == "joker2" and ("3" in tokens or "dqmj3" in stem):
        return False
    if key == "joker3" and ("2" in tokens or "dqmj2" in stem):
        return False
    return any(all(part in stem for part in option) for option in SEARCHES[key][1])
def api(session, params):
    r = session.get(API, params={"format":"json", **params}, timeout=40)
    r.raise_for_status()
    data = r.json()
    if "error" in data: raise ValueError(data["error"])
    return data
def candidates(session, key):
    results = []
    if key in EXACT_FILES: results.append(EXACT_FILES[key])
    for phrase in SEARCHES[key][0]:
        data = api(session, {"action":"query","list":"search","srnamespace":6,"srsearch":phrase,"srlimit":40})
        results.extend(x["title"] for x in data.get("query",{}).get("search",[]))
    return list(dict.fromkeys(t for t in results if valid(key,t)))
def woodus_logo(session,key):
    page=WOODUS_LOGOS.get(key)
    if not page: return None
    try:
        response=session.get(page,timeout=35)
        response.raise_for_status()
        soup=BeautifulSoup(response.text,"html.parser")
        choices=[]
        for anchor in soup.select('a[href]'):
            href=anchor.get("href","")
            if "/gallery/graphics/" not in href or "/logo/" not in href: continue
            label=anchor.get_text(" ",strip=True).lower()
            full=urljoin(page,href)
            if key=="witheredworld" and not ("withered world" in label and ("na" in label or "english" in label)): continue
            if key=="joker2pro" and "pro" not in label and "pro" not in href.lower(): continue
            if key=="joker3pro" and "pro" not in label and "pro" not in href.lower(): continue
            if key=="joker2" and ("pro" in label or "pro" in href.lower()): continue
            if key=="joker3" and ("pro" in label or "pro" in href.lower()): continue
            choices.append((label,full))
        choices=list(dict.fromkeys(choices))
        if len(choices)==1: return choices[0][1]
        print("WOODUS ambiguous/missing",key,choices[:12])
    except Exception as exc:
        print("WOODUS unavailable",key,str(exc))
    return None

def main():
    session=requests.Session()
    session.headers.update({"User-Agent":"DQM-Roster-LogoImporter/2.0 (GitHub Actions; sourcing game logo art)"})
    path=Path("assets/branding/manifest.json")
    manifest=json.loads(path.read_text())
    sources=manifest.setdefault("game_logo_sources",{})
    imported=[];missing=[]
    for key in SEARCHES:
        if key in ("joker3", "joker3pro"):
            print("SKIP", key, "prior source visually confirmed to contain box art; awaiting vetted clean logo")
            missing.append(key)
            continue
        try:
            direct=woodus_logo(session,key)
            found=[] if direct else candidates(session,key)
            if len(found)!=1:
                # Exact known logo file wins over ambiguous search results.
                exact=EXACT_FILES.get(key)
                if exact in found: found=[exact]
            if len(found)!=1:
                print("SKIP",key,"ambiguous or missing actual logo files:",found)
                missing.append(key);continue
            title=found[0]
            data=api(session,{"action":"query","prop":"imageinfo","iiprop":"url|mime|size","titles":title})
            pages=list(data["query"]["pages"].values())
            info=pages[0].get("imageinfo",[])
            if not info: raise ValueError("No image info")
            item=info[0]
            if not item["mime"].startswith("image/"): raise ValueError("Not an image")
            image_response=session.get(item["url"],timeout=50)
            image_response.raise_for_status()
            pic=Image.open(BytesIO(image_response.content))
            pic.load()
            if pic.width<90 or pic.height<25: raise ValueError("Too small")
            if pic.width / pic.height < 1.35: raise ValueError("Likely portrait box art, not a horizontal logo")
            output=Path("assets/branding")/key/"logo.webp"
            output.parent.mkdir(parents=True,exist_ok=True)
            pic.convert("RGBA").save(output,"WEBP",quality=95,method=6)
            manifest["games"][key]=str(output)
            sources[key]={"file":title,"image_url":image_url,"source":WOODUS_LOGOS[key] if direct else "Dragon Quest Wiki: title logo image"}
            imported.append(key)
            print("IMPORTED",key,title,pic.size)
        except Exception as exc:
            print("FAILED",key,str(exc))
            missing.append(key)
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print("Imported:",imported)
    print("Missing (will display text titles):",missing)
    if not imported: print("No new logos imported; existing artwork remains unchanged")
if __name__=="__main__":
    main()
