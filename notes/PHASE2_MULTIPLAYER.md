# Real multiplayer experiment — 2026-10-26

**G2 passed in melonDS 0.9.5:** an unchanged NC3 ROM completed a two-player
Battle Royale round on one computer. The host controlled Naruto; the guest
controlled Choji. Both reached the same results screen, showing Naruto as the
winner. This establishes that the multiplayer battle engine is available for
comparison. It does not establish a single-console CPU replacement.

## Compatible supplied-state recovery

Locally compiled upstream melonDS 0.9.5 restored all supplied format-9 states:

- `Battle_npc_save.svs`: Naruto in a mission arena, with Kiba as the mission boss.
- `Char_selection_save.svs`: Mission Mode character selection for
  **"Defeat Kiba with an Uzumaki Barrage!"**, stage **Main Battle Arena**,
  unlimited time. This finisher condition matters for reusable versus logic.
- `Mp_squad_lead_save.svs`: wireless squad-leader lobby, player name **Delta**.

Screenshots are `workbench/captures/supplied-*-restored.png`.
Only working copies under `workbench/legacy/` were loaded. Input checksums remain
in `workbench/input_manifest.json`.

The serializer source verifies a 512-byte cartridge EEPROM inside `NDCS` at file
offset **`0x0102874C`**. It is extracted as `battery.sav` per supplied state by
`scripts/prepare_workbench.py`. The battle and selection states have identical
EEPROM hashes; the lobby's EEPROM differs. The recovered save shows 43% mission
completion in a fresh modern guest. Loading an unrelated native state can
restore that state's different EEPROM, so battery import must not be assumed
to persist across all state loads.

## Actual tested route

1. Restored the supplied lobby in the compatible emulator. Backing out produced
   the game's expected disconnect message. Start returned to Mode Select.
2. Saved a native Mode Select state (`workbench/legacy/nc3.ml4`). Selected
   Party Mode, then Squad Leader to create a **fresh** lobby.
3. Launched a second 0.9.5 process using a separate working ROM directory,
   loaded the recovered native Mode Select state, and selected Party Mode > Member.
4. Guest discovered **Delta**. Joining populated the second member slot on both
   screens. Emulator logs identify local MP instances **0** and **1** and MACs
   **00:09:BF:11:22:33** and **00:09:BF:12:66:43**.
5. Host Start > **Battle Royale** > **Bamboo Grove** > **60 seconds**.
   Both selected fighters, confirmed Yes, selected/defaulted secret techniques,
   then Start/Yes to finish technique selection.
6. The Objective screen said **Survive!** for both players. Host Start advanced
   into the actual arena. Naruto and Choji appeared in their respective cameras;
   the countdown advanced from 60 into the twenties. Brief independent movement
   inputs were sent. This experiment did not validate damage or actor offsets.
7. The timed round completed and both displayed **Battle Royale Result** with
   Naruto first and Choji second. No connection failure occurred during the round.

This experiment used two coordinated **0.9.5 processes**, whose local MP backend
shares IPC. Two coordinated **1.1 instances** were also created and their file
controller/frame stepping exercised, but they did **not** complete a wireless
match in this experiment. This is not a demonstrated 1.1 networking failure:
the experiment switched to the compatible restored-menu route before attempting
a connection there.

## Evidence and limits

Screenshots under `workbench/captures/`:

- `legacy-guest-search.png`: discovered host.
- `legacy-host-members.png`, `legacy-guest-joined.png`: connected roster.
- `legacy-match-setup.png`: Battle Royale option.
- `legacy-mp-character-select.png`, `legacy-mp-guest-selected.png`: fighter setup.
- `legacy-mp-live-host.png`, `legacy-mp-live-guest.png`: arena entry.
- `legacy-mp-host-current.png`, `legacy-mp-guest-current.png`: ongoing arena,
  countdown 25/24 at the sequential capture moments.
- `mp-after-movement-host.png`, `mp-after-movement-guest.png`: matching results.

Five **guest-side** native states and their RAM extracts are preserved under
`workbench/multiplayer/`: lobby, character selection, ready/objectives, in battle,
and results. `manifest.json` records checksums and raw register metadata.
**Matched host-side native states are still missing:** host save shortcuts did
not produce files, while guest shortcuts did. Screen captures are sequential,
not simultaneous frame captures. Do not label these as matched host/guest states.
The control instrumentation added afterward will support deliberate captures.

A native-GDB attach to the paused host was denied by Linux ptrace policy
(`ptrace_scope=1`); no global policy was changed. This was an OS denial, not an
automatic approval-review rejection. Next native traces can launch the emulator
as GDB's own child, avoiding a request to weaken the system policy.

## Tooling provenance

The multiplayer round ran under the locally built upstream 0.9.5 emulator before
adding the optional legacy capture shim. The original executable is retained as
`tools/build/melonDS-0.9.5/melonDS-upstream-build`. Build fixes were compiler include
flags and project-local dependencies; they did not modify game code or emulator
simulation source. Sources/downloads/settings remain within this project.

The newer frontend control shim is opt-in through `NC3_CONTROL_PATH`; its source
and installer are in `scripts/NC3Control.h` and `scripts/install_emulator_control.py`.
It uses existing UI APIs and counts completed RunFrame calls. Controlled stepping
checks the counter advanced by exactly one per request. It is an experimental
capture build, and no networking parity with the upstream build is claimed.

The legacy capture shim is separately maintained as `scripts/NC3LegacyControl.h`
and `scripts/install_legacy_control.py`. Both installers retain pristine source
backups and write reviewable diffs under `tools/reference/`. No gameplay patch
has been generated. The next milestone is verified fighter fields and live
writers/controller dispatch, using controlled mission and multiplayer samples.
