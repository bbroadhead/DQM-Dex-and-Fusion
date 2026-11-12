#!/usr/bin/env python3
"""Regression test: monster detail links with spaces must be valid request URLs."""
import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

spec = importlib.util.spec_from_file_location("woodus_detail_batch", Path("scripts/woodus_detail_batch.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
examples = [
    "https://www.woodus.com/den/games/dwm1gbc/monsters-details.php?mid=248783&mname=Anteater (M1)",
    "https://www.woodus.com/den/games/dwm1gbc/monsters-details.php?mid=1&mname=Foo & Bar",
    "https://www.woodus.com/den/games/dwm1gbc/monsters-details.php?mid=1&mname=Foo%20Bar",
]
for raw in examples:
    encoded = module.normalize_detail_url(raw)
    assert " " not in encoded and "(" not in encoded and ")" not in encoded, encoded
    assert parse_qs(urlsplit(encoded).query)["mid"] == parse_qs(urlsplit(raw).query)["mid"]
assert parse_qs(urlsplit(module.normalize_detail_url(examples[0])).query)["mname"] == ["Anteater (M1)"]
print("Monster detail URL encoding tests passed")
