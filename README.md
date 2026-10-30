# Naruto: Ninja Council 3 — Party CPU battles

Add **1–3 CPU opponents** to **Party Mode > Squad Leader** and choose a
character for each player. The patch uses the game's Party battles, stage and
time settings, results screen, and rematch flow.

## Get started

1. Supply an original **Naruto: Ninja Council 3 (USA)** ROM (game code **AN4E**,
   64 MiB).
2. Apply [nc3-party-cpu.bps](dist/nc3-party-cpu.bps) with a BPS patcher.
3. Open the patched ROM and enter **Party Mode > Squad Leader**.
4. Press **DS X** or touch **X ADD CPU** to add opponents, then press **Start**.

See the [patching and play guide](dist/PARTY_CPU_README.md) for ROM checksums,
character selection, saves, and troubleshooting.

## Screenshots

| Add a CPU | Choose CPU characters | Fight three CPUs |
| :---: | :---: | :---: |
| ![Squad Leader lobby with the X ADD CPU label](docs/screenshots/add-cpu.png) | ![Selecting CPU 3 after confirming earlier fighters](docs/screenshots/cpu-character-select.png) | ![Naruto fighting three CPUs in Party Mode](docs/screenshots/cpu-match.png) |

## Status and limitations

Battle Royale rounds with one and three CPUs have been tested. The current
release changes the lobby label; full-round testing was
performed on earlier builds with the same gameplay code. See the
[validation details](notes/PARTY_CPU_MODE.md#validation).

CPUs share basic combat AI. Character unlocks and duplicate-character rules
still apply. Other Party rules and the full character/stage roster have not
been exhaustively tested. Wireless guests alongside CPUs are unsupported.

## Development

- [Build from source](docs/BUILDING.md)
- [Party CPU implementation](notes/PARTY_CPU_MODE.md)
- [Mission fighter and AI reference](notes/PHASE3_FIGHTER_MAP.md)
- [Emulator and analysis tools](tools/README.md)
- [Release files](dist/README.md)
