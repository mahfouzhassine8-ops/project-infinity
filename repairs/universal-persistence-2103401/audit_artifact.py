"""Independently rehash downloaded sources/APK members and bound the recorder delta."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from zipfile import ZipFile

def digest(stream):
    value=hashlib.sha256()
    for data in iter(lambda:stream.read(1024*1024),b''):value.update(data)
    return value.hexdigest()

def file_hash(path):
    with path.open('rb') as stream:return digest(stream)

def members(path):
    result={}
    with ZipFile(path) as archive:
        assert len(set(archive.namelist()))==len(archive.namelist())
        for item in archive.infolist():
            with archive.open(item) as stream:result[item.filename]=digest(stream)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','input','protected','overlay','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--build-run',required=True)
    args=parser.parse_args();root=args.candidate
    base=json.loads((Path(__file__).with_name('BASELINE.json')).read_text())
    receipt=json.loads((root/'CANDIDATE.json').read_text())
    assert receipt['source_commit']==args.source_commit and receipt['build_run']==args.build_run
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1)
        assert Path(name).name==name and file_hash(root/name)==expected,name
    before=json.loads((args.input/'NATIVE-SOURCE-MAP.json').read_text())
    protected=json.loads((args.protected/'NATIVE-SOURCE-MAP.json').read_text())
    after=json.loads((root/'NATIVE-SOURCE-MAP.json').read_text())
    canonical=json.dumps(before,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()==base['source_map_sha256']
    assert len(after)==len(before)==base['source_count']==9404
    changed=sorted(n for n in after if before.get(n)!=after[n])
    assert changed==sorted(base['before'])
    with ZipFile(root/'Infinity-Universal-Source-and-Evidence.zip') as archive:
        assert sorted(n[7:] for n in archive.namelist() if n.startswith('native/'))==sorted(after)
        for name,expected in after.items():
            assert hashlib.sha256(archive.read('native/'+name)).hexdigest()==expected,name
            local=(args.overlay if name in changed else args.input/'native')/name
            assert file_hash(local)==expected,name
    parent=args.input/'Infinity-2103401-Fold-Corrective-EXPERIMENTAL.apk'
    baseline=args.protected/'Infinity-2103400-Fold-Corrective-EXPERIMENTAL.apk'
    apks=list(root.glob('*.apk'));assert len(apks)==1;apk=apks[0]
    assert file_hash(parent)==receipt['parent_sha256']=='17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6'
    assert file_hash(baseline)=='e1334ce46bc96edce76a8b7af2d3ebb9871ac7c351526ac2cc6cc58820da009a'
    assert file_hash(apk)==receipt['apk_sha256']
    old,new,original=members(parent),members(apk),members(baseline)
    delta=[dict(path=n,before=old.get(n),after=new.get(n)) for n in sorted(set(old)|set(new)) if old.get(n)!=new.get(n)]
    engine='lib/arm64-v8a/libkodi.so';recorder='lib/arm64-v8a/libinfinitycrash.so'
    expected={engine,recorder,'META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF'}
    assert {x['path'] for x in delta}==expected and len(old)==len(new)==7581
    assert delta==json.loads((root/'APK-DELTA.json').read_text())['changed']
    assert new[engine]==receipt['native_sha256']
    with ZipFile(parent) as a,ZipFile(apk) as b:
        prior,current=a.read(recorder),b.read(recorder)
        old_hash,new_hash=old[engine].encode(),new[engine].encode()
        assert prior.count(old_hash)==1 and prior.replace(old_hash,new_hash)==current
        offset=struct.unpack_from('<Q',prior,40)[0]
        size,count,strings=struct.unpack_from('<HHH',prior,58)
        sections=[struct.unpack_from('<IIQQQQIIQQ',prior,offset+i*size) for i in range(count)]
        names=prior[sections[strings][4]:sections[strings][4]+sections[strings][5]]
        ro=[x for x in sections if names[x[0]:].split(b'\0',1)[0]==b'.rodata'];assert len(ro)==1
        position=prior.index(old_hash);assert ro[0][4]<=position and position+64<=ro[0][4]+ro[0][5]
    result=dict(passed=True,candidate_apk_sha256=receipt['apk_sha256'],build_run=args.build_run,
        source_commit=args.source_commit,verified_source_files=9404,changed_source_files=changed,
        unchanged_source_files=9399,apk_changed_members=delta,apk_unchanged_member_count=7576,
        recorder_only_bounded_engine_hash_changed=True,dex_assets_manifest_other_libraries_identical=True,
        provider_code_changed=False,physical_fold_verified=False,final_lock=False)
    cumulative=dict(scope='Protected 2103400 to candidate; pre-existing 2103401 differences distinguished',
        candidate_sha256=receipt['apk_sha256'],
        apk_changed=[dict(path=n,before=original.get(n),after=new.get(n),origin='this repair changes parent member' if old.get(n)!=new.get(n) else 'pre-existing 2103401') for n in sorted(set(original)|set(new)) if original.get(n)!=new.get(n)],
        source_changed=[dict(path=n,before=protected.get(n),after=after.get(n),origin='this repair' if n in changed else 'pre-existing 2103401') for n in sorted(set(protected)|set(after)) if protected.get(n)!=after.get(n)])
    args.out.mkdir(parents=True,exist_ok=True)
    for name,value in [('INDEPENDENT-CANDIDATE-PRESERVATION.json',result),('CUMULATIVE-2103400-DELTA.json',cumulative)]:
        (args.out/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
