# Local tools

Keep downloads, builds and installed tools here so the workbench stays contained
in this directory. Git includes this README, `melonDS-debug.toml`, the two
`reference/nc3-*-control.patch` files and `reference/sources.json`. All other
contents of this directory are ignored, including copied upstream source files.

The existing scripts use these paths:

- `downloads/`: downloaded archives and their metadata.
- `src/`, `build/`, `local/`: extracted source, builds and local dependencies.
- `python/`: locally installed Python dependencies for research helpers.
- `ghidra_12.2_PUBLIC/`, `jdk-25.0.5+8/`: local analysis tool installations.
- `build/flips/flips`: BPS patch creation/application tool.
- `build/melonDS-0.9.5/melonDS`: interpreter used for the recorded Party tests.

`scripts/bootstrap_melonds.sh` and `scripts/bootstrap_legacy.sh` bootstrap the
emulator workbench. They require host build dependencies; they do not install
every tool listed above. Applying an existing BPS only needs a BPS patcher.
Building the Party ROM from source uses host Clang/LLD and LLVM tools instead
of these emulator/analysis installations. Upstream reference URLs are recorded
in [reference/sources.json](reference/sources.json).
