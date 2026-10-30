# Native multiplayer findings

An unchanged USA ROM completed a two-player **Battle Royale** round in two
melonDS **0.9.5** processes on one computer. This established a native Party
battle baseline for the [CPU implementation](PARTY_CPU_MODE.md).

## Tested flow

1. Start a fresh host lobby through **Party Mode > Squad Leader**.
2. In a second emulator process using a separate ROM directory, choose
   **Party Mode > Member** and join the host.
3. On the host, choose **Battle Royale > Bamboo Grove > 60 seconds**.
4. Select Naruto on the host and Choji on the guest, confirm characters and
   techniques, then advance past the Objective screen with Start.
5. Allow the timed round to finish. Both instances reached the results screen
   with Naruto first and Choji second.

The local multiplayer backend shares IPC between the two processes. The test
covered joining, setup, independent movement, the countdown, and matching
results. It did not validate damage or actor offsets.

## Save-state compatibility

melonDS 0.9.5 restored legacy format-9 states. Its serializer places a 512-byte
cartridge EEPROM inside `NDCS` at file offset **0x0102874C**.
`scripts/prepare_workbench.py` includes extraction support. Loading a state can
restore its EEPROM as well as runtime memory, so battery-save imports should
be checked after state loads.

## Limits and instrumentation

Screenshots were captured sequentially. The experiment did not produce matched
host/guest RAM snapshots at the same frame.

Two melonDS 1.1 instances were exercised for frontend control and frame stepping,
but this experiment did not attempt a complete wireless match in that version.
It therefore establishes no conclusion about 1.1 networking compatibility.

The multiplayer round used upstream 0.9.5 before adding the optional capture
shim. The later shims in `scripts/NC3Control.h` and `scripts/NC3LegacyControl.h`
provide controlled input and frame stepping. Networking parity for instrumented
builds was not established by this experiment.

For native CPU dispatch and fighter fields, see the
[mission fighter map](PHASE3_FIGHTER_MAP.md).
