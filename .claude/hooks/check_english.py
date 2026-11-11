"""PostToolUse hook: reject Vietnamese text written into project files.

Reads the hook payload from stdin, scans the written file for characters
specific to Vietnamese, and exits with code 2 (feedback to Claude) if any
are found. Files outside the project directory are ignored.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path

# Characters that are (almost) exclusive to Vietnamese: ă đ ơ ư and the
# tone-marked vowels in the Latin Extended Additional block (U+1EA0–U+1EF9).
VIETNAMESE_RE = re.compile(r"[ăđơưĂĐƠƯẠ-ỹ]")

# Project-relative glob patterns (forward slashes) that may contain Vietnamese.
EXCLUDED_PATTERNS: list[str] = []

MAX_REPORTED_LINES = 10
MAX_FILE_BYTES = 2_000_000


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    file_path = tool_input.get("file_path") or tool_response.get("filePath")
    if not file_path:
        return 0

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    path = Path(file_path).resolve()
    try:
        rel_path = path.relative_to(project_dir).as_posix()
    except ValueError:
        return 0  # Outside the project (e.g. memory, scratchpad).

    if any(fnmatch.fnmatch(rel_path, pattern) for pattern in EXCLUDED_PATTERNS):
        return 0
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        return 0

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0  # Binary or unreadable file.

    hits = [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if VIETNAMESE_RE.search(line)
    ]
    if not hits:
        return 0

    lines = "\n".join(f"  line {n}: {content[:120]}" for n, content in hits[:MAX_REPORTED_LINES])
    more = f"\n  ... and {len(hits) - MAX_REPORTED_LINES} more line(s)" if len(hits) > MAX_REPORTED_LINES else ""
    sys.stderr.reconfigure(encoding="utf-8")
    print(
        f"Language rule violation in {rel_path}: files in this repo must be written in English "
        f"(see CLAUDE.md > Language). Vietnamese text found on {len(hits)} line(s):\n"
        f"{lines}{more}\nTranslate these lines to English and rewrite the file.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
