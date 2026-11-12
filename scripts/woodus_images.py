#!/usr/bin/env python3
"""Download a small resumable batch of referenced monster artwork.

For personal research where permitted. Do not publish third-party images
without appropriate permission. No automatic retries for access denial.
"""
import argparse
import json
import mimetypes
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path("data/woodus")
ASSETS = Path("assets/monsters")
ALLOWED = {"webp": b"RIFF", "png": b"\x89PNG", "gif": b"GIF8", "jpg": b"\xff\xd8"}
MIMES = {"image/webp": "webp", "image/png": "png", "image/gif": "gif", "image/jpeg": "jpg"}
MAX_BYTES = 3_000_000

def extension_and_validity(content, content_type):
    media = content_type.split(";", 1)[0].strip().lower()
    extension = MIMES.get(media)
    if not extension:
        raise ValueError(f"Unexpected Content-Type: {media}")
    if not content.startswith(ALLOWED[extension]):
        raise ValueError("Image signature does not match Content-Type")
    if extension == "webp" and content[8:12] != b"WEBP":
        raise ValueError("Invalid WebP signature")
    return extension

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", choices=["all", "dwm1gbc", "dwm2gbc"], default="all")
    ap.add_argument("--batch-size", type=int, default=50)
    args = ap.parse_args()
    if not 1 <= args.batch_size <= 50:
        ap.error("batch size must be 1–50")
    games = ["dwm1gbc", "dwm2gbc"] if args.game == "all" else [args.game]
    for game in games:
        manifest = json.loads((ROOT / f"{game}-monsters.json").read_text(encoding="utf-8"))
        folder = ASSETS / game
        folder.mkdir(parents=True, exist_ok=True)
        report_path = ROOT / f"{game}-image-report.json"
        existing = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        mapping = existing.get("images", {})
        failures = []
        downloaded = 0
        requested = 0
        for monster in manifest["monsters"]:
            ident = monster["id"]
            slug = ident.split(":", 1)[1]
            known = mapping.get(ident)
            if known and (Path(known["local_path"]).is_file()):
                continue
            if requested >= args.batch_size:
                break
            requested += 1
            source = monster["image_url"]
            parts = urlsplit(source)
            if parts.scheme != "https" or parts.hostname not in {"woodus.com", "www.woodus.com"} or not parts.path.startswith(f"/den/gallery/graphics/{game}/monster/"):
                failures.append({"id": ident, "error": "Untrusted image URL"})
                continue
            try:
                req = Request(source, headers={"User-Agent": "PersonalDQMResearch/0.1 (manual artwork import)"})
                with urlopen(req, timeout=30) as response:
                    if urlsplit(response.geturl()).hostname not in {"woodus.com", "www.woodus.com"}:
                        raise ValueError("Unexpected redirect host")
                    data = response.read(MAX_BYTES + 1)
                    if len(data) > MAX_BYTES:
                        raise ValueError("Image exceeds 3MB limit")
                    ext = extension_and_validity(data, response.headers.get("Content-Type", ""))
                destination = folder / f"{slug}.{ext}"
                destination.write_bytes(data)
                mapping[ident] = {"local_path": destination.as_posix(), "source_url": source}
                downloaded += 1
                print(f"{game}: saved {monster['name']} ({downloaded})", flush=True)
            except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
                failures.append({"id": ident, "error": str(exc)[:180]})
                print(f"{game}: failed {monster['name']}: {exc}", flush=True)
                if isinstance(exc, HTTPError) and exc.code in (403, 429):
                    print("Source blocked or rate limited; stopping.", flush=True)
                    break
            finally:
                time.sleep(3)
        report = {"game": game, "total": len(manifest["monsters"]),
                  "downloaded_total": sum(1 for v in mapping.values() if Path(v["local_path"]).is_file()),
                  "new_downloads": downloaded, "failures": failures, "images": mapping,
                  "note": "Private research assets only; verify rights before redistribution."}
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{game}: {report['downloaded_total']}/{report['total']} images stored; {len(failures)} failures")

if __name__ == "__main__":
    main()
