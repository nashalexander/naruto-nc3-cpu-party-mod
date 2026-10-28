#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
binary="$project_dir/tools/build/melonDS-1.1/melonDS"
if [[ ! -x "$binary" ]]; then
    echo 'melonDS has not been built. Run bash scripts/bootstrap_melonds.sh first.' >&2
    exit 1
fi
# Keep game sidecars away from the original ROM and supplied states.
mkdir -p workbench/rom workbench/captures workbench/runtime/cache workbench/runtime/config workbench/runtime/data
python3 scripts/prepare_workbench.py
if [[ ! -f workbench/rom/nc3.nds ]]; then
    cp --reflink=auto -- 'Naruto - Ninja Council 3 (USA).nds' workbench/rom/nc3.nds
fi
cd workbench/rom
export XDG_CACHE_HOME="$project_dir/workbench/runtime/cache"
export XDG_CONFIG_HOME="$project_dir/workbench/runtime/config"
export XDG_DATA_HOME="$project_dir/workbench/runtime/data"
export QT_QPA_PLATFORM=xcb
exec "$binary" "$project_dir/workbench/rom/nc3.nds" "$@"
