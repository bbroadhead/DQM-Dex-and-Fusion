#!/usr/bin/env python3
"""Import authentic game-logo images from the Dragon Quest Wiki series gallery.

Only accepts gallery items with an exact title caption. Never substitutes box art
or generic series graphics. Leaves missing logos untouched and reports them.
"""
import json
import re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

PAGE = "https://dragon-quest.org/wiki/Dragon_Quest_Monsters_(series)"
TARGETS = {
    "dqm12": ["Dragon Quest Monsters 1+2", "Dragon Quest Monsters 1·2"],
    "caravan": ["Dragon Quest Monsters: Caravan Heart"],
    "joker": ["Dragon Quest Monsters: Joker"],
    "joker2": ["Dragon Quest Monsters: Joker 2"],
    "joker2pro": ["Dragon Quest Monsters: Joker 2 Professional"],
    "terry3d": ["Dragon Quest Monsters: Terry's Wonderland 3D"],
    "dqm2-3d": ["Dragon Quest Monsters 2: Iru and Luca’s Marvelous Mysterious Key", "Dragon Quest Monsters 2: Iru and Luca's Marvelous Mysterious Key"],
    "joker3": ["Dragon Quest Monsters: Joker 3"],
    "joker3pro": ["Dragon Quest Monsters: Joker 3 Professional"],
    "darkprince": ["Dragon Quest Monsters: The Dark Prince"],
}
def normalize(s):
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("·", "+")).strip().casefold()

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "DQM-Roster-LogoImporter/1.0 (GitHub Actions; image provenance: Dragon Quest Wiki)"})
    response = session.get(PAGE, timeout=40)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    galleries = []
    for item in soup.select("li.gallerybox, div.gallerybox"):
        caption = item.select_one(".gallerytext")
        img = item.select_one("img")
        if caption and img:
            title = caption.get_text(" ", strip=True)
            galleries.append((normalize(title), img))
    print("Gallery items:", len(galleries))
    manifest_path = Path("assets/branding/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    provenance = manifest.setdefault("game_logo_sources", {})
    success, missing = [], []
    for key, titles in TARGETS.items():
        matches = [(title, img) for title, img in galleries if title in {normalize(t) for t in titles}]
        if len(matches) != 1:
            print("SKIP", key, "matching gallery captions:", len(matches))
            missing.append(key)
            continue
        title, img = matches[0]
        src = img.get("src") or img.get("data-src")
        if not src:
            missing.append(key)
            continue
        url = urljoin(PAGE, src)
        try:
            res = session.get(url, timeout=45)
            res.raise_for_status()
            picture = Image.open(BytesIO(res.content))
            picture.load()
            if picture.width < 90 or picture.height < 25:
                raise ValueError("Image is unexpectedly small")
            if picture.width / picture.height > 12:
                raise ValueError("Image aspect ratio implausible")
            output = Path("assets/branding") / key / "logo.webp"
            output.parent.mkdir(parents=True, exist_ok=True)
            picture.convert("RGBA").save(output, "WEBP", quality=95, method=6)
            manifest["games"][key] = str(output)
            provenance[key] = {"gallery": PAGE, "caption": title, "image_url": url}
            success.append(key)
            print("IMPORTED", key, picture.size, url)
        except Exception as exc:
            missing.append(key)
            print("FAILED", key, str(exc))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("Imported:", success)
    print("Missing:", missing)
    if not success:
        raise SystemExit("No logos imported; check wiki gallery markup/network and captions")

if __name__ == "__main__":
    main()
