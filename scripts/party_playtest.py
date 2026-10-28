#!/usr/bin/env python3
"""Party CPU research capture through native input and read-only telemetry."""
import argparse
import json
from pathlib import Path
import struct
from emulator_control import ROOT, command, step
from controller_input import KEYS, press, settle

DIRECTORY=ROOT/'workbench/party-mode'
KEYS.update({'l':81,'r':87})

def snapshot(name, screenshot=True, save=False):
    path=DIRECTORY/(name+'.bin')
    command('dump',path=str(path))
    data=path.read_bytes()
    raw=struct.unpack_from('<110I',data,0x3df000)
    actors=[]
    for slot,address in enumerate(struct.unpack_from('<4I',data,0xcdd60)):
        if not address:continue
        offset=address-0x02000000
        if not 0<=offset<len(data)-0x134:raise ValueError('Invalid actor pointer')
        def integer(field):return struct.unpack_from('<i',data,offset+field)[0]
        actors.append({'slot':slot,'address':hex(address),'character':data[offset+0x1e],
                       'state':data[offset+0x1f],'action':integer(0x20),
                       'facing':data[offset+0x24],'hp':integer(0x30)/4096,
                       'max_hp':integer(0x28)/4096,'resource_38':data[offset+0x38],
                       'x':integer(0x4c)/4096,'y':integer(0x50)/4096,
                       'ai_target':data[offset+0xdc]})
    result={'cpu_mode':raw[0],'cpu_count':raw[1],'exchanges':raw[3],
            'scene':data[0xc6262], 'scene_phase':data[0xc6263],
            'in_character_select':raw[100],'controlled_slot':raw[101],
            'character_object':hex(raw[103]),'characters_done':raw[104],
            'exchange_caller':hex(raw[105]),'in_technique_select':raw[106],
            'technique_object':hex(raw[107]),'in_battle':raw[108],'ai_ticks':raw[109],
            'local_slot':struct.unpack_from('<I',data,0xc6264)[0],
            'session_players':struct.unpack_from('<I',data,0xc626c)[0],
            'roster':list(data[0xce23f:0xce243]),'actors':actors}
    if result['in_character_select']:
        offset=raw[103]-0x02000000
        result['character_phases']=list(data[offset+0x10:offset+0x14])
        result['character_pages']=list(data[offset+0xc:offset+0x10])
        result['character_cursors']=list(data[offset+0x14:offset+0x18])
        result['confirmation_choices']=list(data[offset+0x18:offset+0x1c])
        result['confirmation_pointer_x']=struct.unpack_from('<i',data,0xce654+0xdb0)[0]
        result['portraits_visible']=[data[0xce654+0x2af+0x4c*i] for i in range(4)]
        result['idle_fighters_visible']=[data[0xce654+0x3df+0x4c*i] for i in range(4)]
        result['cursors_visible']=[data[0xce654+0xa1b+0x4c*i] for i in range(4)]
    if screenshot:command('shot',path=str(DIRECTORY/(name+'.png')))
    if save:command('save',path=str(DIRECTORY/(name+'.mln')))
    (DIRECTORY/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

def fight(name,rounds):
    with (DIRECTORY/(name+'-inputs.jsonl')).open('x') as output:
        for i in range(rounds):
            state=snapshot(name+'-current',screenshot=False)
            output.write(json.dumps(state)+'\n');output.flush()
            if not state['actors']:break
            player=state['actors'][0]
            enemies=[a for a in state['actors'][1:] if a['hp']>0]
            if not enemies:break
            enemy=min(enemies,key=lambda a:abs(a['x']-player['x']))
            direction='right' if enemy['x']>=player['x'] else 'left'
            command('key-down',key=KEYS[direction]);step(frames=2)
            if abs(enemy['x']-player['x'])<30:command('key-up',key=KEYS[direction])
            command('key-down',key=KEYS['y']);step(frames=4)
            command('key-up',key=KEYS['y']);settle(12)
            command('key-up',key=KEYS[direction])
    return snapshot(name,save=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name');parser.add_argument('--frames',type=int,default=0)
    parser.add_argument('--key',choices=KEYS);parser.add_argument('--held',type=int,default=8)
    parser.add_argument('--fight-rounds',type=int,default=0)
    args=parser.parse_args()
    if args.key:press(args.key,args.held,after=10)
    if args.frames:settle(args.frames)
    result=fight(args.name,args.fight_rounds) if args.fight_rounds else snapshot(args.name,save=True)
    print(json.dumps(result,indent=2),flush=True)
