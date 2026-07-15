#!/bin/bash
# macOS: double-click this in Finder (first run may need right-click > Open
# to get past Gatekeeper's unsigned-script warning).
# Linux: run with `bash install.command` or `./install.command`.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PYCMD=python3
elif command -v python >/dev/null 2>&1; then
    PYCMD=python
else
    echo "Python was not found."
    echo "Install it via Homebrew (brew install python3) or from https://www.python.org/downloads/"
    read -p "Press Enter to close..."
    exit 1
fi

"$PYCMD" "$DIR/install.py"
read -p "Press Enter to close..."
