#!/usr/bin/env python3
"""
Lightweight helpers for the diagnostics runner.

Provides:
- time_block(name): context manager for timing
- ok()/fail()/skip(): result builders
- write_report_md()/write_report_json(): output writers
- copy_artifact(src, dst_dir): artifact copier that returns relative path
"""
import contextlib
import json
import os
import shutil
import sys
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple


@contextlib.contextmanager
def time_block(name: str):
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        print(f"[TIME] {name}: {duration:.3f}s")


def _base(name: str, status: str, details: str = "", evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "details": details,
        "evidence": evidence or {},
    }


def ok(name: str, details: str = "", evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base(name, "PASS", details, evidence)


def fail(name: str, details: str = "", evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base(name, "FAIL", details, evidence)


def skip(name: str, details: str = "", evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base(name, "SKIP", details, evidence)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def copy_artifact(src: str, dst_dir: str) -> str:
    ensure_dir(dst_dir)
    basename = os.path.basename(src)
    dst = os.path.join(dst_dir, basename)
    shutil.copy2(src, dst)
    return dst


def _status_counts(results: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    p = sum(1 for r in results if r.get("status") == "PASS")
    f = sum(1 for r in results if r.get("status") == "FAIL")
    s = sum(1 for r in results if r.get("status") == "SKIP")
    return p, f, s


def write_report_json(data: Dict[str, Any], path: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _format_table(rows: List[Tuple[str, str, str]]) -> str:
    # rows: [(name, status, details)]
    header = "| Check | Status | Details |\n|---|---|---|\n"
    body = "\n".join(f"| {n} | {s} | {d} |" for n, s, d in rows)
    return header + body + "\n"


def write_report_md(data: Dict[str, Any], path: str) -> None:
    ensure_dir(os.path.dirname(path))
    results = data.get("results", [])
    p, f, s = _status_counts(results)
    rows = [(r.get("name", ""), r.get("status", ""), (r.get("details") or "").replace("\n", "<br>")) for r in results]
    lines: List[str] = []
    lines.append(f"### CryBB Diagnostics Report")
    lines.append("")
    lines.append(f"- **timestamp**: {data.get('timestamp')}")
    if data.get("git_sha"):
        lines.append(f"- **git_sha**: {data.get('git_sha')}")
    lines.append(f"- **mode**: {data.get('mode')}")
    lines.append("")
    lines.append(f"- **summary**: PASS={p} FAIL={f} SKIP={s}")
    lines.append("")
    lines.append(_format_table(rows))
    artifacts = data.get("artifacts", []) or []
    if artifacts:
        lines.append("### Artifacts")
        for a in artifacts:
            rel = a.get("path")
            label = a.get("label") or os.path.basename(rel or "")
            if rel:
                lines.append(f"- [{label}]({rel})")
    content = "\n".join(lines) + "\n"
    with open(path, "w") as f:
        f.write(content)


def console_table(results: List[Dict[str, Any]]) -> str:
    # simple monospaced table for console
    name_w = max(5, max(len(r.get("name", "")) for r in results))
    status_w = 6
    lines = [f"{'CHECK'.ljust(name_w)}  STATUS  DETAILS"]
    for r in results:
        n = r.get("name", "").ljust(name_w)
        s = r.get("status", "").ljust(status_w)
        d = (r.get("details") or "").replace("\n", " ")
        lines.append(f"{n}  {s}  {d}")
    return "\n".join(lines)



