"""Deliver exact existing signed418 bytes plus separately bound runtime evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).parent
OUTER_SHA='a73b059873dd0a62d752cf1c24540ff1931539d5dfd6f373ce18187c099d0af4'
APK_SHA='328757eb858a79f91883c0ba4e2884410baaf0b42730db5d62054679253674e4'
SOURCE='90cb67fd7c1c581e1f6d195adf1bb0c95b8fb42b'
PREFIX='query-cache-candidate/'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda:file.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build-zip',type=Path,required=True)
    parser.add_argument('--status',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.build_zip.resolve()==args.out.resolve() or sha(args.build_zip)!=OUTER_SHA:
        raise ValueError('Exact original successful signed418 artifact required')
    status=json.loads(args.status.read_text())
    if status.get('apk_sha256')!=APK_SHA or status.get('candidate_source')!=SOURCE or status.get('candidate_build')!=40383785065:
        raise ValueError('Exact source/build/APK evidence binding required')
    if status.get('release_accepted') is not False or status.get('final_lock') is not False:
        raise ValueError('Physical user acceptance remains required')
    evidence=sorted(ROOT.glob('*418*RESULT.json'))
    for path in evidence:
        value=json.loads(path.read_text())
        field='candidate_APK_sha256' if path.name=='SIGNED-418-BUILD-RESULT.json' else 'apk_sha256'
        if value.get(field)!=APK_SHA:raise ValueError('Mismatched candidate evidence: '+path.name)
    with ZipFile(args.build_zip) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate artifact paths')
        apks=[n for n in names if n.endswith('.apk')]
        if len(apks)!=1 or hashlib.sha256(archive.read(apks[0])).hexdigest()!=APK_SHA:
            raise ValueError('Exactly one actual signed APK is required')
        sums=archive.read(PREFIX+'SHA256SUMS').decode().splitlines()
        for line in sums:
            digest,name=line.split('  ',1)
            if hashlib.sha256(archive.read(PREFIX+name)).hexdigest()!=digest:
                raise ValueError('Exact component bytes differ: '+name)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(args.build_zip,args.out)
    with ZipFile(args.out,'a',compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT/'DELIVERY-418-INSTALLATION.txt',PREFIX+'INSTALLATION.txt')
        archive.write(args.status,PREFIX+'ACCEPTANCE-STATUS.json')
        for path in evidence:archive.write(path,PREFIX+'evidence/'+path.name)
        for path in sorted(ROOT.glob('*417*RESULT.json')):
            archive.write(path,PREFIX+'historical-417-evidence/'+path.name)
    with ZipFile(args.out) as archive:
        if archive.testzip() is not None:raise ValueError('Delivery ZIP integrity failed')
        if len(archive.namelist())!=len(set(archive.namelist())):raise ValueError('Duplicate delivery entries')
    digest=sha(args.out)
    args.out.with_suffix('.sha256').write_text(digest+'  '+args.out.name+'\n')
    print(json.dumps(dict(path=str(args.out),sha256=digest,size=args.out.stat().st_size,
        APK_bytes_changed=False,component_bytes_changed=False,release_accepted=False,final_lock=False)))


if __name__=='__main__':main()
