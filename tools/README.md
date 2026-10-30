# Emulator and analysis tools

Applying the release patch only requires a BPS patcher. Building the ROM uses
Python and the host LLVM toolchain; see the [build guide](../docs/BUILDING.md).
The tools below support emulator testing and reverse engineering.

## Emulator setup

Run the appropriate bootstrap script from the repository root:

```sh
bash scripts/bootstrap_melonds.sh
# Or, for the version used in recorded Party tests:
bash scripts/bootstrap_legacy.sh
```

The scripts build melonDS 1.1 and 0.9.5 respectively, and require host build
dependencies. Consult each script for the build options and dependency checks.
`melonDS-debug.toml` provides the debugger configuration template.

| Path | Used for |
| --- | --- |
| `build/melonDS-0.9.5/melonDS` | Recorded Party CPU tests and legacy state support |
| `build/flips/flips` | BPS patch creation and application |
| `python/` | Python dependencies for emulator control helpers |
| `ghidra_12.2_PUBLIC/`, `jdk-25.0.5+8/` | Paths expected by the Ghidra launcher |

The bootstrap scripts set up the emulators; other tools in this table need
separate installation. `scripts/run_melonds.sh` launches the baseline research
ROM. To test a patch, open the patched ROM explicitly in the emulator.

## Capture and debugger helpers

The optional frontend control shims are implemented in `scripts/NC3Control.h`
and `scripts/NC3LegacyControl.h`, with corresponding installer scripts. They
support controlled input and frame captures. Authored frontend patches are in
`reference/nc3-frontend-control.patch` and `reference/nc3-legacy-control.patch`.

Upstream source references are listed in [reference/sources.json](reference/sources.json).
See the [debugger baseline](../notes/PHASE1_LIVE_BASELINE.md) and
[multiplayer findings](../notes/PHASE2_MULTIPLAYER.md) for version-specific limits.
