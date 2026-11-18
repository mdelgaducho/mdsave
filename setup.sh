#!/usr/bin/env bash
# MDsave Setup / Installer Wrapper
# Redirige la ejecución al instalador universal install.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/install.sh" "$@"
