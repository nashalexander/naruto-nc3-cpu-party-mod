# Party CPU patch: patching and play guide

This patch adds **one human plus 1–3 CPUs** to **Party Mode > Squad Leader**.
You choose each CPU's character and play through the game's Party battle flow.
No second DS or wireless guest is needed.

## Apply the patch

Use a BPS patcher to apply **`nc3-party-cpu.bps`** to an original
**Naruto: Ninja Council 3 (USA)** ROM, game code **AN4E**, 64 MiB
(67,108,864 bytes). Apply it directly to the original ROM.

| ROM | SHA-256 |
| --- | --- |
| Original | `6ca0d8af595730515acd591cbee3879a6c5ebaf6889422d375b1c841a832d5cc` |
| Patched | `5b86da28089a9c67c6978e584a4d36e5290a2337caca47193e1bb033d434265f` |

For example, with Flips on your PATH and the patch in the current directory:

```sh
flips --apply nc3-party-cpu.bps \
  'Naruto - Ninja Council 3 (USA).nds' nc3-party-cpu.nds
sha256sum nc3-party-cpu.nds
```

Open the patched output in your emulator and boot normally. No scripts are
needed to play.

## Play

1. Enter **Party Mode > Squad Leader**.
2. Press **DS X** or touch **X ADD CPU** in the next empty player box.
   Repeat to add up to three CPUs.
3. Press **Start**, then choose **Battle Royale**, a stage, and a time limit.
4. Choose P1's character and confirm **Yes**. Then choose CPU 1's character,
   followed by CPU 2 and CPU 3 if added. The label on the left identifies the
   active CPU. The normal grid, touch controls, and L/R page buttons work.
5. At each character confirmation, **No** is selected initially. Press Left
   once for **Yes**, then A. Confirmed fighters remain visible; future CPU
   slots reserve no characters.
6. CPUs automatically confirm their default techniques. Choose P1's techniques
   normally and finish with **Start**.
7. Press **Start** on the Objective screen to begin.

After results, press Start to open **Play again?**. Yes repeats the match with
the same roster. **End Game** opens the game's disconnect screen; press Start
to return to Mode Select.

To restart with fewer CPUs, leave and re-enter Squad Leader. Leaving Party
Mode clears the CPU roster. The add-CPU label disappears when all slots are
filled. Native character unlocks and duplicate-character restrictions apply.

## Saves and troubleshooting

- Use a copy of your battery save (`.sav`) with the patched ROM's base filename,
  following your emulator's save import rules.
- Boot through the menus. Save states from the original ROM or an earlier patch
  restore that build's code and should not be loaded with this patch.
- If **X ADD CPU** does not appear, check that you opened the patched ROM and
  that its checksum matches the table above.
- The lobby still shows wireless wording and Join artwork. Start works once a
  CPU is added. No wireless guest needs to join.

## Tested behavior and limitations

Tests cover complete one-CPU and three-CPU Battle Royale
rounds, individual character selection, CPU movement and attacks, natural
damage, results, rematch, and exit. The tested three-CPU roster was
Naruto / Sasuke / Sakura / Shikamaru.

The current release's lobby label was checked separately. Full-round checks
were performed on earlier builds with the same gameplay code; the runtime
report records the build checksums for those checks.

CPUs share basic combat AI, with no difficulty selector or character-specific
tuning. Other Party rules and the full character/stage roster have not been
exhaustively tested. Mixing CPUs with wireless guests is unsupported.
