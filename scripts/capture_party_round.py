#!/usr/bin/env python3
"""Capture a timed Party round and optionally exercise rematch/exit with input."""
import argparse

from party_playtest import press, settle, snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',required=True)
    parser.add_argument('--rematch-exit',action='store_true')
    args=parser.parse_args()
    prefix=args.prefix
    players=snapshot(prefix+'-round-start',screenshot=False)['session_players']

    def record(name,screenshot=True):
        state=snapshot(prefix+'-'+name,screenshot=screenshot)
        print(name,state['scene'],[(a['character'],a['hp']) for a in state['actors']],flush=True)
        return state

    def wait_for(predicate,name,limit=1800):
        for _ in range(limit//60):
            state=snapshot(prefix+'-current',screenshot=False)
            if predicate(state):return state
            settle(60)
        record('failed-'+name)
        raise RuntimeError('Timed out: '+name)

    for i in range(12):
        settle(600)
        state=record('round-'+str(i),screenshot=False)
        if state['scene']==10:
            settle(200)
            record('results')
            break
    else:raise RuntimeError('Timed round did not reach native results')
    if not args.rematch_exit:return
    press('start',after=20);settle(80);record('play-again')
    press('left',after=15);press('a',after=20)
    # Actor allocation precedes the native health reset during construction.
    wait_for(lambda s:s['scene']==20 and len(s['actors'])==players and
             all(a['max_hp']>0 and a['hp']==a['max_hp'] for a in s['actors']),'rematch')
    state=record('rematch-live')
    assert all(a['hp']==a['max_hp'] for a in state['actors'])
    # Let the native intro finish before opening the pause menu.
    settle(300)
    press('start',after=15);settle(80)
    press('down',after=30);press('down',after=30)
    press('a',after=20)
    wait_for(lambda s:s['scene']==16,'end-game')
    settle(120);record('end-game')
    press('start',after=15)
    wait_for(lambda s:s['scene']==2,'mode-select')
    settle(120)
    state=record('exit')
    assert not state['cpu_mode'] and not state['cpu_count']


if __name__=='__main__':main()
