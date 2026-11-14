#!/usr/bin/env python3
"""Regression: Woodus PS1 HTML leaves monster <tr> elements unclosed."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from import_dqm12ps1 import Parser
sample='''<table><thead><tr><th>Image</th><th>Name</th><th>Japanese Name</th></tr></thead><tbody>
<tr><td><img src="one.webp"></td><td><a href="monsters-details.php?mid=1">1EyeClown</a></td><td>ひとつめピエロ</td>
<tr><td><img src="two.webp"></td><td><a href="monsters-details.php?mid=2">Zoma</a></td><td>ゾーマ</td>
</tbody></table>'''
p=Parser();p.feed(sample);p.close()
assert len(p.rows)==3,p.rows
assert [row[0][1] for row in p.rows[1:]]==["1EyeClown","Zoma"],p.rows
assert [row[1][0] for row in p.rows[1:]]==["one.webp","two.webp"],p.rows
print("PS1 malformed-row parser regression passed")
