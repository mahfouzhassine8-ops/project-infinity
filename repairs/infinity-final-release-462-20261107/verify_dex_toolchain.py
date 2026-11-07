"""Read-only class inventory with the original signing workflow's Java major.

No class normalization, hash exception, guard change, APK or DEX edit.
"""
from pathlib import Path
import argparse
import re
import subprocess
import sys
import json
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
from inventory import file_sha,load,save,disassemble,parse_dex,digest,canonical
from release_gate import require

def audit(parent,jars,out):
    require(not out.exists(),'FRESH_TOOLCHAIN_AUDIT');out.mkdir(parents=True)
    require(file_sha(parent)=='a24ffafd056db23aa9d433552e17d4362cc9dbc9dd568b086d84cabadae8c619','EXACT_SIGNED462_INPUT')
    java=subprocess.check_output(['java','-version'],stderr=subprocess.STDOUT,text=True)
    require(re.search(r'version "21\.',java),'ORIGINAL_SIGNER_JAVA21_REQUIRED')
    a=load(ROOT/'repairs/dual-experience-isolation-2103420/release-authority.json')
    require(a['generation']==50 and a['candidate_versionCode']==2103464,'EXACT_UNISSUED_ENGINEERING_CANDIDATE')
    disassemble(parent,jars,out/'dex')
    classes,_,_=parse_dex(out/'dex')
    expected={n.removeprefix('class:'):v for n,v in a['payload'].items() if n.startswith('class:')}
    require(classes.keys()==expected.keys(),'EXACT_ORIGINAL_CLASS_SET')
    differences=[n for n in classes if classes[n]['sha256']!=expected[n]['sha256']]
    require(not differences,'ORIGINAL_JAVA21_CLASS_HASH_MISMATCH:'+repr(differences[:10]))
    target='Landroidx/media3/common/util/Util;'
    require(classes[target]['sha256']=='e6838a660dc0f2ba70cb8656eabef8538ef9ae16d75bdf74b1bbeb44059723d1','EXACT_APPROVED_COBRA_CLASS')
    with ZipFile(parent) as z:dexes={n:digest(z.read(n)) for n in z.namelist() if re.fullmatch(r'classes[0-9]*\.dex',n)}
    report=dict(status='PASS_ALL_ORIGINAL_CLASS_HASHES_WITH_ORIGINAL_JAVA21',java=java,java_major=21,parent_apk_sha256=file_sha(parent),DEX=dexes,classes_checked=len(classes),class_hashes_sha256=digest(canonical({n:classes[n]['sha256'] for n in sorted(classes)})),class_differences=[],Cobra_classes_changed=[],APK_or_DEX_modified=False,guard_modified=False,hash_normalization=False,retained_refusal=dict(run=42426683249,artifact=13595313349,artifact_sha256='6d6e67abf0ca12aed1f598ca30976631aebad3c75637bf44ae54cd38824970c6',reason='Java17 baksmali float annotation differs from original Java21'),example=dict(class_name=target,java17_sha256='b64920f363e7ed8f65a084ddfc81b456ced2e59ce07b922687859fdedf5f0e79',java21_sha256=classes[target]['sha256'],unchanged_instruction='0x4d9b3063',java17_comment='3.25454944E8f',java21_comment='3.2545494E8f'),application_tests='NOT_RUN_SOURCE_AUDIT_ONLY',Android='NOT_RUN',Fold='NOT_RUN')
    save(out/'DEX-TOOLCHAIN-VERIFICATION.json',report)
    print(report['status'],len(classes))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('parent','jars','out'):p.add_argument('--'+n,type=Path,required=True)
    audit(**vars(p.parse_args()))
