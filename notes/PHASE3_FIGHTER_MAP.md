# Verified mission fighter map — 2026-10-26

This map is for the original AN4E ROM, SHA-256
`6ca0d8af595730515acd591cbee3879a6c5ebaf6889422d375b1c841a832d5cc`.
Findings combine controlled frame captures, original-byte-asserted RAM probes,
native hardware watchpoints on the emulator's backing RAM, and the emulated
ARM9 registers/instruction at each write. These recovered native AI and actor
interfaces support the [Party CPU implementation](PARTY_CPU_MODE.md).

## Actor state and copies

The tested Naruto-versus-Kiba mission has two main fighter-state pointers:

| Location | Observed meaning | P1 | CPU |
|---|---|---|---|
| `0x020CDD60`, four pointer slots | Persistent/source state pointers | `0x021E7E18` | `0x021E7F5C` |
| `0x020CDD70`, four pointer slots | Simulation working-state pointers | `0x021E80A0` | `0x021E81E4` |
| `0x020C7F3C`, four pointer slots | Another persistent-state pointer table | `0x021E7E18` | `0x021E7F5C` |
| `0x020C82DC` | Staging state records, copied with size `0x134` | P1 record | CPU follows at `+0x134` |

The live allocation addresses above are scene-specific. Resolve the pointer
tables after initialization; do not assume they are permanent actor addresses.
Observed heap spacing `0x144` is not proof of a fixed actor-array stride. The
copy routines explicitly copy **`0x134` bytes per record**.

The first words are **not character IDs**: CPU offset 0 changes autonomously
from `0x14` to `0x03` during the same Kiba encounter. Their exact meaning is not
yet classified. The prior `CELL`-archive lead is not used as fighter state.

| Offset from state pointer | Finding | Evidence / limits |
|---|---|---|
| `+0x20`, 32-bit | Action/state selector | P1 idle `0`, Right `9`, Left `6`; CPU preparation writes `0`, `8`, `0x1A` and other states. |
| `+0x24`, byte | Facing candidate | `1` while walking right, `2` left; read in directional movement code. Not independently frozen. |
| `+0x4C`, signed 32-bit | X, Q12 (`4096` units/pixel) | P1 and Kiba individually displaced horizontally; persistent source-buffer edits survive subsequent frames. |
| `+0x50`, signed 32-bit | Y, Q12 | Kiba independently moved up by 64 pixels. Grounded Naruto is around Y=768 in this stage. |
| `+0x30`, signed 32-bit | Current HP, Q12 | Natural CPU hits reduce Naruto from 150 to 144; half-value probes reduce gauges; zero CPU HP triggers Finished and then mission failure. |
| `+0x28` | Maximum/initial HP, Q12 | Constructor reads the stat preset, shifts by 12 and copies this field to current HP +0x30. Natural damage changes only current HP. |
| `+0x2C`, `+0x34` | Maximum/initial and current chakra, Q12 | Constructor initializes both from the resource stat preset. Consumption behavior still needs a controlled test. |
| `+0x1D`, byte | Actor slot | Constructor assigns its slot argument. |
| `+0x1E`, byte | Character ID | Constructor stores character argument; Naruto=0, playable Sasuke=1, mission Kiba=32. |
| `+0x1F`, byte | Animation/state | Independent from the action selector at +0x20. |
| `+0xDC`, byte | AI target selector | 4 selects nearest; 0 targets P1. Initialized by mission data. |
| `+0xDD`, 60 bytes | AI weighted action table | Constructor copies resource group 0x8C's selected profile. |

Repeated idle4 captures from an identical baseline have **zero differing bytes**
across the full 4 MiB main RAM. Left/right samples at 4/8 frames narrowed movement
to 18 symmetric candidates. The true source-state X is at P1 pointer `+0x4C`;
writing only working X `0x021E80EC` shifts the current rendered pass but is
overwritten. Writing source X `0x021E7E64` persists. This distinction was checked
over 2 and 5 frames, not inferred from a single screenshot.

`scripts/capture_mission.py` replays the idle/walking experiment. The optional
legacy frontend shim requires a fully paused emulation thread for dumps/probes,
and every probe requires matching original bytes. No ROM bytes are written.

## Input and control dispatch

| Address | Verified role / preconditions |
|---|---|
| `0x0201F0D8` | **Literal data**, value `0x04000130` (KEYINPUT), not an instruction. The previously tentative lead is now tied to the live cached-input writer. |
| Around `0x0201F098–0x0201F0CC` | Reads KEYINPUT and the additional-key shadow at `0x027FFFA8`, combines/inverts/masks with `0x2FFF`, then calls the input-cache helper. |
| `0x0201EFC4` | Input cache helper: R0=cache pointer, R1=active-high keys. Live stores at `0x0201EFC8` and `0x0201EFD8`; immediate caller is `0x0201F0CC`, LR=`0x0201F0D0`. |
| `0x020C3380`, 16-bit | Active-high held input cache: idle `0`, Right `0x10`, Left `0x20`. |
| `0x020C3382`, 16-bit | Newly pressed bits: helper computes new held bits AND NOT previous held bits. Live Right press sets `0x10`, subsequent held frame clears it. |
| `0x0202866C` | Player control preparation. R0=working fighter, R1=`0x020C3380` input context, R2=source fighter. Live store at `0x02028E6C` sets action 9 for Right; release store at `0x02029240` restores action 0. |
| `0x0203AC54` | CPU preparation. R0=working pointer table (`0x020CDD70` here), R1=CPU slot index (`1`). Live CPU action writes at `0x0203AE34`, `0x0203ADF4`, `0x0203B25C`, `0x0203B164`. |
| `0x020293C4` | Common fighter update. R0=working fighter state, R1=working pointer table. Both player and CPU paths are live-confirmed callers. |

The reached dispatcher differentiates index zero and nonzero slots:

```text
P1:  0203F6D8 -> 0202866C (prepare player action)
     0203F6E4 -> 020293C4 (common fighter update)
CPU: 0203F6F4 -> 0203AC54 (prepare CPU action)
     0203F734 -> 020293C4 (common fighter update)
```

This is live mission dispatch evidence. The later multiplayer dispatch hook is documented in the
[Party CPU notes](PARTY_CPU_MODE.md).

## Coordinate writers and validated callers

Right movement writes at **`0x0202B1D8: strne r0, [r6, #0x4C]`**, preceded by an
addition of `0x2000` (2 pixels). On the observed hit R6=`0x021E80A0`, R0=`0x5D000`,
and destination=`0x021E80EC` (91 -> 93 pixels). The left branch stores at
`0x0202B1D0` after subtracting `0x2000`.

Native ARM9 R15 was `0x0202B1E0`; subtracting the ARM pipeline offset 8 gives the
executed store. The RAM opcode matches serialized `CurInstr=0x1586004C`.
The native call stack identifies ARM9Write32 -> DataWrite32 -> A_STR_IMM.

Raw LR=`0x02025320` at this point is a stale subcall return, **not** the caller of
the whole fighter update. The valid saved return is in ARM9 DTCM:

- DTCM base=`0x027C0000`, SP=`0x027C3AD0`.
- Saved return at SP+`0x2C`=`0x0203F6E8`.
- The preceding instruction `0x0203F6E4` is `bl 0x020293C4`.

For CPU action preparation, a watchpoint at working `+0x20` records the store at
`0x0203AE34`; its DTCM saved return is `0x0203F6F8`, validating the actual
`bl 0x0203AC54` at `0x0203F6F4`. CPU X movement at `0x0202CCA8` has saved return
`0x0203F738`, validating the common-update call at `0x0203F734`.

The stack lives in DTCM, not the main-RAM mirror at the same virtual range. Main
RAM alone does not contain these saved return addresses.

The X writes propagate in this observed order for four successive walking frames:

1. Working state X changes in the fighter update.
2. Staging X at `0x020C8328` is written by copy code `0x02006A18`, with LR
   `0x0202F2D0` (copy call at `0x0202F2CC`).
3. Source X at `0x021E7E64` is written by the same copy code, with LR
   `0x0203A598` (copy call at `0x0203A594`).

Copy helper `0x02006924` takes **R0=source, R1=destination, R2=length**; do not
assume the libc memcpy argument order. Both reached callers use length `0x134`.

The watchpoint script is `scripts/trace_coordinate_writes.py`; it logs bounded
events and matching opcodes.

## Battle-end objective recovery

Setting Kiba's current HP to zero triggers Finished, but the mission then reports
**Failed** with "Some techniques should be done up close!". The selected mission
requires an Uzumaki Barrage finish. This mission-specific objective makes the
encounter unsuitable as a general versus battle. Subsequent resource traces identified a generic knockout goal,
but the released CPU patch uses native Party battles instead. See the
[Party implementation](PARTY_CPU_MODE.md) for the active design.
