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
print("Caravan Heart browser syntax and key UI invariants OK")
