"""Ordinary melonDS controller input shared by Party CPU capture tools."""
import time

from emulator_control import command, step

KEYS = {'a': 88, 'b': 90, 'x': 83, 'y': 65, 'start': 16777220,
        'left': 16777234, 'right': 16777236, 'up': 16777235, 'down': 16777237}


def settle(frames):
    """Run at normal speed for UI transitions; may exceed the target slightly."""
    initial = command('status')['instances'][0]
    if not initial['paused']:
        raise RuntimeError('Pause before settling')
    target = initial['frames'] + frames
    deadline = time.monotonic() + 60
    command('resume')
    try:
        while time.monotonic() < deadline:
            current = command('status')['instances'][0]['frames']
            if current >= target:
                return
            time.sleep(.05)
        raise TimeoutError('UI transition did not reach target frame')
    finally:
        command('pause')


def press(key, frames=8, after=30):
    command('key-down', key=KEYS[key])
    step(frames=frames)
    command('key-up', key=KEYS[key])
    step(frames=after)
