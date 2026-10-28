"""Source inside native GDB after pausing the legacy emulator at the baseline.

gdb command: source scripts/trace_coordinate_writes.py
Then continue and request four right-walking frames through the file controller.
This traces emulator host writes to three proven movement-related RAM copies.
"""
import gdb
import json
from pathlib import Path

OUTPUT = Path(globals().get('NC3_TRACE_DIRECTORY', 'workbench/captures/coordinate-writes'))
OUTPUT.mkdir(parents=True, exist_ok=True)
POINTS = []
EVENTS = []


class CoordinateWrite(gdb.Breakpoint):
    def __init__(self, address):
        self.address = address
        offset = address - 0x02000000
        # A constant host address avoids also watching the NDS::MainRAM pointer
        # variable, which otherwise consumes an extra hardware watch slot.
        host_address = int(gdb.parse_and_eval('NDS::MainRAM')) + offset
        self.width = globals().get('NC3_TRACE_WIDTH', 4)
        ctype = {1: 'unsigned char', 2: 'unsigned short', 4: 'unsigned int'}[self.width]
        access = globals().get('NC3_TRACE_ACCESS', 'write')
        wp = gdb.WP_READ if access == 'read' else gdb.WP_WRITE
        super().__init__(f'*({ctype}*){host_address}', type=gdb.BP_WATCHPOINT, wp_class=wp)

    def stop(self):
        regs = [int(gdb.parse_and_eval(f'NDS::ARM9->R[{i}]')) for i in range(16)]
        cpsr = int(gdb.parse_and_eval('NDS::ARM9->CPSR'))
        current = int(gdb.parse_and_eval('NDS::ARM9->CurInstr'))
        pc = regs[15] - (4 if cpsr & 0x20 else 8)
        ram = int(gdb.parse_and_eval('NDS::MainRAM'))
        inferior = gdb.selected_inferior()
        value = int.from_bytes(inferior.read_memory(ram + self.address - 0x02000000, self.width), 'little')
        dtcm = int(gdb.parse_and_eval('NDS::ARM9->DTCM'))
        dtcm_base = int(gdb.parse_and_eval('NDS::ARM9->DTCMBase'))
        sequence = len(EVENTS)
        dtcm_path = OUTPUT / f'{sequence:03d}-dtcm.bin'
        dtcm_path.write_bytes(inferior.read_memory(dtcm, 0x4000).tobytes())
        instruction = None
        if 0x02000000 <= pc < 0x02400000:
            size = 2 if cpsr & 0x20 else 4
            instruction = int.from_bytes(inferior.read_memory(ram + pc - 0x02000000, size), 'little')
        event = {'sequence': sequence, 'watched_address': self.address, 'value': value,
                 'width': self.width, 'access': globals().get('NC3_TRACE_ACCESS', 'write'),
                 'registers_raw': regs, 'cpsr': cpsr, 'current_instruction': current,
                 'inferred_instruction_pc': pc, 'instruction_at_pc': instruction,
                 'dtcm_base': dtcm_base, 'dtcm_dump': str(dtcm_path),
                 'native_backtrace': gdb.execute('bt 5', to_string=True)}
        EVENTS.append(event)
        (OUTPUT / 'events.json').write_text(json.dumps(EVENTS, indent=2) + '\n')
        print(f'NC3 write {sequence}: {self.address:08x} = {value:08x}, ARM9 PC {pc:08x}')
        if len(EVENTS) >= globals().get('NC3_TRACE_MAX_EVENTS', 24):
            for point in POINTS: point.enabled = False
        return False


for address in globals().get('NC3_TRACE_ADDRESSES', (0x020c8328, 0x021e7e64, 0x021e80ec)):
    POINTS.append(CoordinateWrite(address))
print(f'{len(POINTS)} field watchpoints installed; bounded trace enabled.')
