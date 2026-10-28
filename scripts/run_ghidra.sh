#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export JAVA_HOME="$project_dir/tools/jdk-25.0.5+8"
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p workbench/runtime/ghidra-home workbench/ghidra
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:+$JAVA_TOOL_OPTIONS }-Duser.home=$project_dir/workbench/runtime/ghidra-home"
if [[ "${1:-}" == --headless ]]; then
    shift
    exec "$project_dir/tools/ghidra_12.2_PUBLIC/support/analyzeHeadless" "$@"
fi
exec "$project_dir/tools/ghidra_12.2_PUBLIC/ghidraRun" "$@"
