#!/usr/bin/env python3
"""Actual filesystem identity tests; run inside a disposable root mount namespace.

The host executable is only a topology fixture. Android command behavior is
verified separately on the real system image; it is not inferred from this test.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='infinity-vendor-contract-') as temp:
        root = Path(temp)
        source = root/'check.cpp'
        source.write_text('''#include "InfinityReadonlyPlatformCommand.h"
#include <iostream>
int main(int argc, char** argv) {
  if (argc != 3) return 2;
  bool actual=InfinityReadonlyPlatformCommand::VendorUname(argv[1]);
  std::cout << actual << "\\n";
  return actual == (argv[2][0]=='1') ? 0 : 1;
}
''')
        binary = root/'check'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                        '-I'+str(HERE/'runtime/xbmc/interfaces/python'),str(source),'-o',str(binary)], check=True)
        # Mounting occurs only in the CI job's private namespace. Never modify
        # a machine's existing vendor contents.
        vendor = Path('/vendor')
        vendor.mkdir(exist_ok=True)
        results=[]
        for name,readonly,kind,expected in [
            ('immutable-os-applet',True,'valid',True),
            ('writable-mount',False,'valid',False),
            ('wrong-target',True,'wrong',False),
            ('ordinary-file',True,'ordinary',False),
            ('writable-binary',True,'writable',False),
            ('unowned-binary',True,'unowned',False),
            ('missing-target',True,'missing',False),
        ]:
            fixture=root/name; (fixture/'bin').mkdir(parents=True)
            target=fixture/'bin/toybox_vendor'
            if kind!='missing':
                shutil.copyfile('/usr/bin/uname',target);target.chmod(0o755)
            link=fixture/'bin/uname'
            if kind=='ordinary': shutil.copyfile('/usr/bin/uname',link);link.chmod(0o755)
            else: link.symlink_to('other' if kind=='wrong' else 'toybox_vendor')
            if kind=='wrong': shutil.copyfile('/usr/bin/uname',fixture/'bin/other')
            if kind=='writable':target.chmod(0o777)
            if kind=='unowned':os.chown(target,65534,65534)
            subprocess.run(['mount','--bind',str(fixture),str(vendor)],check=True)
            try:
                if readonly:subprocess.run(['mount','-o','remount,bind,ro',str(vendor)],check=True)
                result=subprocess.run([str(binary),'/vendor/bin/uname',str(int(expected))],capture_output=True,text=True)
                results.append(dict(case=name,passed=result.returncode==0,observed=result.stdout.strip()))
                assert result.returncode==0,(name,result.stderr)
                for bad in ('/vendor/bin/toybox_vendor','/vendor/bin/../bin/uname','/tmp/uname'):
                    subprocess.run([str(binary),bad,'0'],check=True,capture_output=True)
            finally:subprocess.run(['umount',str(vendor)],check=True)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(dict(scope='real mount/symlink/owner checks; host topology only',
            results=results,passed=all(r['passed'] for r in results),physical_fold_verified=False),indent=2)+'\n')
        print('PASS: 7 actual vendor identity cases; alternate paths denied in every case')


if __name__=='__main__':main()
