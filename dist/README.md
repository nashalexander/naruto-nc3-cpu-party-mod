# NC3 Party CPU patch

Use **`nc3-party-cpu.bps`** for **Party Mode > Squad Leader > + ADD CPU**.
This supports one human plus 1–3 CPUs and lets you choose each CPU character.

From the project root, run:

```sh
tools/build/flips/flips --apply dist/nc3-party-cpu.bps \
  'Naruto - Ninja Council 3 (USA).nds' workbench/build/nc3-party-cpu-applied.nds
sha256sum workbench/build/nc3-party-cpu-applied.nds
```

The output must have SHA-256:

`7d136eecf654d65d51e98034b39398d04716f8362852d2d5dc87cd7462a692db`

Open **`workbench/build/nc3-party-cpu-applied.nds`** explicitly in melonDS.
Boot normally, using a copy of your `.sav` progress file; do not load an old
save state. The research launcher `scripts/run_melonds.sh` opens the original
workbench ROM, so use melonDS's Open ROM command to select this output instead.

[Full play/save/patch instructions](PARTY_CPU_README.md) ·
[Patch bundle](nc3-party-cpu-prototype.zip)

This repository's release artifacts use the native Party method. Apply the
Party patch directly to the original baseline ROM.
