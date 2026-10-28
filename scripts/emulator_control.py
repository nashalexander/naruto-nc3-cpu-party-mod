#!/usr/bin/env python3
"""Send a local JSON command to the opt-in melonDS frontend control shim."""
import argparse
import json
import os
from pathlib import Path
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
REQUEST = Path(os.environ.get('NC3_CONTROL_PATH', ROOT / 'workbench/runtime/control.json')).resolve()
LOG = ROOT / 'workbench/captures/control.jsonl'


def command(op, instance=0, timeout=15, **kwargs):
    req = dict(op=op, instance=instance, id=uuid.uuid4().hex, **kwargs)
    if REQUEST.exists():
        raise RuntimeError('An unconsumed emulator request already exists')
    REQUEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = REQUEST.with_suffix('.tmp')
    temporary.write_text(json.dumps(req))
    temporary.replace(REQUEST)
    response = Path(str(REQUEST) + '.result')
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if response.exists():
            r = json.loads(response.read_text())
            if r.get('id') == req['id']:
                LOG.parent.mkdir(parents=True, exist_ok=True)
                with LOG.open('a') as f:
                    f.write(json.dumps({'time': time.time(), 'request': req, 'response': r}) + '\n')
                if not r.get('ok'):
                    raise RuntimeError(r.get('error', 'Emulator command failed'))
                return r
        time.sleep(.025)
    raise TimeoutError('Emulator command timed out. A GDB stop can block emulation-thread requests.')


def step(instance=0, frames=1):
    for _ in range(frames):
        r = command('step', instance)
        target = r['target_frame']
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            status = command('status', instance)
            current = next(s for s in status['instances'] if s['instance'] == instance)
            if current['frames'] >= target and current.get('paused', True):
                if current['frames'] != target:
                    raise RuntimeError('Frame step advanced an unexpected number of frames')
                break
            time.sleep(.025)
        else:
            raise TimeoutError('Frame did not finish')
    return command('status', instance)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('op')
    p.add_argument('fields', nargs='?', default='{}', help='JSON object of operation arguments')
    p.add_argument('--instance', type=int, default=0)
    a = p.parse_args()
    kw = json.loads(a.fields)
    if a.op == 'step':
        result = step(a.instance, kw.get('frames', 1))
    else:
        if 'path' in kw:
            kw['path'] = str((ROOT / kw['path']).resolve())
        result = command(a.op, a.instance, **kw)
    print(json.dumps(result, indent=2))
