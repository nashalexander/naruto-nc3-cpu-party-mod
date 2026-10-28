#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export NC3_CONTROL_PATH="$project_dir/workbench/runtime/control.json"
python3 - <<'PY'
from pathlib import Path
p = Path('tools/build/melonDS-1.1/portable/melonDS.toml')
backup = p.with_suffix('.toml.before-capture')
if p.exists() and not backup.exists(): backup.write_bytes(p.read_bytes())
text = Path('tools/melonDS-debug.toml').read_text()
text = text.replace('[Instance0.Gdb]\nEnabled = true', '[Instance0.Gdb]\nEnabled = false')
p.write_text(text)
PY
exec bash scripts/run_melonds.sh "$@"
