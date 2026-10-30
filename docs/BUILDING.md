# Build from source

Run all commands from the repository root. You need Python 3, Clang with ARM
cross-compilation support, LLD, `llvm-nm`, and `llvm-objcopy`.

## Prepare the ROM

Place an original USA ROM in the repository root with this filename:

```text
Naruto - Ninja Council 3 (USA).nds
```

The required ROM is 64 MiB (67,108,864 bytes), game code **AN4E**. Verify it:

```sh
sha256sum --check baseline-rom.sha256
```

Expected SHA-256:

```text
6ca0d8af595730515acd591cbee3879a6c5ebaf6889422d375b1c841a832d5cc
```

## Compile

```sh
python3 scripts/build_party_cpu.py
```

The builder checks the input checksum, compiles the ARM9 payload, installs
hooks, and writes these outputs under `workbench/party-mode/build/`:

- `nc3-party-cpu-research.nds`: patched ROM to open in an emulator.
- `build.json`: build checksum, hook bytes, and symbol metadata.
- `party-cpu.elf` and `payload.bin`: compiled payload and debugging symbols.

Boot the output normally. Save states from a different build restore that
build's code. For play and save instructions, see the
[play guide](../dist/PARTY_CPU_README.md).

## Source map

| Path | Purpose |
| --- | --- |
| `scripts/party_cpu/mod.c` | Lobby, selection, CPU control, and cleanup hooks |
| `scripts/party_cpu/mod.ld` | Payload memory layout |
| `scripts/build_party_cpu.py` | ROM validation, compilation, and hook installation |
| `scripts/nc3_resources.py` | ROM resource parsing |
| `scripts/record_party_validation.py` | Runtime capture validation |
| `scripts/package_party_cpu.py` | BPS creation, round-trip verification, and packaging |

Runtime validation and packaging require emulator captures in the structure
expected by those scripts; compiling the ROM does not require captures.
Release reports describe the builds they identify. A new source build needs
its own playtesting before making equivalent validation claims.

For hook addresses and memory reservations, see the
[implementation notes](../notes/PARTY_CPU_MODE.md). For emulator setup, see the
[tool guide](../tools/README.md).
