"""Verified NC3 USA filedata.bin resource table and uncompressed metadata access."""
from pathlib import Path
import hashlib
import struct

SOURCE_SHA256 = '6ca0d8af595730515acd591cbee3879a6c5ebaf6889422d375b1c841a832d5cc'


def load_original(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError('Source ROM SHA-256 does not match the original NC3 USA ROM')
    return data


class Resources:
    def __init__(self, rom):
        fat = struct.unpack_from('<I', rom, 0x48)[0]
        start, end = struct.unpack_from('<2I', rom, fat)
        if start != 0xECC00 or end - start != 21575688:
            raise ValueError('Unexpected filedata.bin FAT mapping')
        self.rom_offset = start
        self.data = rom[start:end]
        count = struct.unpack_from('<I', self.data)[0]
        if count != 0x90:
            raise ValueError('Unexpected resource-group count')
        self.offsets = [struct.unpack_from('<I', self.data, 4 + i * 4)[0] * 4 for i in range(count)]
        if self.offsets != sorted(self.offsets) or self.offsets[0] != 4 + count * 4:
            raise ValueError('Invalid resource offsets')

    def entries(self, group):
        pos = self.offsets[group]
        end = self.offsets[group + 1] if group + 1 < len(self.offsets) else len(self.data)
        rows = []
        while pos + 4 <= end:
            flags = struct.unpack_from('<I', self.data, pos)[0]
            if flags == 0xFFFFFFFF:
                break
            size = flags & 0x7FFFFFFF
            next_pos = pos + 4 + ((size + 3) & ~3)
            if next_pos > end:
                raise ValueError('Resource exceeds group boundary')
            rows.append({'index': len(rows), 'file_offset': pos + 4,
                         'rom_offset': self.rom_offset + pos + 4,
                         'size': size, 'compressed': bool(flags & 0x80000000)})
            pos = next_pos
        return rows

    def entry(self, group, index):
        return self.entries(group)[index]


def sjis_fullwidth(text):
    full = ''.join(chr(ord(c) + 0xFEE0) if '!' <= c <= '~'
                   else '\u3000' if c == ' ' else c for c in text)
    return full.encode('shift_jis')
