#!/usr/bin/env python3
"""Same-version, same-signer rollback: exact green engine/code before native start.

Original 2103365 artifacts are read-only inputs. This produces a distinct rollback
APK with versionCode 2103366, avoiding Android's downgrade restriction. Userdata
is never included, read or altered by this builder or the code transaction.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / 'repairs/android-checkpoint-shutdown'
sys.path[:0] = [str(R), str(ROOT / 'repairs/mobile-regressions-2103304')]
import runtime_delta
import participant_asset
import android_ci
from packaging_checks import DEX, SIGNATURE, dex_contract, require, manifest_tree, resource_ids, run

BASE = 'faf41ee1d35fe55140bb1e193089643cc9ac06ee'
GREEN = json.loads((R / 'system-stability-2103366/GREEN-2103365.json').read_text())
VERSION = 2103366
RELEASE = '1.0.9-2103365-Code-Rollback-RC1'
NAME = 'Infinity-2103366-2103365-Code-Rollback-RC1.apk'
sha = lambda data: hashlib.sha256(data).hexdigest()

def replace_once(text, before, after):
    require(text.count(before) == 1, 'Unexpected rollback source preimage: ' + before[:60])
    return text.replace(before, after)

def reverse_payload(old_zip, candidate_zip):
    with zipfile.ZipFile(io.BytesIO(old_zip)) as old, zipfile.ZipFile(io.BytesIO(candidate_zip)) as new:
        previous = json.loads(old.read('manifest.json'))
        plan = json.loads(new.read('manifest.json'))
        require(set(old.namelist()) == set(new.namelist()), 'Unexpected rollback script inventory')
        pins = {x['path']: x for x in previous['files']}
        for row in plan['files']:
            name = row['path']
            require(row['baseline'] == pins[name]['after'], 'Wrong rollback green preimage')
            row['candidate'] = row['after']
            row['after'] = pins[name]['after']
        files = {'manifest.json': (json.dumps(plan, sort_keys=True, separators=(',', ':'))+'\n').encode()}
        for row in plan['files']:
            files['payload/'+row['path']] = old.read('payload/'+row['path'])
            require(sha(files['payload/'+row['path']]) == row['after'], 'Wrong green rollback bytes')
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as z:
            for name, data in sorted(files.items()):
                entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.create_system=3;entry.external_attr=0o100644<<16
                z.writestr(entry,data)
        return output.getvalue()

def installer(source, asset, candidate):
    # Existing transaction/locking/fsync logic is reused. Only finite source pins,
    # one accepted code generation and its authentic journal recovery are added.
    source,n=re.subn(r'(?<![A-Z_])ASSET_SHA256 = "[0-9a-f]{64}"', 'ASSET_SHA256 = "'+sha(asset)+'"', source)
    require(n==1,'Unexpected installer digest')
    source=replace_once(source,'  private static final String ADDON =',
        '  private static final String CANDIDATE_ASSET_SHA256 = "'+sha(candidate)+'";\n  private static final String ADDON =')
    source=replace_once(source,'    String baseline;','    String baseline;\n    String candidate;')
    source=replace_once(source,'      change.after = checkedHash(file.getString("after"));',
        '      change.candidate = checkedHash(file.getString("candidate"));\n      change.after = checkedHash(file.getString("after"));')
    source=replace_once(source,'(change.baseline != null && change.baseline.equals(current))',
        '(change.baseline != null && change.baseline.equals(current)) || change.candidate.equals(current)')
    source=replace_once(source,'(expected.baseline != null && expected.baseline.equals(original))',
        '(expected.baseline != null && expected.baseline.equals(original)) || (expected.candidate != null && expected.candidate.equals(original))')
    recovery='''    if (CANDIDATE_ASSET_SHA256.equals(journal.getString("asset_sha256"))) {
      Payload prior = new Payload(); prior.assetHash = CANDIDATE_ASSET_SHA256;
      prior.addonXml = payload.addonXml;
      for (Change current : payload.changes) {
        Change old = new Change(); old.path = current.path; old.before = current.before;
        old.previous = current.previous; old.baseline = current.baseline;
        old.after = current.candidate;
        prior.changes.add(old); prior.byPath.put(old.path, old);
      }
      payload = prior;
    }
'''
    return replace_once(source,'    String phase = journal.getString("phase");',recovery+'    String phase = journal.getString("phase");')

def assets_and_sources(baseline, destination):
    require(sha(baseline.read_bytes()) == GREEN['sha256'], 'Wrong protected 2103365 APK')
    destination.mkdir(parents=True,exist_ok=True)
    result={}
    with zipfile.ZipFile(baseline) as apk:
        for name,component,candidate in (
            ('checkpoint-controller.zip','InfinityCheckpointAddonInstaller',participant_asset.build()),
            ('checkpoint-controller-20.zip','InfinityCheckpointController20Installer',android_ci.installed_build.build('script.infinity.commandcenter'))):
            asset=reverse_payload(apk.read('assets/infinity/'+name),candidate)
            (destination/name).write_bytes(asset)
            original=(R/'runtime/android/overlay/tools/android/packaging/xbmc/src'/(component+'.java.in')).read_text()
            (destination/(component+'.java.in')).write_text(installer(original,asset,candidate))
            result[name]=sha(asset)
    return result

def stage(args):
    args.out.mkdir(parents=True,exist_ok=True)
    baseline_manifest=json.loads(subprocess.check_output(['git','show',BASE+':repairs/android-checkpoint-shutdown/runtime/android/manifest.json']))
    runtime_delta.verify(args.source,baseline_manifest['after'])
    payloads=args.out/'code-rollback';assets=assets_and_sources(args.baseline,payloads)
    after=dict(baseline_manifest['after'])
    for component in ('InfinityCheckpointAddonInstaller','InfinityCheckpointController20Installer'):
        relative='tools/android/packaging/xbmc/src/'+component+'.java.in'
        (args.source/relative).write_bytes((payloads/(component+'.java.in')).read_bytes())
        after[relative]=sha((args.source/relative).read_bytes())
    runtime_delta.verify(args.source,after)
    proof={'schema':1,'source_commit':os.environ.get('GITHUB_SHA'), 'baseline_commit':BASE,
           'baseline_sha256':GREEN['sha256'],'source_after':after,'assets_sha256':assets,
           'userdata_touched':False,'native_recompiled':False,'device_accepted':False}
    (args.out/'ROLLBACK-SOURCE.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    factory=android_ci.factory
    factory.BASE_APK_SHA256=GREEN['sha256'];factory.VERSION_CODE=VERSION;factory.RELEASE=RELEASE
    factory.prepare(args.source.resolve(),args.baseline.resolve(),args.build.resolve(),args.out.resolve())
    for name in assets:
        target=args.build/'xbmc/assets/infinity'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((payloads/name).read_bytes())

def package(args):
    require(sha(args.baseline.read_bytes())==GREEN['sha256'],'Wrong protected APK')
    proof=json.loads((args.out/'ROLLBACK-SOURCE.json').read_text())
    runtime_delta.verify(args.source,proof['source_after'])
    donor=args.build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    require(resource_ids(bt/'aapt2',args.baseline,args.out/'green-resources.txt')==resource_ids(bt/'aapt2',donor,args.out/'rollback-resources.txt'),'Rollback resource ID drift')
    unsigned=args.out/'rollback-unsigned.apk'
    replacements={'assets/infinity/'+n:d for n,d in proof['assets_sha256'].items()}
    with zipfile.ZipFile(args.baseline) as old,zipfile.ZipFile(donor) as compiled:
        old_jni,old_classes=dex_contract(old);new_jni,new_classes=dex_contract(compiled)
        require(old_jni==new_jni,'Rollback JNI drift')
        prefixes=('Lcom/projectinfinity/kodi/InfinityCheckpointAddonInstaller$','Lcom/projectinfinity/kodi/InfinityCheckpointController20Installer$')
        require(all(c.startswith(prefixes) for c in old_classes^new_classes),'Rollback Java class drift')
        require({n for n in compiled.namelist() if n.startswith('assets/') and not n.endswith('/')}==set(replacements),'Unreviewed rollback assets')
        for n,digest in replacements.items():require(sha(compiled.read(n))==digest,'Rollback asset mismatch')
        with zipfile.ZipFile(unsigned,'w') as out:
            for info in old.infolist():
                if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename) or SIGNATURE.fullmatch(info.filename) or info.filename in replacements:continue
                out.writestr(copy.copy(info),old.read(info.filename))
            for info in compiled.infolist():
                if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename) or info.filename in replacements:out.writestr(copy.copy(info),compiled.read(info.filename))
    old_manifest=manifest_tree(run(bt/'aapt','dump','xmltree',args.baseline,'AndroidManifest.xml',output=args.out/'green-manifest.txt'))
    new_manifest=manifest_tree(run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=args.out/'rollback-manifest.txt'))
    for m in (old_manifest,new_manifest):
        for key in ('android:versionCode','android:versionName'):m['attrs'].pop(key,None)
    require(old_manifest==new_manifest,'Rollback manifest drift beyond version')
    for name in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):require(bool(os.environ.get(name)),'Permanent signer unavailable')
    final=args.out/NAME;run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    certificate=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=args.out/'rollback-signer.txt')
    require(GREEN['signer_certificate_sha256'] in certificate.lower(),'Rollback signer drift')
    badging=run(bt/'aapt','dump','badging',final,output=args.out/'rollback-badging.txt')
    require("versionCode='2103366' versionName='"+RELEASE+"'" in badging,'Wrong rollback identity')
    require('application-debuggable' not in badging,'Debuggable rollback')
    with zipfile.ZipFile(args.baseline) as old,zipfile.ZipFile(final) as new:
        names={n for n in old.namelist() if not SIGNATURE.fullmatch(n)}
        require(names=={n for n in new.namelist() if not SIGNATURE.fullmatch(n)},'Rollback APK inventory drift')
        kept={n for n in names if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and n not in replacements}
        for n in kept:require(old.read(n)==new.read(n),'Protected rollback payload changed: '+n)
        require(sha(new.read('lib/arm64-v8a/libkodi.so'))==GREEN['native_packaged_sha256'],'Wrong rollback engine')
        require(new.testzip() is None,'Rollback ZIP integrity failure')
    proof.update(apk=NAME,apk_sha256=sha(final.read_bytes()),version_code=VERSION,version_name=RELEASE,
                 certificate_sha256=GREEN['signer_certificate_sha256'],protected_entries=len(kept),
                 original_native_and_state_formats_restored=True,physical_fold_verified=False)
    (args.out/'ROLLBACK-DELIVERY.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    unsigned.unlink()
    print('PASS same-signer rollback; exact green native/scripts, protected payload, userdata excluded; not Fold accepted')

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('stage','package'))
    for name in ('source','baseline','build','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();stage(a) if a.mode=='stage' else package(a)
if __name__=='__main__':main()
