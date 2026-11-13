#!/usr/bin/env python3
"""Import genuine game title logos from Dragon's Den dedicated logo galleries.

Never overwrite approved logos. Never use box art. Missing logos remain text.
"""
import json
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image

BASE = "https://www.woodus.com/den/games/"
GALLERIES = {
    "dqm12": "dqmpsx",
    "caravan": "dqm3gba",
    "joker": "dqm4ds",
    "joker2": "dqm5ds",
    "joker2pro": "dqm5ds",
    "terry3d": "dqm13ds",
    "dqm2-3d": "dqm23ds",
    "joker3": "dqm6",
    "joker3pro": "dqm6",
    "witheredworld": "dqm8",
}
def discover(session, key, page):
    response = session.get(page, timeout=35)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    choices = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        url = urljoin(page, href)
        parsed = urlparse(url)
        if not re.search(r"/gallery/graphics/[^/]+/logo/", parsed.path, re.I):
            continue
        if not re.search(r"\.(png|webp|jpe?g)$", parsed.path, re.I):
            continue
        label = a.get_text(" ", strip=True).lower()
        name = parsed.path.rsplit("/", 1)[-1].lower()
        combined = label + " " + name
        professional = bool(re.search(r"\bpro(fessional)?\b|(?:joker|dqmj)[23][_-]?pro", combined))
        if key in ("joker2pro", "joker3pro") and not professional:
            continue
        if key in ("joker2", "joker3") and professional:
            continue
        if key == "witheredworld" and not ("withered" in combined and ("na" in combined or "english" in combined)):
            continue
        choices.append((label, url))
    choices = list(dict.fromkeys(choices))
    print("CANDIDATES", key, choices, flush=True)
    if len(choices) == 1:
        return choices[0][1]
    # Prefer an explicitly named North American/English version.
    preferred = [url for label, url in choices if re.search(r"\b(na|english|usa)\b", label)]
    if len(preferred) == 1:
        return preferred[0]
    return None

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; DQM-Roster-LogoImporter/3.0)"})
    path = Path("assets/branding/manifest.json")
    manifest = json.loads(path.read_text())
    sources = manifest.setdefault("game_logo_sources", {})
    imported, missing = [], []
    for key, folder in GALLERIES.items():
        if key in manifest["games"]:
            print("KEEP", key, "already has approved artwork", flush=True)
            continue
        page = BASE + folder + "/logos.php"
        try:
            url = discover(session, key, page)
            if not url:
                missing.append(key)
                print("SKIP", key, "no unambiguous logo image", flush=True)
                continue
            r = session.get(url, timeout=50, headers={"Referer": page})
            r.raise_for_status()
            img = Image.open(BytesIO(r.content))
            img.load()
            if img.width < 100 or img.height < 25:
                raise ValueError("image too small")
            if img.width / img.height < 1.2:
                raise ValueError("image is too portrait-shaped; may be cover art")
            output = Path("assets/branding") / key / "logo.webp"
            output.parent.mkdir(parents=True, exist_ok=True)
            img.convert("RGBA").save(output, "WEBP", quality=95, method=6)
            manifest["games"][key] = str(output)
            sources[key] = {"gallery": page, "image_url": url, "source": "Dragon's Den dedicated Logos gallery"}
            imported.append(key)
            print("IMPORTED", key, url, img.size, flush=True)
        except Exception as exc:
            missing.append(key)
            print("FAILED", key, repr(exc), flush=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("SUMMARY imported:", imported, "missing:", missing, flush=True)
    if missing:
        print("WARNING: Some logos were unavailable. Text titles remain; see reasons above.", flush=True)
    if not imported:
        raise SystemExit("No new logos imported. Inspect CANDIDATES/FAILED lines above.")

if __name__ == "__main__":
    main()
