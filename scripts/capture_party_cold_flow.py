#!/usr/bin/env python3
"""Replay a cold-boot local Party CPU setup with normal buttons/touch only."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from emulator_control import ROOT,command,step
from party_playtest import snapshot,press,settle

DIRECTORY=ROOT/'workbench/party-mode'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cpus',type=int,choices=[1,2,3],default=3)
parser.add_argument('--prefix',default='cold-final')
parser.add_argument('--from-lobby',action='store_true',help='Replay from a native lobby state of this exact build')
parser.add_argument('--selection-regressions',action='store_true',help='Check blank CPUs, formerly reserved fighters and confirmation UI')
parser.add_argument('--characters',help='Comma-separated test roster, using IDs 0–3 (default: 0,1,2,3 as needed)')
parser.add_argument('--add-with-x',action='store_true',help='Add CPUs using the DS X button rather than touch')
parser.add_argument('--lobby-only',action='store_true',help='Stop after adding CPUs and capturing the lobby')
args=parser.parse_args()
prefix=args.prefix
counter=0

def data():
    path=DIRECTORY/(prefix+'-current.bin')
    command('dump',path=str(path))
    return path.read_bytes()

def wait_for(predicate,description,limit=1800):
    for _ in range(limit//60):
        b=data()
        if predicate(b):return b
        settle(60)
    command('shot',path=str(DIRECTORY/(prefix+'-failed.png')))
    raise RuntimeError('Timed out: '+description)

def scene(value):
    wait_for(lambda b:b[0xc6262]==value,'scene '+str(value))
    settle(220)

def record(name,save=False):
    global counter
    counter+=1
    name=prefix+'-'+name
    r=snapshot(name,save=save)
    print(name,'scene',r['scene'],'CPUs',r['cpu_count'],'control',r['controlled_slot'],flush=True)
    return r

def touch(x,y,frames=8):
    command('touch',x=x,y=y);step(frames=frames);command('release-touch')
    settle(40)

def control(b):return struct.unpack_from('<I',b,0x3df000+404)[0]

def phase(b,index):
    obj=struct.unpack_from('<I',b,0x3df000+412)[0]-0x02000000
    return b[obj+0x10+index]

def choose(index,x,y,target_page=0):
    wait_for(lambda b:b[0xc6262]==6 and control(b)==index and phase(b,index)==1,
             'character input for slot '+str(index))
    for _ in range(4):
        b=data();obj=struct.unpack_from('<I',b,0x3df000+412)[0]-0x02000000
        if b[obj+0x0c+index]==target_page:break
        press('l',after=20);settle(120)
    touch(x,y)
    if phase(data(),index)!=6:press('a',after=30)
    wait_for(lambda b:phase(b,index)==6,'character confirmation for slot '+str(index))
    if args.selection_regressions:
        s=record('slot-'+str(index)+'-no')
        assert s['confirmation_choices'][index]==1 and s['confirmation_pointer_x']==104
        assert s['idle_fighters_visible'][:index+1]==[1]*(index+1)
    press('left',after=20)
    if args.selection_regressions:
        s=record('slot-'+str(index)+'-yes')
        assert s['confirmation_choices'][index]==0 and s['confirmation_pointer_x']==32
    press('a',after=30)
    if index<args.cpus:
        wait_for(lambda b:control(b)==index+1,'handoff to CPU '+str(index+1))
        settle(180)
    else:scene(7)
    record('confirmed-slot-'+str(index))

status=command('status')['instances'][0]
if not status['paused']:command('pause')
build=json.loads((DIRECTORY/'build/build.json').read_text())
rom=DIRECTORY/'build/nc3-party-cpu-research.nds'
assert hashlib.sha256(rom.read_bytes()).hexdigest()==build['target_sha256']
(DIRECTORY/(prefix+'-build.json')).write_text(json.dumps(build,indent=2)+'\n')
command('shot',path=str(DIRECTORY/(prefix+'-start.png')))
if not args.from_lobby:
    for _ in range(8):
        if data()[0xc6262]==12:break
        press('start',after=10);settle(180)
    scene(12)
b=data();assert struct.unpack_from('<I',b,0x3ffdc4)[0]==0x023d0000
for hook in build['hooks']:
    offset=hook['address']-0x02000000
    assert b[offset:offset+4]==bytes.fromhex(hook['after'])
record('lobby-restored' if args.from_lobby else 'boot')
if not args.from_lobby:
    command('touch',x=28,y=55);step(frames=6)
    for x in range(40,256,15):command('touch',x=x,y=55);step(frames=2)
    command('touch',x=255,y=55);step(frames=8);command('release-touch');settle(100)
    touch(130,55);scene(2)
    touch(163,60);press('a',after=20);scene(5)
    press('a',after=20)
def host_ready(b):
    obj=struct.unpack_from('<I',b,0xc6268)[0]-0x02000000
    return 0<=obj<len(b)-128 and b[obj+12]==2 and struct.unpack_from('<H',b,0xc3488)[0]==1
wait_for(host_ready,'fresh squad leader lobby');settle(80)
record('empty-lobby',save=True)
for i in range(args.cpus):
    if args.add_with_x:press('x',after=30)
    else:touch(120,90+32*i)
    wait_for(lambda b:struct.unpack_from('<I',b,0x3df004)[0]==i+1,'Add CPU '+str(i+1))
    record('added-cpu-'+str(i+1))
if args.lobby_only:
    print('CPU-add lobby captured; stopping before match setup.',flush=True)
    raise SystemExit(0)
press('start',after=20);scene(11)
record('party-rules')
touch(193,88);press('a',after=20);scene(8)
record('stage')
press('a',after=20);settle(220);record('time')
press('a',after=20);scene(6)
record('p1-select',save=True)
if args.selection_regressions:
    s=record('unassigned-cpus')
    assert s['character_phases'][1:1+args.cpus]==[255]*args.cpus
    assert s['portraits_visible'][1:1+args.cpus]==[0]*args.cpus
    assert s['idle_fighters_visible'][1:1+args.cpus]==[0]*args.cpus
    assert s['cursors_visible'][1:1+args.cpus]==[0]*args.cpus
    for target_page,character in [(1,3),(2,32),(3,35)]:
        for _ in range(4):
            b=data();obj=struct.unpack_from('<I',b,0x3df000+412)[0]-0x02000000
            if b[obj+0x0c]==target_page:break
            press('l',after=20);settle(100)
        touch(128,102)
        if phase(data(),0)!=6:press('a',after=30)
        wait_for(lambda b:phase(b,0)==6,'formerly reserved character '+str(character))
        s=record('p1-former-default-'+str(character))
        assert s['character_pages'][0]==target_page and s['character_cursors'][0]==4
        assert s['confirmation_choices'][0]==1 and s['confirmation_pointer_x']==104
        press('right',after=10);press('a',after=30)
        wait_for(lambda b:phase(b,0)==1,'decline character '+str(character))
choices={0:(128,102,0),1:(78,102,0),2:(177,102,0),3:(128,102,1)}
expected=[int(v) for v in args.characters.split(',')] if args.characters else list(range(1+args.cpus))
assert len(expected)==1+args.cpus and all(v in choices for v in expected)
for i,character in enumerate(expected):choose(i,*choices[character])
b=data();roster=list(b[0xce23f:0xce243])
assert roster[:1+args.cpus]==expected,(roster,expected)
record('techniques')
press('start',after=30);settle(70);press('left',after=20);press('a',after=30)
scene(9);record('objectives',save=True)
press('start',after=20);scene(20)
wait_for(lambda b:all(struct.unpack_from('<4I',b,0xcdd60)[:1+args.cpus]),'fighter constructors')
record('constructed',save=True)
settle(500)
r=record('live',save=True)
assert [a['character'] for a in r['actors']]==expected
assert r['local_slot']==0 and r['session_players']==1+args.cpus and r['ai_ticks']>0
print('Party CPU flow verified for',args.cpus,'CPUs; native lobby replay' if args.from_lobby else 'CPUs; cold boot',flush=True)
