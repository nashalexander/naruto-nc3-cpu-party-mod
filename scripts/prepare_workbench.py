#!/usr/bin/env python3
"""Validate original inputs and extract debugger references without changing them."""
import hashlib
import json
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '6ca0d8af595730515acd591cbee3879a6c5ebaf6889422d375b1c841a832d5cc'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sections(data):
    if len(data) < 16 or data[:4] != b'MELN':
        raise ValueError('Not a melonDS state')
    major, minor, size = struct.unpack_from('<HHI', data, 4)
    if (major, minor) != (9, 0) or size != len(data):
        raise ValueError('Expected complete version 9.0 state')
    result = {}
    offset = 16
    while offset < len(data):
        if offset + 16 > len(data):
            raise ValueError('Truncated section header')
        name = data[offset:offset + 4].decode('ascii')
        length = struct.unpack_from('<I', data, offset + 4)[0]
        if length < 16 or offset + length > len(data) or name in result:
            raise ValueError('Invalid section length or duplicate section')
        result[name] = {'offset': offset, 'length': length}
        offset += length
    return result


def main():
    rompath = ROOT / 'Naruto - Ninja Council 3 (USA).nds'
    rom = rompath.read_bytes()
    if digest(rom) != EXPECTED:
        raise ValueError('Original ROM checksum mismatch; refusing extraction')
    out = ROOT / 'workbench' / 'extracted'
    out.mkdir(parents=True, exist_ok=True)
    report = {'rom': {'filename': rompath.name, 'sha256': digest(rom),
                      'game_code': rom[12:16].decode('ascii')}, 'states': []}
    for cpu, header_offset in [('arm9', 0x20), ('arm7', 0x30)]:
        offset, entry, base, size = struct.unpack_from('<4I', rom, header_offset)
        if offset + size > len(rom):
            raise ValueError('CPU image exceeds ROM')
        image = rom[offset:offset + size]
        (out / f'{cpu}.bin').write_bytes(image)
        report['rom'][cpu] = {'rom_offset': offset, 'entry': entry,
                              'ram_base': base, 'size': size, 'sha256': digest(image)}
    arm9 = (out / 'arm9.bin').read_bytes()
    states = sorted((ROOT / 'svs').glob('*.svs'))
    if len(states) != 3:
        raise ValueError('Expected the three supplied save states')
    for path in states:
        data = path.read_bytes()
        table = sections(data)
        ndsg = table['NDSG']['offset'] + 16
        console = struct.unpack_from('<I', data, ndsg)[0]
        if console != 0 or table['NDSG']['length'] < 16 + 4 + 0x1000000:
            raise ValueError('Expected DS console and full allocated main RAM')
        # v0.9.5 NDS::DoSavestate: console type, then MainRAMMaxSize bytes.
        ram_offset = ndsg + 4
        ram = data[ram_offset:ram_offset + 0x400000]
        # Prove the mapping with several nontrivial code windows.
        for start in (0, 0x800, 0x1000, 0x1F000):
            if ram[start:start + 256] != arm9[start:start + 256]:
                raise ValueError(f'ARM9 mapping check failed: {path.name}')
        stateout = out / path.stem
        stateout.mkdir(exist_ok=True)
        (stateout / 'mainram.bin').write_bytes(ram)
        # v0.9.5 CartCommon: encryption modes + DSi flag (12 bytes), then
        # CartRetail SRAM length and payload. This ROM uses a 512-byte EEPROM.
        cart = table['NDCS']['offset'] + 16
        save_size = struct.unpack_from('<I', data, cart + 12)[0]
        if save_size != 512 or table['NDCS']['length'] < 16 + 16 + save_size:
            raise ValueError('Unexpected NC3 cartridge save layout')
        battery = data[cart + 16:cart + 16 + save_size]
        (stateout / 'battery.sav').write_bytes(battery)
        cpu = table['ARM9']['offset'] + 16
        # Serialized R15 includes the interpreter pipeline; do not call it a
        # verified live PC or treat LR as proof of a caller.
        regs = struct.unpack_from('<16I', data, cpu + 8)
        cpsr = struct.unpack_from('<I', data, cpu + 72)[0]
        changed = [i for i, (a, b) in enumerate(zip(arm9, ram)) if a != b]
        runs = []
        for i in changed:
            if runs and runs[-1]['end_exclusive'] == i:
                runs[-1]['end_exclusive'] = i + 1
            else:
                runs.append({'start': i, 'end_exclusive': i + 1})
        for run in runs:
            start, end = run['start'], run['end_exclusive']
            run['ram_address'] = 0x02000000 + start
            run['rom_offset'] = report['rom']['arm9']['rom_offset'] + start
            run['original_hex'] = arm9[start:end].hex()
            run['state_hex'] = ram[start:end].hex()
        (stateout / 'arm9_image_differences.json').write_text(json.dumps(runs, indent=2) + '\n')
        info = {'filename': path.name, 'sha256': digest(data), 'version': '9.0',
                'console_type': console, 'sections': table,
                'mainram_file_offset': ram_offset, 'mainram_base': 0x02000000,
                'mainram_size': len(ram), 'mainram_sha256': digest(ram),
                'battery_file_offset': cart + 16, 'battery_size': save_size,
                'battery_sha256': digest(battery),
                'arm9_registers_raw': {f'r{i}': f'0x{r:08x}' for i, r in enumerate(regs)},
                'cpsr': f'0x{cpsr:08x}', 'arm9_image_differing_bytes': len(changed),
                'arm9_image_difference_runs': len(runs)}
        (stateout / 'metadata.json').write_text(json.dumps(info, indent=2) + '\n')
        report['states'].append(info)
        copy = ROOT / 'workbench' / 'states' / path.name
        copy.parent.mkdir(exist_ok=True)
        if copy.exists():
            if digest(copy.read_bytes()) != digest(data):
                raise ValueError(f'Refusing to overwrite changed working state: {copy}')
        else:
            shutil.copy2(path, copy)
    (ROOT / 'workbench' / 'input_manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Verified ROM and 3 version-9.0 states; extracted ARM images and 4 MiB RAM snapshots.')
    print('Outputs: workbench/input_manifest.json and workbench/extracted/')


if __name__ == '__main__':
    main()
