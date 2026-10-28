#!/usr/bin/env python3
"""Create and independently apply the verified Party CPU BPS; never bundle ROMs."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    report=json.loads((DIST/'party-cpu-runtime-validation.json').read_text())
    build=json.loads((DIST/'party-cpu-build.json').read_text())
    source=ROOT/'Naruto - Ninja Council 3 (USA).nds'
    target=ROOT/'workbench/party-mode/build/nc3-party-cpu-research.nds'
    assert sha(source)==report['source_sha256'] and sha(target)==report['target_sha256']
    for name,digest in build['source_files_sha256'].items():assert sha(ROOT/name)==digest
    patch=DIST/'nc3-party-cpu.bps'
    flips=ROOT/'tools/build/flips/flips'
    subprocess.run([str(flips),'--create','--bps-delta',str(source),str(target),str(patch)],check=True)
    applied=ROOT/'workbench/party-mode/build/release-roundtrip.nds'
    subprocess.run([str(flips),'--apply',str(patch),str(source),str(applied)],check=True)
    assert applied.read_bytes()==target.read_bytes()
    build['bps_roundtrip']=True;build['patch_sha256']=sha(patch);build['patch_size']=patch.stat().st_size
    (DIST/'party-cpu-build.json').write_text(json.dumps(build,indent=2)+'\n')
    entries={'nc3-party-cpu.bps':patch,'README.md':DIST/'PARTY_CPU_README.md',
             'party-cpu-build.json':DIST/'party-cpu-build.json',
             'party-cpu-runtime-validation.json':DIST/'party-cpu-runtime-validation.json'}
    for name in ['scripts/build_party_cpu.py','scripts/nc3_resources.py','scripts/party_cpu/mod.c',
                 'scripts/party_cpu/mod.ld','scripts/record_party_validation.py',
                 'scripts/package_party_cpu.py','scripts/emulator_control.py',
                 'scripts/controller_input.py','scripts/party_playtest.py',
                 'scripts/capture_party_cold_flow.py','scripts/capture_party_round.py',
                 'notes/PARTY_CPU_MODE.md']:
        entries[name]=ROOT/name
    checksums=''.join(sha(path)+'  '+name+'\n' for name,path in entries.items())
    checksum_path=DIST/'party-cpu-checksums.sha256';checksum_path.write_text(checksums)
    entries['checksums.sha256']=checksum_path
    archive=DIST/'nc3-party-cpu-prototype.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,path in entries.items():
            assert path.suffix not in ('.nds','.sav','.svs','.bin','.mln')
            z.write(path,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for line in z.read('checksums.sha256').decode().splitlines():
            digest,name=line.split('  ',1)
            assert hashlib.sha256(z.read(name)).hexdigest()==digest
    print(json.dumps({'patch':str(patch),'patch_bytes':patch.stat().st_size,
                      'bundle':str(archive),'bundle_bytes':archive.stat().st_size},indent=2))

if __name__=='__main__':main()
