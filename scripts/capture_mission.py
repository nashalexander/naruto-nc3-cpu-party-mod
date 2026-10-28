#!/usr/bin/env python3
"""Replay the controlled mission experiment against the legacy capture build.

Launch the compatible emulator with NC3_CONTROL_PATH pointing to
workbench/runtime/legacy-control.json before running this script.
"""
import hashlib
import json
import os
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('NC3_CONTROL_PATH', str(ROOT / 'workbench/runtime/legacy-control.json'))
from emulator_control import command, step


def main():
    out = ROOT / 'workbench/controlled-mission'
    out.mkdir(parents=True, exist_ok=True)
    if command('status')['instances'][0]['running']:
        command('pause')
    command('load', path=str(ROOT / 'workbench/states/Battle_npc_save.svs'))
    step(frames=2)
    baseline = out / 'baseline.mln'
    command('save', path=str(baseline))
    command('dump', path=str(out / 'baseline.bin'))
    command('shot', path=str(out / 'baseline.png'))
    cases = [('idle4', None, 4), ('idle4-repeat', None, 4),
             ('right4', 16777236, 4), ('left4', 16777234, 4),
             ('right8', 16777236, 8), ('left8', 16777234, 8), ('idle8', None, 8)]
    manifest = []
    for name, key, frames in cases:
        command('load', path=str(baseline))
        if key: command('key-down', key=key)
        step(frames=frames)
        if key: command('key-up', key=key)
        info = command('dump', path=str(out / (name + '.bin')))
        command('shot', path=str(out / (name + '.png')))
        (out / (name + '.json')).write_text(json.dumps(info, indent=2) + '\n')
        digest = hashlib.sha256((out / (name + '.bin')).read_bytes()).hexdigest()
        manifest.append({'case': name, 'key': key, 'frames': frames, 'mainram_sha256': digest})
        print('Captured', name, flush=True)
    assert (out / 'idle4.bin').read_bytes() == (out / 'idle4-repeat.bin').read_bytes(), 'Idle replay differs'
    data = {name: (out / (name + '.bin')).read_bytes() for name, _, _ in cases}
    candidates = []
    for offset in range(0, 0x400000, 4):
        v = {name: struct.unpack_from('<i', ram, offset)[0] for name, ram in data.items()}
        right, left = v['right4'] - v['idle4'], v['left4'] - v['idle4']
        right8, left8 = v['right8'] - v['idle8'], v['left8'] - v['idle8']
        if right and right == -left and abs(right) < 0x1000000 and right8 == -left8 and abs(right8) > abs(right):
            candidates.append({'address': 0x02000000 + offset, 'values': v, 'delta4': right, 'delta8': right8})
    (out / 'capture_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'movement_candidates.json').write_text(json.dumps(candidates, indent=2) + '\n')
    print('Idle replay identical; saved', len(candidates), 'movement candidates. These require visual/write-trace proof.')


if __name__ == '__main__':
    main()
