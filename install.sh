#!/bin/bash
set -euo pipefail

[[ "$(uname -s)" == Darwin ]] || exit 0

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
    echo "chatferry: skipped, uv is not installed (brew install uv)" >&2
    exit 0
fi

echo "Installing chatferry..."
uv tool install --force --quiet --python 3.13 --editable "$src"
echo "chatferry is installed: run chatferry doctor to start"
