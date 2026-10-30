# NC3 Party CPU prototype

This build adds local CPU players to **Party Mode > Squad Leader**. It uses the
game's Party battles, character grid, stage/time selection and results screen.
It supports **one human plus 1–3 CPUs** without another DS or wireless guest.

## Play

1. Enter **Party Mode**, then **Squad Leader**.
2. Press **DS X** or touch **X ADD CPU** inside the next empty player box.
   Repeat for more CPUs (three maximum). The label has extra left padding
   and disappears when all three CPU slots are filled.
3. Press **Start** once at least one CPU is present.
4. Choose **Battle Royale**, a stage and a time limit normally.
5. CPU slots begin unassigned and reserve no characters. Choose your character
   and confirm **Yes**. The grid then controls **CPU 1**,
   followed by CPU 2 and CPU 3 if added. The label on the left identifies the
   current CPU. Use the normal grid, touch controls and L/R page buttons.
   The confirmation starts on **No**; press Left once for **Yes**, then A.
6. Confirm each CPU character. CPUs automatically keep and confirm their
   default techniques. Choose P1's techniques normally and finish with Start.
7. Press **Start** on the Objective screen to begin.

After results, Start opens **Play again?**; Yes repeats the match with the same
roster. End Game uses the game's existing disconnect screen; press Start there
to return to Mode Select. Leaving Party Mode clears the added CPUs.

The lobby retains the original wireless wording and Join artwork. **Start works
with the added CPUs; no guest needs to join.** Normal character unlock rules and
the native restriction against duplicate fighters remain. To start over with
fewer CPUs, leave and re-enter Squad Leader.

## Apply the patch

Apply **`nc3-party-cpu.bps` directly to the original USA ROM**.
Expected original SHA-256:

`6ca0d8af595730515acd591cbee3879a6c5ebaf6889422d375b1c841a832d5cc`

With this project's local Flips:

```sh
tools/build/flips/flips --apply dist/nc3-party-cpu.bps \
  'Naruto - Ninja Council 3 (USA).nds' workbench/build/nc3-party-cpu-applied.nds
```

Open **`workbench/build/nc3-party-cpu-applied.nds`** explicitly in melonDS.
Verify the output with:

```sh
sha256sum workbench/build/nc3-party-cpu-applied.nds
```

Expected patched SHA-256:
`5b86da28089a9c67c6978e584a4d36e5290a2337caca47193e1bb033d434265f`.
It is byte-identical to the tested `nc3-party-cpu-research.nds`.
The research launcher
`scripts/run_melonds.sh` opens the original workbench ROM: select the patched
output using melonDS's Open ROM command instead.

The command above assumes you are in the project root. If using the extracted
ZIP elsewhere, select its `nc3-party-cpu.bps` and the original USA ROM in your
BPS patcher; the resulting ROM must have the same patched SHA-256 above.

Use a copy of your battery save with the patched ROM's filename. Start the mode
through the game's menus; save states from the original ROM or an earlier patch
restore that build's code and must not be loaded into this updated ROM.
No scripts are needed to play the patched ROM.

## Player-box label in prototype 4

The next empty player box reads **X ADD CPU**, with extra space before X.
There is no corner hint. Press DS X or touch the player box to add a CPU.

## Selection fixes in prototype 2

- Future CPU slots stay empty until their turn, so their former defaults no
  longer block P1's choices. Confirmed choices still follow native uniqueness
  and unlock rules.
- Confirmed idle fighters remain visible while later CPUs choose.
- The Yes/No pointer matches the highlighted choice for each slot.

## Scope and validation

Battle Royale is the verified rule set. Desktop tests cover a complete round
with one CPU, a cold-boot round with three CPUs, individual character selection,
autonomous movement/attacks, natural damage, results, rematch and exit. The
three-CPU roster tested was Naruto / Sasuke / Sakura / Shikamaru. CPUs share a
basic combat AI; there is no per-character AI tuning or difficulty selector.
Other Party rules and the full character/stage roster have not been exhaustively
tested. Mixing CPUs with wireless guests is unsupported.

**Delta compatibility still needs device testing.** Desktop validation uses
the project-local melonDS 0.9.5 interpreter. Mission data is unchanged by this
Party build. Technical details and evidence are recorded in
`notes/PARTY_CPU_MODE.md` and `party-cpu-runtime-validation.json`.

To rebuild the research ROM in this workbench:

```sh
python3 scripts/build_party_cpu.py
```

The builder requires Clang/LLD and LLVM tools. Sources, original-byte assertions,
the ARM9 reservation/bootstrap and hook metadata are included with the patch.
The release bundle contains no ROM or save files.
