#!/usr/bin/env python3
"""Build original-byte-asserted ARM hooks for Party CPU research (not a release)."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from nc3_resources import load_original, Resources

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'workbench/party-mode/build'
BASE=0x023d0000
HOOKS={0x02061164:('lobby_hook','original_lobby'),
       0x020207c8:('count_hook','original_count'),
       0x02020738:('exchange_hook','original_exchange'),
       0x0200fa7c:('packet_hook','original_packet'),
       0x020205f0:('slot_hook','original_slot'),
       0x0206647c:('character_hook','original_character'),
       0x02069e30:('technique_hook','original_technique'),
       0x020226b0:('scene_hook','original_scene'),
       0x0204d660:('preview_hook','original_preview')}

def branch(pc,target,link=False):
    delta=target-pc-8
    assert delta%4==0 and -(1<<25)<=delta<(1<<25)
    return struct.pack('<I',(0xeb000000 if link else 0xea000000)|((delta//4)&0xffffff))

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    if (BUILD/'build.json').exists():
        previous=json.loads((BUILD/'build.json').read_text())
        history=BUILD/'history';history.mkdir(exist_ok=True)
        stem=previous['target_sha256'][:16]
        (history/(stem+'.json')).write_bytes((BUILD/'build.json').read_bytes())
        if (BUILD/'payload.bin').exists():
            (history/(stem+'.payload.bin')).write_bytes((BUILD/'payload.bin').read_bytes())
    source=load_original(ROOT/'Naruto - Ninja Council 3 (USA).nds')
    arm9=source[0x4000:0x4000+0xbf398]
    entry=Resources(source).entry(0x8c,16)
    assert entry['size']==60 and not entry['compressed']
    weights=source[entry['rom_offset']:entry['rom_offset']+60]
    (BUILD/'cpu_ai.inc').write_text('static const u8 generic_cpu_ai[60]={'+','.join(str(v) for v in weights)+'};\n')
    asm=['.syntax unified','.arm','.arch armv5te','.text']
    for address,(hook,original) in HOOKS.items():
        word=struct.unpack_from('<I',arm9,address-0x02000000)[0]
        asm += [f'.global {original}', f'{original}:']
        if word&0xffff0000==0xe92d0000:
            asm += [f'.word 0x{word:08x}']
        elif word&0xffff0000==0xe59f0000:
            value=struct.unpack_from('<I',arm9,address-0x02000000+8+(word&0xfff))[0]
            asm += [f'ldr r{(word>>12)&15}, =0x{value:08x}']
        else:raise ValueError(f'Unsupported trampoline instruction {address:08x}: {word:08x}')
        asm += [f'ldr pc, =0x{address+4:08x}', '.ltorg']
    # Enter the native CPU routine after its mission-only result-pointer guard.
    # The original prologue/arguments are reproduced; Party config stays intact.
    assert arm9[0x3ac54:0x3ac5c]==bytes.fromhex('f0412de918d04de2')
    asm += ['.global local_cpu_prepare','local_cpu_prepare:',
            'push {r4,r5,r6,r7,r8,lr}','sub sp, sp, #0x18',
            'ldr r2, =0x020ce23c','mov r5, r0','mov r4, r1','mov r0, #0',
            'ldr pc, =0x0203ac78','.ltorg']
    asm += ['.global cpu_profile_gate','cpu_profile_gate:',
            'push {r12,lr}','mrs lr, cpsr','ldr r12, =state','ldr r12, [r12]',
            'cmp r12, #0','bne 1f','msr cpsr_f, lr','pop {r12,lr}',
            'ldrlt pc, =0x0203b0ac','ldr pc, =0x0203aee8',
            '1: msr cpsr_f, lr','pop {r12,lr}','ldr pc, =0x0203b0ac','.ltorg']
    (BUILD/'originals.S').write_text('\n'.join(asm)+'\n')
    subprocess.run(['clang','--target=arm-none-eabi','-fuse-ld=lld','-mcpu=arm946e-s','-marm','-O2',
                    '-ffreestanding','-fno-builtin','-fno-unwind-tables','-fno-stack-protector',
                    '-nostdlib','-Wl,-T,'+str(ROOT/'scripts/party_cpu/mod.ld'),
                    '-I'+str(BUILD),
                    str(ROOT/'scripts/party_cpu/mod.c'),str(BUILD/'originals.S'),
                    '-o',str(BUILD/'party-cpu.elf')],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',str(BUILD/'party-cpu.elf'),str(BUILD/'payload.bin')],check=True)
    nm=subprocess.check_output(['llvm-nm','--defined-only',str(BUILD/'party-cpu.elf')],text=True)
    symbols={line.split()[2]:int(line.split()[0],16) for line in nm.splitlines() if len(line.split())==3}
    payload=(BUILD/'payload.bin').read_bytes()
    payload+=bytes((-len(payload))%4)
    (BUILD/'payload.bin').write_bytes(payload)
    assert symbols['payload_end']<BASE+0x10000
    patches=[]
    target=bytearray(source)
    modified=bytearray(arm9)
    for address,(hook,_) in HOOKS.items():
        before=arm9[address-0x02000000:address-0x02000000+4]
        after=branch(address,symbols[hook])
        modified[address-0x02000000:address-0x02000000+4]=after
        patches.append({'address':address,'before':before.hex(),'after':after.hex(),'hook':hook})
    callsite=0x0202d97c
    before=arm9[callsite-0x02000000:callsite-0x02000000+4]
    assert before==branch(callsite,0x0202866c,True)
    after=branch(callsite,symbols['prepare_hook'],True)
    modified[callsite-0x02000000:callsite-0x02000000+4]=after
    patches.append({'address':callsite,'before':before.hex(),'after':after.hex(),'hook':'prepare_hook'})
    gate=0x0203aee4
    before=arm9[gate-0x02000000:gate-0x02000000+4]
    assert struct.unpack('<I',before)[0] == (struct.unpack('<I',branch(gate,0x0203b0ac))[0]&0x0fffffff)|0xb0000000
    after=branch(gate,symbols['cpu_profile_gate'])
    modified[gate-0x02000000:gate-0x02000000+4]=after
    patches.append({'address':gate,'before':before.hex(),'after':after.hex(),'hook':'cpu_profile_gate'})
    # The SDK's main arena high limit reserves the 64 KiB injection region.
    assert struct.unpack_from('<I',arm9,0x5b3c)[0]==0x023e0000
    struct.pack_into('<I',modified,0x5b3c,BASE)
    # Early entry executes without a stack: copy payload before SDK BSS clearing.
    boot=0x02000000+len(arm9)
    boot_asm=f'''.syntax unified
.arm
.arch armv5te
.text
.global _start
_start:
 ldr r0, =0x{BASE:08x}
 mov r1, #0
 ldr r2, =0x{BASE+0x10000:08x}
1: str r1, [r0], #4
 cmp r0, r2
 blo 1b
 ldr r0, =payload_source
 ldr r1, =0x{BASE:08x}
 ldr r2, ={len(payload)}
2: ldrb r3, [r0], #1
 strb r3, [r1], #1
 subs r2, r2, #1
 bne 2b
 mov ip, #0x04000000
 ldr pc, =0x02000804
.ltorg
.balign 4
payload_source:
.incbin "{BUILD/'payload.bin'}"
'''
    (BUILD/'bootstrap.S').write_text(boot_asm)
    subprocess.run(['clang','--target=arm-none-eabi','-fuse-ld=lld','-mcpu=arm946e-s','-marm','-nostdlib',
                    '-Wl,-Ttext='+hex(boot),'-Wl,--entry=_start',str(BUILD/'bootstrap.S'),
                    '-o',str(BUILD/'bootstrap.elf')],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',str(BUILD/'bootstrap.elf'),str(BUILD/'bootstrap.bin')],check=True)
    assert arm9[0x800:0x804]==bytes.fromhex('01c3a0e3')
    modified[0x800:0x804]=branch(0x02000800,boot)
    modified.extend((BUILD/'bootstrap.bin').read_bytes())
    assert 0x02000000+len(modified)<0x020d4e00 # startup clears temporary raw payload with BSS
    relocated=0x03400000
    assert all(b==0xff for b in source[relocated:relocated+len(modified)])
    target[relocated:relocated+len(modified)]=modified
    struct.pack_into('<I',target,0x20,relocated)
    struct.pack_into('<I',target,0x2c,len(modified))
    struct.pack_into('<I',target,0x80,(relocated+len(modified)+0x1ff)&~0x1ff)
    crc=0xffff
    for b in target[:0x15e]:
        crc^=b
        for _ in range(8):crc=(crc>>1)^(0xa001 if crc&1 else 0)
    struct.pack_into('<H',target,0x15e,crc)
    rom_path=BUILD/'nc3-party-cpu-research.nds';rom_path.write_bytes(target)
    report={'status':'research; runtime and CPU selection/combat pending',
            'source_sha256':hashlib.sha256(source).hexdigest(),
            'target_sha256':hashlib.sha256(target).hexdigest(),
            'payload_base':BASE,'payload_size':len(payload),'symbols':symbols,'hooks':patches,
            'state_size':symbols['payload_end']-symbols['state'],
            'arm9_rom_offset':relocated,'arm9_size':len(modified),'header_crc':crc}
    report['source_files_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ['scripts/build_party_cpu.py','scripts/party_cpu/mod.c','scripts/party_cpu/mod.ld']}
    report['cpu_ai_profile']=16
    (BUILD/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'rom':str(rom_path),'payload_size':len(payload),'hooks':len(patches)},indent=2))

if __name__=='__main__':main()
