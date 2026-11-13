#!/usr/bin/env python3
"""Extract official DWM2 family symbols from the supplied original manual.
Source: Woodus Cobi's Journey manual, PDF page 19 / printed page 17.
Only touches assets/branding/families/official/ and branding manifest.
"""
import hashlib,json,sys
from pathlib import Path
import fitz
from PIL import Image,ImageDraw

EXPECTED="72c5a15e138ae31a18c9e7655f9cd1f59865fbf02cbe0fbdc8cb0cb9e6458c2d"
SOURCE=Path(sys.argv[1])
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,"Unexpected PDF version: aborting instead of cropping wrong artwork"
doc=fitz.open(SOURCE)
page=doc[18]
pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
im=Image.frombytes("RGB",[pix.width,pix.height],pix.samples).convert("RGBA")
assert abs(im.width-646)<=2 and abs(im.height-470)<=2,f"Unexpected page size: {im.size}"
centers={"slime":(74,183),"plant":(272,183),"material":(469,183),
"dragon":(74,247),"bug":(272,247),"water":(469,247),
"bird":(74,309),"devil":(272,309),"boss":(469,309),
"beast":(74,374),"zombie":(272,374)}
out=Path("assets/branding/families/official")
out.mkdir(parents=True,exist_ok=True)
for name,(x,y) in centers.items():
 crop=im.crop((x-29,y-29,x+29,y+29))
 mask=Image.new("L",(58,58),0)
 ImageDraw.Draw(mask).ellipse((2,2,55,55),fill=255)
 crop.putalpha(mask)
 crop.save(out/f"{name}.png",optimize=True)
manifest_path=Path("assets/branding/manifest.json")
manifest=json.loads(manifest_path.read_text())
for game,entries in manifest["families"].items():
 for family in entries:
  assert family in centers,f"Missing official symbol: {family}"
  entries[family]=f"assets/branding/families/official/{family}.png"
manifest["family_icon_source"]="Dragon Warrior Monsters 2: Cobi's Journey instruction booklet, printed page 17 (PDF page 19). Boss uses the manual's ??? family emblem."
manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
print("Extracted",len(centers),"official family emblems. Monster images unchanged.")
