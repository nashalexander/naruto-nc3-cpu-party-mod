# ARM9 debugger baseline

These initial observations establish the ARM9 address mapping for the original
USA ROM. For the completed patch, see the [Party CPU notes](PARTY_CPU_MODE.md).

## Configuration

The baseline used melonDS 1.1 with `ENABLE_GDBSTUB=ON`, `ENABLE_JIT=OFF`,
`RelWithDebInfo`, and the Qt6 X11 frontend. GDB connected to TCP port **3333**.
`Gdb.Enabled` belongs inside `Instance0` in the TOML configuration; see
`tools/melonDS-debug.toml`.

For static analysis, import the raw ARM9 into Ghidra with processor
`ARM:LE:32:v5t:default` and base address **0x02000000**. Instruction/data
boundaries require analysis; a successful import alone does not establish them.

## Startup trace

1. Entry PC: **0x02000800**.
2. Breakpoint: **0x02000A78**.
3. LR: **0x02000818**; caller: **0x02000814: bl 0x02000A78**.
4. **0x02000A7C: ldr r1, [pc, #172]** reads **0x02000B30**.
5. After stepping from the callee entry, PC is **0x02000A80** and R1 is
   **0x000F9005**.

The literal maps to original ROM offset **0x4B30**; the load instruction maps
to **0x4A7C**. The trace was reproduced on a second emulator run. This is
startup initialization evidence; fighter dispatch is documented separately in
the [fighter map](PHASE3_FIGHTER_MAP.md).

## Replay

From the repository root, launch the baseline emulator, then run GDB in another
terminal:

```sh
bash scripts/run_melonds.sh
```

```sh
gdb -nx -q -x scripts/arm9_startup_proof.gdb
```

The tested melonDS 1.1 stub failed to reconnect after a debugger disconnect.
Restart the emulator for each new GDB session. The X11 launcher uses
`QT_QPA_PLATFORM=xcb`; targeted XSendEvent input worked in this configuration.

Legacy format-9 save states require compatible emulator support. The
[multiplayer notes](PHASE2_MULTIPLAYER.md) describe testing with melonDS 0.9.5.
