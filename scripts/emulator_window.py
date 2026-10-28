#!/usr/bin/env python3
"""Inspect/control a melonDS X11 window; dependencies live in tools/python."""
import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/python'))
from Xlib import X, XK, display
from Xlib.protocol import event
from Xlib.ext import xtest
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('action', choices=['list', 'shot', 'key', 'click', 'type', 'close'])
p.add_argument('args', nargs='*')
p.add_argument('--window', type=lambda v: int(v, 0))
a = p.parse_args()
d = display.Display()
root = d.screen().root
windows = []


def walk(w, depth=0):
    if depth > 3:
        return
    try:
        cls = w.get_wm_class() or ()
        if any('melonds' in c.lower() for c in cls):
            g = w.get_geometry()
            if w.get_attributes().map_state == X.IsViewable:
                windows.append((w, g.width * g.height))
        for child in w.query_tree().children:
            walk(child, depth + 1)
    except Exception:
        pass


walk(root)
if a.action == 'list':
    for w, _ in windows:
        g = w.get_geometry()
        print(hex(w.id), repr(w.get_wm_name()), g.width, g.height)
    sys.exit(0)
if a.window:
    candidates = [w for w, _ in windows if w.id == a.window]
else:
    candidates = [w for w, _ in sorted(windows, key=lambda t: t[1], reverse=True)]
if not candidates:
    raise SystemExit('No matching visible melonDS window')
w = candidates[0]
g = w.get_geometry()
if a.action == 'close':
    w.send_event(event.ClientMessage(window=w, client_type=d.intern_atom('WM_PROTOCOLS'),
                                    data=(32, [d.intern_atom('WM_DELETE_WINDOW'), X.CurrentTime, 0, 0, 0])))
    d.sync()
elif a.action == 'shot':
    # X11 may return stale/undefined pixels for an obscured window. Expose it
    # before reading, especially when coordinated instances overlap.
    root.send_event(event.ClientMessage(window=w, client_type=d.intern_atom('_NET_ACTIVE_WINDOW'),
                                      data=(32, [1, X.CurrentTime, 0, 0, 0])),
                    event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    w.configure(stack_mode=X.Above)
    d.sync()
    time.sleep(0.4)
    raw = w.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xffffffff)
    im = Image.frombytes('RGB', (g.width, g.height), raw.data, 'raw', 'BGRX')
    target = ROOT / a.args[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    im.save(target)
    print(target)
else:
    root.send_event(event.ClientMessage(window=w, client_type=d.intern_atom('_NET_ACTIVE_WINDOW'),
                                      data=(32, [1, X.CurrentTime, 0, 0, 0])),
                    event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    w.configure(stack_mode=X.Above)
    w.set_input_focus(X.RevertToParent, X.CurrentTime)
    d.sync()
    time.sleep(0.35)
    time.sleep(0.15)
    def send(kind, code, mask):
        w.send_event(kind(time=X.CurrentTime, root=root, window=w,
                          child=X.NONE, root_x=1, root_y=1, event_x=1,
                          event_y=1, state=mask, detail=code, same_screen=1),
                     propagate=True)
    if a.action == 'key':
        codes = [d.keysym_to_keycode(XK.string_to_keysym(s)) for s in a.args]
        if not all(codes):
            raise SystemExit('Unknown key')
        modifiers = {'Shift_L': X.ShiftMask, 'Shift_R': X.ShiftMask,
                     'Control_L': X.ControlMask, 'Control_R': X.ControlMask,
                     'Alt_L': X.Mod1Mask, 'Alt_R': X.Mod1Mask}
        state = 0
        for name, code in zip(a.args, codes):
            send(event.KeyPress, code, state)
            state |= modifiers.get(name, 0)
        d.sync()
        time.sleep(0.12)
        for name, code in reversed(list(zip(a.args, codes))):
            send(event.KeyRelease, code, state)
            state &= ~modifiers.get(name, 0)
    elif a.action == 'type':
        for char in a.args[0]:
            candidates = d.keysym_to_keycodes(ord(char))
            candidates = [(code, index) for code, index in candidates if index < 2]
            if not candidates:
                raise SystemExit('Cannot type character: ' + repr(char))
            code, index = candidates[0]
            mask = X.ShiftMask if index == 1 else 0
            send(event.KeyPress, code, mask)
            send(event.KeyRelease, code, mask)
        d.sync()
    else:
        x, y = map(int, a.args)
        xy = root.translate_coords(w, x, y)
        xtest.fake_input(d, X.MotionNotify, x=xy.x, y=xy.y)
        xtest.fake_input(d, X.ButtonPress, 1)
        xtest.fake_input(d, X.ButtonRelease, 1)
    d.sync()
    time.sleep(0.5)
