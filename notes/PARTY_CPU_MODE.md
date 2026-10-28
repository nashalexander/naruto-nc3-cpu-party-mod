# Native Party Mode CPU work

Requested behavior: Party Mode > Squad Leader presents an Add CPU button;
one human plus at least one CPU can continue without a wireless guest. After
choosing P1, the same console chooses a character for every CPU slot. This is
the native Party implementation. The complete flow and a three-CPU round now
work from a cold boot.
Release: `dist/nc3-party-cpu-prototype.zip`; instructions: `dist/PARTY_CPU_README.md`.

## Recovered interfaces

- Squad-leader lobby tick: **0x02061164**, object phase at +0x0C. Phase 2 is the
  host lobby; 4 the member lobby; 5/7/8 perform fade/profile/config handshakes.
  The supplied host object is 0x0218E7BC (dynamic allocation, not a fixed address).
- Live lobby input read: 0x0206197C, reached from cached input 0x020C3382.
  Trace: `workbench/captures/party-lobby-input-reads/events.json` and DTCM dumps.
- Multiplayer player-count query: **0x020207C8**, popcount of halfword
  **0x020C3488**. The native Start gate at 0x02061C74 requires count > 1.
- Local slot/count/session globals: **0x020C6264**, **0x020C626C**,
  **0x020C6274** respectively. Lobby-to-settings uses these before the native
  session configuration call **0x0204814C**.
- Game packet exchange: **0x02020738**; participant packet lookup:
  **0x0200FA7C**; lobby/name data lookup: **0x020205F0**.
  Normal packet manager is 0x020C4B20; receive buffer 0x020C3720.
- Multiplayer fighter loop: **0x0202D5BC**, distinct from the mission loop.
  At **0x0202D97C** it calls human preparation 0x0202866C; at
  **0x0202D990** it calls the shared fighter update 0x020293C4.
  This supplies a candidate CPU-dispatch hook while retaining Party combat.
- Names use fixed-width text renderer **0x0207B18C**; main text renderer
  0x0207B100. These consume Shift-JIS pairs. Lobby name conversion is separate
  because wireless profile names are UTF-16.

Reached functions are exported under `workbench/decompiled/`. The mistakenly
named `dispatch_candidate.c` starts inside a function and must not be used as
an authoritative function map; `mission_fighter_tick.c` uses the actual entry
0x0203F3D4. Other `*_candidate.c` exports are exploratory only.

## Injection workbench

`scripts/build_party_cpu.py` compiles `scripts/party_cpu/mod.c` for ARM946E-S
with local system Clang/LLD. It emits original-instruction trampolines, validates
the original ROM SHA-256, and records each hook's original/replacement bytes.
The working ROM remains under `workbench/party-mode/build/`. The release BPS
is `dist/nc3-party-cpu.bps`, applied directly to the unchanged USA ROM. The
bundle includes source, build metadata and runtime validation, without ROMs or saves.

The executable payload is copied to **0x023D0000** by a stack-free startup shim.
The SDK main-arena high limit at literal **0x02005B3C** is reduced from 0x023E0000
to 0x023D0000, reserving 64 KiB for code/state. ARM9's expanded raw image is
relocated into checked blank ROM space at 0x03400000. The temporary bootstrap
source remains below the SDK static-BSS end 0x020D4E00; startup copies it before
normal BSS clearing. Header ARM9 offset/size, used-ROM size and CRC are rebuilt.
Original ARM7 and filesystem file mappings remain unchanged.

## Implemented behavior

Eleven ARM9 hooks provide the lobby button, local participant count/names, packet
exchange, sequential character selection, default CPU technique confirmation,
CPU preparation, selector rendering and mode cleanup. The native rules,
stage/time menus, actor creation, shared fighter update, damage, results and
rematch remain in use.

Future slots are initialized to native grid cell 6 on page 0 (empty character
36), with selector phase 255 suspended until their turn. The native conflict
filter expects only 36 character entries: the wrapper temporarily redirects its
two literal pointers (0x02066DA4 and 0x020683C8) to a 37-entry copy whose empty
entry is 255. It restores both pointers on return, preserving the adjacent
preview-resource table. Completed choices keep native uniqueness rules; future
slots reserve no fighter. On handoff, the next slot starts on an available
unlocked fighter and its own grid cursor moves to that position.

The guarded preview renderer hook at 0x0204D660 hides only future slots' portraits,
idle fighters and cursors immediately before native rendering. It sets the
shared confirmation pointer X from the active slot's actual Yes/No field (104
for No, 32 for Yes), after native input/animation changes. The handoff also
resets the shared message sprite to native sequence 1,
"Use this character?", instead of leaving sequence 5 (waiting for other players).
Removing the old unconditional write to UI+0x3DF preserves P1's confirmed idle
fighter.

The selector temporarily sets the logical local slot only while processing the
current character grid. P1 confirms first, then CPU 1 through CPU 3. Completed
slots keep their own pages/cursors and confirmation state. The logical local
slot is restored to zero after each selector call. Native unlock and duplicate
character rules remain. CPU technique confirmation pulses Start so transitions
cannot swallow the only press; P1 technique selection stays interactive.

At 0x0202D97C, P1 retains human preparation; the added slots use native CPU
preparation at 0x0203AC78 with original AI resource 0x8C, entry 16 (60 bytes).
The adapter skips the mission-only configuration guard. The hook at 0x0203AEE4
also bypasses mission-only profile handling for local CPUs. Each CPU targets
the nearest live other actor explicitly: the mission automatic-target path has
a 256-pixel activation radius that leaves distant Party spawns idle. CPUs share
a basic AI profile, without character-specific tuning or a difficulty selector.
CPU action packets contain no human held keys during combat.

State occupies 440 bytes at 0x023DF000. Returning to Mode Select clears active
CPU mode and count. Leaving/re-entering the lobby permits starting over with
fewer CPUs; there is no remove-CPU control. Wireless Join artwork/wording and
the native End Game disconnect banner remain; Start exits that banner normally.
Mixed wireless-human/CPU sessions are unsupported.

## Validation

Final target SHA-256:
`7d136eecf654d65d51e98034b39398d04716f8362852d2d5dc87cd7462a692db`.

The `v2-cold-release-*` captures in `workbench/party-mode/` exercise the exact build
from boot, without state loads, RAM probes or hotloading during that flow:

- Empty Squad Leader lobby; add CPU 1, 2 and 3; Start without a wireless peer.
- Battle Royale, Bamboo Grove, native selected time 60.
- All future CPU portraits/cursors are blank and reserve no character.
- P1 can reach confirmation for former CPU defaults 3, 32 and 35, declining
  each through the native No choice before the normal test roster.
- Independently choose Naruto, Sasuke, Sakura and Shikamaru in order.
- No and Yes each align with the pointer for all four slots; one Left press
  selects Yes, and confirmed idle fighters persist across all handoffs.
- CPUs finish default techniques while P1 remains interactive.
- Four native actors, CPU pursuit/attacks and naturally changing health for all.
- Complete timed round and native four-fighter rankings.
- Play Again reconstructs all four fighters at full health.
- End Game returns to Mode Select and clears CPU state.

The `v2-single-release-*` captures replay the exact build's empty lobby through a
one-CPU Shikamaru/Naruto match and native results. This replay uses a state made
by the patched ROM itself; it is separate from the no-state-load cold test.
Earlier research captures and hotloader tooling are not the release proof.
Player attacks and natural CPU damage were also exercised in earlier runtime
captures. Actor +0x38 remains unclassified; it is not evidence for stock counts.

`scripts/record_party_validation.py` checks capture consistency, original input
integrity, all hooks installed after cold boot, AI profile/targets, damage,
results/rematch/exit and the cold-test control audit. The report is
`dist/party-cpu-runtime-validation.json`. `scripts/package_party_cpu.py` creates
a BPS delta, independently applies it, compares the entire resulting ROM and
checks every bundled file checksum. Other Party rules and the full roster/stage
matrix are not exhaustively tested. Delta compatibility needs device testing.
