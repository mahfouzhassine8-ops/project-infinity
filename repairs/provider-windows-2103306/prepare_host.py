#!/usr/bin/env python3
"""Reconstruct only the three audited preimages for fast host tests.

Not a native build recipe. The native job reconstructs the entire lineage and
must match the exact complete source receipt shipped with locked APK 2103305.
"""
from pathlib import Path
import argparse
import importlib.util
import hashlib


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    here=Path(__file__).resolve().parent;root=here.parents[1]
    native=module(root/'repairs/native-responsive-2103290/native_layout.py','native3290')
    retained=module(root/'repairs/inplace-reflow-2103291/inplace_reflow.py','retained3291')
    from native_patch import FILES,LOCKED_PREIMAGES,once
    for name in FILES:
        text=(here/'fixtures/kodi'/name).read_text()
        if name==FILES[0]:text=retained.patch_skin_h(native.patch_skin_h(text))
        if name==FILES[1]:
            text=retained.patch_skin_cpp(native.patch_skin_cpp(text))
            text=once(once(text,'#include "Skin.h"','#include "Skin.h"\n#if defined(TARGET_ANDROID)\n'
                '#include "platform/android/activity/InfinityResponsiveness.h"\n#endif'),
                'void CSkinInfo::Start()\n{','void CSkinInfo::Start()\n{\n#if defined(TARGET_ANDROID)\n'
                '  ++InfinityHealth::skinGeneration;\n#endif')
        assert hashlib.sha256(text.encode()).hexdigest()==LOCKED_PREIMAGES[name],name
        file=a.output/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(text)
    print('PASS: all three host preimages match exact 2103305 native source hashes')


if __name__=='__main__':main()
