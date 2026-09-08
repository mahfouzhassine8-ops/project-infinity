#!/usr/bin/env python3
"""Static cross-reference against #5's pinned Kodi source and native patches; NO compilation."""
from pathlib import Path
import argparse, re, shutil, subprocess, sys, tempfile
from g2_candidate6 import ROOT, NATIVE_METHODS, digest, spec

def verify(source: Path) -> None:
    s=spec()
    for name,h in s['upstream_file_hashes'].items():
        if digest((source/name).read_bytes())!=h:
            raise ValueError('Wrong upstream source: '+name)
    for name,h in s['reference_script_hashes'].items():
        if digest((ROOT/'scripts'/name).read_bytes())!=h:
            raise ValueError('Native reference patch differs from G2 #5: '+name)
    with tempfile.TemporaryDirectory(prefix='g2-native-ref-') as tmp:
        work=Path(tmp)
        for name in s['upstream_file_hashes']:
            p=work/'kodi'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
        for name in s['reference_script_hashes']:
            subprocess.run([sys.executable,str(ROOT/'scripts'/name)],cwd=work,check=True)
        activity=work/'kodi/xbmc/platform/android/activity'
        cpp=(activity/'JNIMainActivity.cpp').read_text()
        blocks={
            'Main':cpp.split('jclass cMain',1)[1].split('jclass cSettingsObserver',1)[0],
            'XBMCSettingsContentObserver':cpp.split('jclass cSettingsObserver',1)[1].split('jclass cInputDeviceListener',1)[0],
            'XBMCInputDeviceListener':cpp.split('jclass cInputDeviceListener',1)[1].split('void CJNIMainActivity::_onNewIntent',1)[0],
            'XBMCMainView':(activity/'JNIXBMCMainView.cpp').read_text(),
        }
        for name,text in blocks.items():
            actual={n+d for n,d in re.findall(r'\{"([^"\n]+)",\s*"([^"\n]+)"',text)}
            if actual!=NATIVE_METHODS[name]:raise ValueError('Registered native methods differ for '+name)
        if 'return 2; // Candidate D contract' not in cpp:
            raise ValueError('G2 native ABI is no longer version 2')
        if 'APP_PACKAGE com.projectinfinity.kodi' not in (work/'kodi/version.txt').read_text():
            raise ValueError('Native package identity differs')
    print('PASS: all 19 JNI registrations across four classes match G2 #5; six Infinity endpoints retain ABI v2. No native build.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    verify(p.parse_args().source)
