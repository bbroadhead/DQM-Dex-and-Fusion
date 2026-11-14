#!/usr/bin/env python3
"""Static checks for Caravan Heart's browser UI and reform controls."""
from pathlib import Path
import re
import subprocess
import tempfile

html=Path("index.html").read_text(encoding="utf-8")
scripts=re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.S|re.I)
if not scripts:raise SystemExit("No inline JavaScript found")
with tempfile.TemporaryDirectory() as tmp:
    for i,source in enumerate(scripts):
        path=Path(tmp)/f"inline-{i}.js"
        path.write_text(source,encoding="utf-8")
        subprocess.run(["node","--check",str(path)],check=True)
for needle in (
    'monsterOptions("",true)',
    'm.family||families.get(m.id)||""',
    'm.obtainable===false',
    'id="showUnobtainable"',
    'const resultStars=',
    'const resultId=resultStars?',
    'const chartUnresolved=',
    'target.obtainable===false',
    'Unobtainable</span>',
):
    if needle not in html:raise SystemExit(f"Missing Caravan UI feature: {needle}")
block=html[html.index("function renderCaravanReform()"):html.index("function renderFusionPanel()")]
if block.index("const resultStars=")>block.index("const resultId=resultStars?"):
    raise SystemExit("Reform star result used before initialization")
import json

details=json.loads(Path("data/woodus/dqm3gba-details.json").read_text(encoding="utf-8"))["records"]
general=json.loads(Path("data/woodus/dqm3gba-reform-general.json").read_text(encoding="utf-8"))
obtainable={m["id"]:m for m in details if m.get("obtainable") is not False}
assert len(obtainable)==200, f"Expected 200 obtainable monsters; got {len(obtainable)}"
assert all(m.get("family") in ("Beast","Demon","Material","Animal","Slime","Nature","Elemental") for m in obtainable.values())
assert sum(m.get("obtainable") is False for m in details)==21
for star,rows in general["stars"].items():
    for influence,columns in rows.items():
        for dominant,result in columns.items():
            if result is not None:
                assert result in obtainable, f"Unobtainable or missing chart result: {star}/{influence}/{dominant}: {result}"
assert len(general["unmatched"])==1
assert general["unmatched"][0]["source_name"]=="Star Fish"

print("Caravan Heart browser syntax, roster, reform-chart and UI invariants OK")
