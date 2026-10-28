#!/usr/bin/env python3
"""Install the opt-in local control shim in the downloaded 1.1 frontend."""
from pathlib import Path
import shutil
import difflib

root = Path(__file__).resolve().parents[1]
src = root / 'tools/src/melonDS-1.1/src/frontend/qt_sdl'
edits = {
    'main.cpp': [('Net net;\n', 'Net net;\n\n#include "NC3Control.h"\n'),
                 ('    int ret = melon.exec();', '    nc3StartControl(&melon);\n    int ret = melon.exec();')],
    'EmuThread.h': [('    int frontBuffer = 0;', '    std::atomic<uint64_t> nc3FrameCount{0};\n    int frontBuffer = 0;')],
    'EmuThread.cpp': [('                nlines = emuInstance->nds->RunFrame();',
                       '                nlines = emuInstance->nds->RunFrame();\n                ++nc3FrameCount;')],
}
patches = []
for name, changes in edits.items():
    path = src / name
    backup = path.with_suffix(path.suffix + '.nc3-original')
    if not backup.exists():
        shutil.copy2(path, backup)
    before = backup.read_text()
    after = before
    for old, new in changes:
        if after.count(old) != 1:
            raise ValueError(f'Unexpected upstream text: {name}: {old}')
        after = after.replace(old, new)
    path.write_text(after)
    patches.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                      fromfile='a/' + name, tofile='b/' + name))
shutil.copy2(root / 'scripts/NC3Control.h', src / 'NC3Control.h')
(root / 'tools/reference/nc3-frontend-control.patch').write_text(''.join(patches))
print('Installed opt-in control shim; original frontend files backed up; ROM untouched.')
