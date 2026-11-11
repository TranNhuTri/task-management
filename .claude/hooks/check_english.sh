#!/bin/sh
# Launcher for check_english.py.
#
# Claude Code runs hooks on the host machine, never inside Docker, so a
# Python interpreter must be installed on the host. If none is usable, fail
# loudly (exit 2) instead of letting the language check be skipped silently.

HOOK_DIR=$(dirname "$0")
MIN_VERSION_CHECK='import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'

# "python3" or "python" may be the Microsoft Store stub on Windows; running a
# real version check filters it out.
for candidate in python3 python py; do
    if "$candidate" -c "$MIN_VERSION_CHECK" >/dev/null 2>&1; then
        exec "$candidate" "$HOOK_DIR/check_english.py"
    fi
done

cat >&2 <<'EOF'
Hook error: the English-only language check was NOT run for this file.
No usable Python 3.8+ interpreter was found on the host PATH (tried: python3, python, py).
Hooks run on the host machine, not inside Docker, so running the project with Docker does not help.
Fix: install Python 3.8+ on the host and make sure it is on PATH (see README.md > Claude Code hooks).
Tell the user about this problem, and manually make sure the file you just wrote contains no Vietnamese text.
EOF
exit 2
