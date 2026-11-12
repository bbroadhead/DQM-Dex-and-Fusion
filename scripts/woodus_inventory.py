#!/usr/bin/env python3
"""Small, conservative Woodus page inventory. Does not download images."""
import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SOURCES = {
    "dwm1gbc": "https://www.woodus.com/den/games/dwm1gbc/monsters.php",
    "dwm2gbc": "https://www.woodus.com/den/games/dwm2gbc/monsters.php",
}
class InventoryParser(HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.images = []
        self.links = []
        self.anchor = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and attrs.get("src"):
            self.images.append({"src": urljoin(self.base, attrs["src"]), "alt": attrs.get("alt", "").strip()})
        if tag == "a" and attrs.get("href"):
            self.anchor = {"url": urljoin(self.base, attrs["href"]), "text": ""}
    def handle_data(self, data):
        if self.anchor is not None:
            self.anchor["text"] += data
    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            self.anchor["text"] = re.sub(r"\\s+", " ", self.anchor["text"]).strip()
            self.links.append(self.anchor)
            self.anchor = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=["dwm1gbc", "dwm2gbc", "all"], default="all")
    args = parser.parse_args()
    output = Path("woodus-output")
    output.mkdir(exist_ok=True)
    games = list(SOURCES) if args.game == "all" else [args.game]
    for i, game in enumerate(games):
        url = SOURCES[game]
        request = Request(url, headers={"User-Agent": "PersonalDQMResearch/0.1 (manual one-shot inventory)"})
        with urlopen(request, timeout=30) as response:
            final_url = response.geturl()
            if urlparse(final_url).hostname not in ("www.woodus.com", "woodus.com"):
                raise RuntimeError("Unexpected redirect host")
            html = response.read(5_000_000).decode("utf-8", errors="replace")
        parsed = InventoryParser(final_url)
        parsed.feed(html)
        data = {"game": game, "source": final_url, "image_references": parsed.images,
                "links": parsed.links, "note": "Unverified page inventory; not normalized monster records."}
        (output / (game + "-inventory.json")).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{game}: {len(parsed.images)} image references, {len(parsed.links)} links")
        if i < len(games) - 1:
            time.sleep(3)
if __name__ == "__main__":
    main()
