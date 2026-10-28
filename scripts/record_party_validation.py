#!/usr/bin/env python3
"""Verify Party CPU capture evidence and write the release validation report."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct
from nc3_resources import Resources

ROOT=Path(__file__).resolve().parents[1]
CAP=ROOT/'workbench/party-mode'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((CAP/(name+'.json')).read_text())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold-prefix',default='v2-cold-release')
    parser.add_argument('--single-prefix',default='v2-single-release')
    args=parser.parse_args()
    cold,single_prefix=args.cold_prefix,args.single_prefix
    build=json.loads((CAP/'build/build.json').read_text())
    frozen=json.loads((CAP/f'{cold}-build.json').read_text())
    assert frozen['target_sha256']==build['target_sha256']
    assert digest(CAP/'build/nc3-party-cpu-research.nds')==build['target_sha256']
    for name,sha in build['source_files_sha256'].items():assert digest(ROOT/name)==sha
    original=json.loads((ROOT/'workbench/input_manifest.json').read_text())
    assert digest(ROOT/original['rom']['filename'])==build['source_sha256']
    for entry in original['states']:assert digest(ROOT/'svs'/entry['filename'])==entry['sha256']
    boot=(CAP/f'{cold}-boot.bin').read_bytes()
    assert struct.unpack_from('<I',boot,0x3ffdc4)[0]==0x023d0000
    assert struct.unpack_from('<I',boot,0x3ffe20)[0]==0x03400000
    for hook in build['hooks']:
        offset=hook['address']-0x02000000
        assert boot[offset:offset+4]==bytes.fromhex(hook['after'])

    rom=(ROOT/original['rom']['filename']).read_bytes()
    grid=rom[0x4000+0xb0d70:0x4000+0xb0d70+36]
    remap=rom[0x4000+0xafab0:0x4000+0xafab0+36]
    blank=read(f'{cold}-unassigned-cpus')
    assert blank['character_phases'][1:]==[255,255,255]
    assert blank['portraits_visible'][1:]==[0,0,0]
    assert blank['idle_fighters_visible'][1:]==[0,0,0]
    assert blank['cursors_visible'][1:]==[0,0,0]
    for page,character in [(1,3),(2,32),(3,35)]:
        s=read(f'{cold}-p1-former-default-'+str(character))
        assert s['character_phases'][0]==6
        assert s['character_pages'][0]==page and s['character_cursors'][0]==4
        assert s['confirmation_choices'][0]==1 and s['confirmation_pointer_x']==104
    for slot in range(4):
        no=read(f'{cold}-slot-'+str(slot)+'-no')
        yes=read(f'{cold}-slot-'+str(slot)+'-yes')
        assert no['confirmation_choices'][slot]==1 and no['confirmation_pointer_x']==104
        assert yes['confirmation_choices'][slot]==0 and yes['confirmation_pointer_x']==32
        assert no['idle_fighters_visible'][:slot+1]==[1]*(slot+1)
        assert yes['idle_fighters_visible'][:slot+1]==[1]*(slot+1)
        for choice in ['no','yes']:
            ram=(CAP/(f'{cold}-slot-'+str(slot)+'-'+choice+'.bin')).read_bytes()
            def word(address):return struct.unpack_from('<I',ram,address-0x02000000)[0]
            def signed_word(address):return struct.unpack_from('<i',ram,address-0x02000000)[0]
            message=word(0x020ce654+0xd08)
            sequence=word(word(message)+12)
            # Native sequence 1 is "Use this character?", not ready/waiting (5).
            while struct.unpack_from('<h',ram,sequence-0x02000000)[0]>=0:sequence+=8
            sequence+=4
            assert word(message+4)==sequence
            yes_mode=signed_word(word(0x020ce654+0xd54)+16)
            no_mode=signed_word(word(0x020ce654+0xda0)+16)
            assert (yes_mode==-2 and no_mode>=0) if choice=='no' else (yes_mode>=0 and no_mode==-2)
    for i in range(1,4):
        added=read(f'{cold}-added-cpu-'+str(i));assert added['cpu_count']==i
    for i in range(3):
        s=read(f'{cold}-confirmed-slot-'+str(i))
        assert s['controlled_slot']==i+1 and s['local_slot']==0
        chosen=[remap[grid[s['character_pages'][j]*9+s['character_cursors'][j]]]
                for j in range(i+1)]
        assert chosen==[0,1,2][:i+1]
        assert s['character_phases'][:i+1]==[4]*(i+1)
        ram=(CAP/(f'{cold}-confirmed-slot-'+str(i)+'.bin')).read_bytes()
        ui=0xce654
        for slot in range(i+2):
            cursor=s['character_cursors'][slot]
            x,y=struct.unpack_from('<2i',ram,ui+slot*0x4c+0xa20)
            assert x==0x38+50*(cursor%3) and y==0x22+46*(cursor//3)
    selected=read(f'{cold}-confirmed-slot-3')
    assert selected['roster']==[0,1,2,3] and selected['scene']==7
    tech=(CAP/f'{cold}-techniques.bin').read_bytes()
    obj=struct.unpack_from('<I',tech,0x3df000+428)[0]-0x02000000
    assert list(tech[obj+12:obj+16])==[1,4,4,4]
    live=read(f'{cold}-live')
    assert live['session_players']==4 and live['cpu_count']==3 and live['local_slot']==0
    assert [a['character'] for a in live['actors']]==[0,1,2,3]
    assert live['ai_ticks']>0
    weights=Resources(rom).entry(0x8c,16)
    expected=rom[weights['rom_offset']:weights['rom_offset']+60]
    ram=(CAP/f'{cold}-live.bin').read_bytes()
    for actor in live['actors'][1:]:
        offset=int(actor['address'],16)-0x02000000
        assert ram[offset+0xdd:offset+0xdd+60]==expected
        assert 0<=actor['ai_target']<4 and actor['ai_target']!=actor['slot']
    assert [struct.unpack_from('<H',ram,0x3df010+64*i)[0] for i in range(1,4)]==[0,0,0]
    rounds=[read(p.stem) for p in sorted(CAP.glob(f'{cold}-round-*.json'))]
    assert any(s['actors'] for s in rounds)
    for slot in range(4):
        values=[s['actors'][slot]['hp'] for s in [live,*rounds] if len(s['actors'])==4]
        assert min(values)<max(values),f'No observed damage for slot {slot}'
    results=read(f'{cold}-results')
    assert results['scene']==10 and not results['actors'] and results['cpu_count']==3
    rematch=read(f'{cold}-rematch-live')
    assert rematch['scene']==20 and len(rematch['actors'])==4
    assert all(a['hp']==a['max_hp'] for a in rematch['actors'])
    exit_state=read(f'{cold}-exit')
    assert exit_state['scene']==2 and not exit_state['cpu_mode'] and not exit_state['cpu_count']

    single=read(f'{single_prefix}-live')
    assert json.loads((CAP/f'{single_prefix}-build.json').read_text())['target_sha256']==build['target_sha256']
    single_ram=(CAP/f'{single_prefix}-live.bin').read_bytes()
    for hook in build['hooks']:
        offset=hook['address']-0x02000000
        assert single_ram[offset:offset+4]==bytes.fromhex(hook['after'])
    assert single['cpu_count']==1 and single['session_players']==2
    assert [a['character'] for a in single['actors']]==[3,0]
    single_result=read(f'{single_prefix}-results')
    assert single_result['scene']==10 and not single_result['actors']
    controls=[json.loads(line) for line in (ROOT/'workbench/captures/control.jsonl').read_text().splitlines()]
    start=max(i for i,r in enumerate(controls) if r['request'].get('path','').endswith(f'/{cold}-start.png'))
    end=max(i for i,r in enumerate(controls) if r['request'].get('path','').endswith(f'/{cold}-exit.bin'))
    ops=collections.Counter(r['request']['op'] for r in controls[start:end+1])
    assert not ops['probe-write'] and not ops['load']
    evidence=[p for p in CAP.glob(f'{cold}-*') if p.suffix in ('.json','.png')]
    evidence += [CAP/f'{single_prefix}-live.json',CAP/f'{single_prefix}-results.json',CAP/f'{single_prefix}-results.png']
    report={'version':'party-cpu-prototype-2','target_sha256':build['target_sha256'],
            'source_sha256':build['source_sha256'],
            'emulator':'project-local melonDS 0.9.5 interpreter with frontend capture shim',
            'cold_boot':True,'add_cpu_button':True,'cpu_counts_exercised':[1,2,3],
            'complete_rounds_verified':{'three_cpus':'cold boot','one_cpu':'native lobby replay of same build'},
            'sequential_selection':['P1','CPU 1','CPU 2','CPU 3'],
            'cold_roster':[0,1,2,3],'one_cpu_roster':[3,0],
            'unassigned_cpus_reserve_no_character':True,
            'p1_former_cpu_defaults_selectable':[3,32,35],
            'confirmed_idle_fighters_remain_visible':True,
            'confirmation_pointer_matches_no_and_yes_for_all_four_slots':True,
            'confirmation_animation_matches_pointer':True,
            'confirmation_message_reset_for_each_slot':True,
            'cpu_default_techniques_confirm_automatically':True,
            'human_input_owner_after_selection':0,'cpu_action_input_packets_zero':True,
            'cpu_ai_profile':16,'natural_damage_all_four_fighters':True,
            'native_results':True,'rematch_full_health_reset':True,'exit_clears_cpu_mode':True,
            'cold_test_savestate_loads':ops['load'],'cold_test_ram_probes':ops['probe-write'],
            'original_inputs_unchanged':True,'wireless_peer_required':False,
            'tested_rule':'Battle Royale','tested_stage':'Bamboo Grove','selected_time_limit':60,
            'delta_status':'untested; device test needed',
            'limitations':['native unlock and duplicate-character restrictions',
                           'shared basic CPU AI; no difficulty selector or character-specific tuning',
                           'other Party rules/full roster/stage matrix not exhaustively tested',
                           'no mixed wireless-human/CPU session support',
                           'native wireless lobby wording and End Game disconnect screen retained'],
            'evidence_sha256':{p.name:digest(p) for p in sorted(evidence)}}
    (ROOT/'dist/party-cpu-runtime-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    release=dict(build)
    release['version']=report['version'];release['status']='Desktop Party CPU behavior verified; Delta pending'
    release['runtime_validation']='party-cpu-runtime-validation.json'
    # Reviewable RAM image edits, separate from the ROM relocation itself.
    target=(CAP/'build/nc3-party-cpu-research.nds').read_bytes()
    old=rom[0x4000:0x4000+0xbf398];new=target[build['arm9_rom_offset']:build['arm9_rom_offset']+len(old)]
    edits=[];i=0
    while i<len(old):
        if old[i]==new[i]:i+=1;continue
        begin=i
        while i<len(old) and old[i]!=new[i]:i+=1
        edits.append({'ram_address':hex(0x02000000+begin),'original':old[begin:i].hex(),'replacement':new[begin:i].hex()})
    release['arm9_original_region_diff']=edits
    (ROOT/'dist/party-cpu-build.json').write_text(json.dumps(release,indent=2)+'\n')
    print('Party CPU runtime evidence, input integrity, cold boot, results/rematch/exit verified.')

if __name__=='__main__':main()
