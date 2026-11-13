#!/usr/bin/env python3
"""Import genuine game-title artwork from explicit Dragon Quest Wiki file pages.

Approved logos are immutable. Reject portrait box art and ambiguous sources.
Unresolved games keep their text-only title buttons.
"""
import json
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image

API = "https://dragon-quest.org/w/api.php"
FILES = {
    "caravan": "File:DQMCH_Logo.png",
    "joker": "File:DQMJ_Logo.png",
    "joker2": "File:DQMJ2_Logo.png",
    "terry3d": "File:DQM_Terrys_Wonderland_3D_Logo.png",
    "dqm2-3d": "File:DQM2_3DS_Logo.png",
    "joker3": "File:DQMJ3_Logo.png",
    "joker3pro": "File:DQMJ3_Pro_Logo.png",
}
# These have LaunchBox clear-logo listings but no independently verified direct
# image URL. Do not download their box covers as a substitute.
UNRESOLVED = ("dqm12", "joker2pro")

def file_url(session, title):
    response = session.get(API, params={
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|mime", "titles": title, "redirects": "1",
    }, timeout=35)
    response.raise_for_status()
    pages = response.json()["query"]["pages"]
    page = next(iter(pages.values()))
    info = page.get("imageinfo")
    if not info:
        raise ValueError("Wiki file not found or imageinfo unavailable: " + title)
    url = info[0]["url"]
    if not url.startswith("https://dragon-quest.org/"):
        raise ValueError("Unexpected image host: " + url)
    return url

def validate(image, title):
    width, height = image.size
    if width < 120 or height < 30 or width / height < 1.25:
        raise ValueError(f"Not a wide title logo: {title} ({width}x{height})")
    if width / height > 8:
        raise ValueError(f"Suspiciously thin image: {title}")
    # A transparent title graphic is much less likely to be box art.
    rgba = image.convert("RGBA")
    extrema = rgba.getchannel("A").getextrema()
    if extrema[0] == 255:
        raise ValueError(f"Opaque image; requires manual logo-vs-box-art review: {title}")
    return rgba

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "DQM-Dex-LogoImporter/4.0 (game title artwork)"})
    path = Path("assets/branding/manifest.json")
    manifest = json.loads(path.read_text())
    sources = manifest.setdefault("game_logo_sources", {})
    imported, missing = [], []
    for key, title in FILES.items():
        if key in manifest["games"]:
            print("KEEP", key, "already has approved artwork", flush=True)
            continue
        try:
            url = file_url(session, title)
            result = session.get(url, timeout=50, headers={
                "Referer": "https://dragon-quest.org/wiki/" + title
            })
            result.raise_for_status()
            img = Image.open(BytesIO(result.content))
            img.load()
            rgba = validate(img, title)
            output = Path("assets/branding") / key / "logo.webp"
            output.parent.mkdir(parents=True, exist_ok=True)
            rgba.save(output, "WEBP", quality=95, method=6)
            manifest["games"][key] = str(output)
            sources[key] = {
                "gallery": "https://dragon-quest.org/wiki/" + title,
                "image_url": url,
                "source": "Dragon Quest Wiki dedicated file page; transparency and proportions validated",
            }
            imported.append(key)
            print("IMPORTED", key, url, img.size, flush=True)
        except Exception as exc:
            missing.append(key)
            print("SKIP", key, repr(exc), flush=True)
    for key in UNRESOLVED:
        if key not in manifest["games"]:
            missing.append(key)
            print("SKIP", key, "no independently verified direct clear-logo image URL", flush=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("SUMMARY imported:", imported, "missing:", missing, flush=True)
    if missing:
        print("WARNING: Missing games retain text titles; never substitute box art.", flush=True)

if __name__ == "__main__":
    main()
