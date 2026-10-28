# Live debugger baseline — 2026-10-26

Network and desktop access succeeded through reviewed commands outside the
default sandbox. No system packages were installed. All new downloads, source,
binaries, settings, working ROM/state copies, and Ghidra project data stay here.

## Tools actually installed and exercised

- melonDS **1.1**, locally built from upstream tag archive with
  `ENABLE_GDBSTUB=ON`, `ENABLE_JIT=OFF`, `RelWithDebInfo`, Qt6, X11 frontend.
- ENet **1.3.18**, locally built and statically linked to satisfy its dependency.
- Existing system GDB, ARM target, connected to local TCP **3333**.
- Ghidra **12.2**, upstream release zip, SHA-256 checked against GitHub's release
  digest. Requires **Java 25**; local Temurin **25.0.5+8** was downloaded and
  checked against Adoptium's package checksum. Java 21 was also downloaded before
  inspecting this release's minimum version; it is unused.
- `python-xlib` **0.33** and `six` **1.17.0**, installed only to `tools/python`.

Download metadata and receipts are in `tools/downloads/`. Ghidra's Java home
and settings are confined by `scripts/run_ghidra.sh`. Successful raw ARM9 import
is recorded in `workbench/captures/ghidra-import.log`; the project is
`workbench/ghidra/NC3.gpr`, program `/arm9.bin`, processor
`ARM:LE:32:v5t:default`, base `0x02000000`. Automatic analysis was deliberately
disabled for this baseline; instruction/data boundaries are not recovered yet.

## G1 evidence

The original game boots using built-in BIOS/firmware. Captures show its publisher
screen, NC3 title, and Data Select screen. Input was successfully sent to the
emulator. A native format-13 save was created at `workbench/rom/nc3.ml1` on Data
Select. This is a fresh game, not an imported supplied state; no supplied state
has been visually validated yet. Native restore was tested with F1 and returned
to Data Select with the emulator's "State loaded from slot 1" confirmation;
see `workbench/captures/native-state-restored.png`.

The continuous debugger session captured:

1. Entry PC **`0x02000800`**.
2. Breakpoint hit inside the live ARM9 at **`0x02000A78`**.
3. **LR `0x02000818`**, with the actual caller instruction
   **`0x02000814: bl 0x02000A78`** inspected in live RAM.
4. **`0x02000A7C: ldr r1, [pc, #172]`** reads **`0x02000B30`**.
   Memory contains **`0x000F9005`**; after two single steps from the callee entry,
   PC is **`0x02000A80`** and **R1 is `0x000F9005`**.
5. The literal matches original ROM offset **`0x4B30`**. The access instruction
   maps to original ROM offset **`0x4A7C`**.

This satisfies G1's reproducible live pause/caller/access proof. It is startup/CP15
initialization evidence, not an actor or AI trace. The replay recipe is
`scripts/arm9_startup_proof.gdb`; the exact sequence was executed interactively,
then replayed successfully by that script on a second fresh emulator run. Both
runs produced the same caller, accessed address, literal value, and post-step PC.

Evidence files:

- `workbench/captures/first-gdb-connection.txt`
- `workbench/captures/arm9-session.log`
- `workbench/captures/mainram-startup-02000a80.bin`
- `workbench/captures/rom-boot.png`
- `workbench/captures/rom-title.png`
- `workbench/captures/main-menu.png` (Data Select)
- `workbench/captures/native-state-restored.png`
- `workbench/rom/nc3.ml1`

## Setup corrections and limits

`Gdb.Enabled` must be inside **`Instance0`**, as shown in the corrected template.
Explicit TOML parent tables avoid a startup serialization exception. The launcher
sets `QT_QPA_PLATFORM=xcb` so the emulator can be operated and captured via X11.
Targeted XSendEvent key events work here; XTest key injection did not reliably
advance the title. The helper restricts itself to visible melonDS windows.

melonDS 1.1's debug stub entered a tight loop reporting `receiving from stream 0`
after the first GDB disconnect. A reconnect attempt failed. The affected project
processes were stopped, the generated repetitive log was reduced to a bounded
excerpt, and a clean emulator was launched. A **single continuous GDB session**
then captured the successful trace. Avoid disconnect/reconnect on the same run;
restart the project emulator for a new client. No emulator source modification
was made. `arm9-startup-call.txt` records the failed reconnect, not proof.

The original ROM and supplied states remain unchanged. There is no gameplay
patch, verified AI dispatch, actor address, or multiplayer result yet. G2 still
requires an actual coordinated two-instance connection experiment. The supplied
format-9 states still need an older importer or fresh scene reproduction in 1.1;
their structural validity does not establish runtime compatibility.

## Commands

```bash
bash scripts/run_melonds.sh
# In another terminal, from this directory, on a fresh emulator startup:
gdb -nx -q -x scripts/arm9_startup_proof.gdb
# Ghidra GUI, with project-local Java and settings:
bash scripts/run_ghidra.sh
```

Desktop/debugger commands require the reviewed execution context; the default
sandbox still denies network and local socket access. The active development
session has demonstrated the reviewed path works.
