#!/usr/bin/env python3
"""Ensure freshly tested Java and every test source equal the locked 2103374 evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile

def unique(path, name):
    result=list(path.rglob(name));assert len(result)==1,(name,result);return result[0]

def snapshot(path):
    return {p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--locked',type=Path,required=True);p.add_argument('--fresh',type=Path,required=True);p.add_argument('--build',type=Path,required=True)
    args=p.parse_args()
    original=json.loads(unique(args.locked,'SOURCE-PRESERVATION.json').read_text())['after']
    current=json.loads(unique(args.fresh,'SOURCE-PRESERVATION.json').read_text())['after']
    assert original==current and len(current)==264,'Fresh test runtime differs from locked 2103374'
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        with tarfile.open(unique(args.locked,'test-source.tar.gz')) as archive:
            for member in archive.getmembers():
                assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts and (member.isfile() or member.isdir())
            archive.extractall(root)
        saved=snapshot(root/'test');fresh=snapshot(args.build/'xbmc/src/test')
        assert saved==fresh,'A locked 2103374 regression source or fixture changed'
    receipt={'source_files_equal_to_locked_2103374':264,'all_207_test_sources_and_fixtures_equal':True,'original_regression_sources_edited':False,'physical_device_verified':False}
    (args.fresh/'ANDROID-2103374-PARENT-PRESERVATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: 264 runtime source files and all locked 207 test sources/fixtures are exact')

if __name__=='__main__':main()
