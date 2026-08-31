"""Read explicitly supplied local credentials; never log or copy their values."""
from __future__ import annotations

import os
import re
from pathlib import Path


def load_credentials(path: Path) -> dict:
    if path.stat().st_size > 16384:
        raise ValueError("credential file too large")
    text = path.read_text(encoding="utf-8-sig")
    values = {}
    for line in text.splitlines():
        # New provider keys may contain dot-delimited segments; never truncate.
        matches = re.findall(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_.-]+", line)
        if not matches:
            continue
        qwen = bool(re.search(r"qwen|dashscope|bailian|百炼|通义|千问", line, re.I))
        deepseek = bool(re.search(r"deepseek|深度求索", line, re.I))
        if len(matches) != 1 or qwen == deepseek:
            raise ValueError("ambiguous credential labels; values suppressed")
        name = "DASHSCOPE_API_KEY" if qwen else "DEEPSEEK_API_KEY"
        if name in values:
            raise ValueError("duplicate credential labels; values suppressed")
        values[name] = matches[0]
    if not values:
        raise ValueError("no labeled credentials found")
    urls = re.findall(r"https?://[^\s\"'<>]+", text)
    regions = set()
    for url in urls:
        if url.rstrip("/") == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1":
            regions.add("singapore")
        elif url.rstrip("/") == "https://dashscope.aliyuncs.com/compatible-mode/v1":
            regions.add("beijing")
        else:
            raise ValueError("unrecognized endpoint; do not send credentials")
    if "DASHSCOPE_API_KEY" in values:
        if len(regions) != 1:
            raise ValueError("Qwen requires one explicit verified regional base URL")
        values["INTENTCOMPASS_QWEN_REGION"] = regions.pop()
    os.environ.update(values)
    return {"qwen_present": "DASHSCOPE_API_KEY" in values, "deepseek_present": "DEEPSEEK_API_KEY" in values, "qwen_region": values.get("INTENTCOMPASS_QWEN_REGION")}
