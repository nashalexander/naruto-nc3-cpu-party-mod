#!/usr/bin/env python3
from pathlib import Path
import shutil
import difflib

root = Path(__file__).resolve().parents[1]
src = root / 'tools/src/melonDS-0.9.5/src/frontend/qt_sdl'
p = src / 'main.cpp'
backup = p.with_suffix('.cpp.nc3-original')
if not backup.exists(): shutil.copy2(p, backup)
before = backup.read_text()
after = before
for old, new in [('// TODO: uniform variable spelling',
                  '#include <atomic>\nstd::atomic<uint64_t> nc3LegacyFrames{0};\n\n// TODO: uniform variable spelling'),
                 ('            u32 nlines = NDS::RunFrame();',
                  '            u32 nlines = NDS::RunFrame();\n            ++nc3LegacyFrames;'),
                 ('int main(int argc, char** argv)',
                  '#include "NC3LegacyControl.h"\n\nint main(int argc, char** argv)'),
                 ('    int ret = melon.exec();',
                  '    nc3StartLegacyControl(&melon);\n    int ret = melon.exec();')]:
    if after.count(old) != 1: raise ValueError('Unexpected upstream text: ' + old)
    after = after.replace(old, new)
p.write_text(after)
shutil.copy2(root / 'scripts/NC3LegacyControl.h', src / 'NC3LegacyControl.h')
header = src / 'main.h'
header_backup = header.with_suffix('.h.nc3-original')
if not header_backup.exists(): shutil.copy2(header, header_backup)
header_before = header_backup.read_text()
needle = '    bool emuIsRunning();'
assert header_before.count(needle) == 1
header_after = header_before.replace(needle, '    bool nc3Paused() const { return EmuStatus.load() == 2; }\n' + needle)
header.write_text(header_after)
(root / 'tools/reference/nc3-legacy-control.patch').write_text(''.join(difflib.unified_diff(
    before.splitlines(True), after.splitlines(True), fromfile='a/main.cpp', tofile='b/main.cpp')) + ''.join(difflib.unified_diff(
    header_before.splitlines(True), header_after.splitlines(True), fromfile='a/main.h', tofile='b/main.h')))
print('Installed opt-in legacy capture shim; original source backed up.')
