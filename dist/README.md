# Party CPU release files

Apply [nc3-party-cpu.bps](nc3-party-cpu.bps) to the original USA ROM.
The [patching and play guide](PARTY_CPU_README.md) contains checksums,
instructions, save handling, and known limitations.

| File | Purpose |
| --- | --- |
| `nc3-party-cpu.bps` | BPS patch for the original USA ROM |
| `party-cpu-build.json` | Build metadata, hook bytes, and source hashes |
| `party-cpu-runtime-validation.json` | Recorded checks and validation scope |
| `party-cpu-checksums.sha256` | Checksums using release-bundle paths |

In the bundle, `README.md` is the play guide (`PARTY_CPU_README.md` here).
Source paths in the checksum manifest are relative to the bundle root.
