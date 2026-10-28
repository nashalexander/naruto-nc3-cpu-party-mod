"""GDB-only, asserted research hot reload at the native frame-input writer.

Requires a cold-booted Party CPU research image whose ArenaHi is already
0x023D0000. This never converts an original-ROM state into a verified mod run.
The live-build.json sidecar identifies the currently executing payload.
"""
import gdb
import json
from pathlib import Path

directory=Path('workbench/party-mode')
current=json.loads((directory/'build/build.json').read_text())
previous=json.loads((directory/'live-build.json').read_text())

class PartyHotReload(gdb.Breakpoint):
    def __init__(self):
        ram=int(gdb.parse_and_eval('NDS::MainRAM'))
        super().__init__(f'*(unsigned short*){ram+0xc3380}',
                         type=gdb.BP_WATCHPOINT,wp_class=gdb.WP_WRITE)

    def stop(self):
        pc=int(gdb.parse_and_eval('NDS::ARM9->R[15]'))-8
        if pc!=0x0201efc8:return False
        inferior=gdb.selected_inferior()
        ram=int(gdb.parse_and_eval('NDS::MainRAM'))
        def read(address,n):return inferior.read_memory(ram+address-0x02000000,n).tobytes()
        def write(address,data):inferior.write_memory(ram+address-0x02000000,data)
        assert int.from_bytes(read(0x023ffdc4,4),'little')==0x023d0000, 'Heap reservation not established'
        old_hooks={h['address']:h for h in previous['hooks']}
        for hook in current['hooks']:
            expected=old_hooks.get(hook['address'],hook)['after' if hook['address'] in old_hooks else 'before']
            assert read(hook['address'],4)==bytes.fromhex(expected), f'Unexpected hook bytes at {hook["address"]:08x}'
        # The native input poll occurs before any Party hooks in this frame.
        assert int(gdb.parse_and_eval('NDS::ARM9->R[14]'))==0x0201f0d0
        saved=read(previous['symbols']['state'],min(previous.get('state_size',400),current.get('state_size',400)))
        write(current['payload_base'],(directory/'build/payload.bin').read_bytes())
        write(current['symbols']['state'],bytes(0x1000))
        write(current['symbols']['state'],saved)
        for hook in current['hooks']:write(hook['address'],bytes.fromhex(hook['after']))
        (directory/'live-build.json').write_text(json.dumps(current,indent=2)+'\n')
        (directory/'last-hotload.json').write_text(json.dumps({
            'native_input_pc':hex(pc),'previous_target':previous['target_sha256'],
            'new_target':current['target_sha256'],'hooks_checked':len(current['hooks']),
            'research_only':True},indent=2)+'\n')
        self.enabled=False
        print('NC3 Party research payload hot-loaded after asserted native input poll')
        return False

PARTY_HOT_POINT=PartyHotReload()
