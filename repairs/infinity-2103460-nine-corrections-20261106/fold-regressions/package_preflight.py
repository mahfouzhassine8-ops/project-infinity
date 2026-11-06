"""Assemble forward skin264 / recovery265 through the existing original signer.

No keys or signing implementation here. The exact signed262 quick-update
artifact is the functional/recovery reference; signed460 seeds unchanged shims.
APK462 itself is neither repackaged nor modified.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
from zipfile import ZipFile
import xml.etree.ElementTree as ET

PREVIOUS_ARTIFACT=13495017909
PREVIOUS_RUN=42202256097
PREVIOUS_SHA='3bfb47761e7e2aad2f24c5f24967ec8e8ba1da43b97cdbe299e2cf93703d4298'
REFERENCE='9ab8ec01ea552c89fa64afaac4b3bf9d82d53893'
PREFIX='repairs/infinity-2103460-nine-corrections-20261106/'

def prepare(p,apk,out):
    assert p.sha(apk)==p.BASE,'EXACT_SIGNED460_SEED_REQUIRED'
    assert p.run('git','branch','--show-current').strip()=='work/infinity-2103460-nine-corrections-20261106'
    p.run('git','merge-base','--is-ancestor',REFERENCE,'HEAD')
    assert p.run('git','status','--porcelain','--untracked-files=no').strip()=='','COMMITTED_REVIEWED_SOURCE_REQUIRED'
    assert not out.exists(),'fresh output required'
    old_inventory=json.loads(p.run('git','show',REFERENCE+':'+PREFIX+'SOURCE-INVENTORY.json'))
    inventory=json.loads((p.HERE.parent/'SOURCE-INVENTORY.json').read_text())
    extra={str(Path('repairs/infinity-master-corrective-20261105/overlay/assets/addons')/p.CC/n) for n in ('addon.xml','context.py','plugin.py')}
    assert set(inventory['changed_source_files'])==set(old_inventory['changed_source_files'])|extra
    runtime={str(Path('repairs/infinity-master-corrective-20261105/overlay/assets/addons')/p.CC/n) for n in ('addon.xml','context.py','plugin.py','infinity_search.py')}
    runtime|={str(Path('repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons')/p.SKIN/'unified'/n) for n in ('DialogVideoInfo.xml','Includes_InfinityMediaLists.xml')}
    changed=p.run('git','diff','--name-only',REFERENCE,'HEAD').splitlines()
    assert all(n in runtime or n==PREFIX+'SOURCE-INVENTORY.json' or n==PREFIX+'quick-update/package_updates.py' or n.startswith(PREFIX+'fold-regressions/') for n in changed),'UNAUTHORIZED_SOURCE_DIFFERENCE'
    for source in (*inventory['changed_source_files'],PREFIX+'quick-update/package_updates.py',
                   PREFIX+'fold-regressions/package_preflight.py',PREFIX+'SOURCE-INVENTORY.json'):
        assert (p.ROOT/source).read_bytes()==subprocess.check_output(['git','show','HEAD:'+source],cwd=p.ROOT),'SOURCE_NOT_BOUND_TO_HEAD:'+source
    # Signer, authority, native sources and all protected runtime ownership stay frozen.
    for n in ('repairs/dual-experience-isolation-2103420/release-authority.json',
              'repairs/dual-experience-isolation-2103420/signer-policy.json',
              '.github/workflows/infinity-combined-release.yml',
              PREFIX+'quick-update/SignInfinityQuickUpdate.java'):
        assert (p.ROOT/n).read_bytes()==subprocess.check_output(['git','show',REFERENCE+':'+n],cwd=p.ROOT),n
    out.mkdir(parents=True);addons=out/'addons';addons.mkdir()
    with ZipFile(apk) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        for n in z.namelist():
            if n.startswith(tuple('assets/addons/'+a+'/' for a in (*p.module_bundle.IDS,p.SKIN))) and not n.endswith('/'):
                f=addons/n.removeprefix('assets/addons/');assert '..' not in f.parts
                f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
    previous=out/'previous-authenticated.zip'
    local=os.environ.get('INFINITY_FOLD_PREVIOUS_ARCHIVE')
    if local:
        assert p.sha(local)==PREVIOUS_SHA
        shutil.copyfile(local,previous)
    else:
        run=json.loads(p.run('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{PREVIOUS_RUN}'))
        assert run['workflow_id']==397702717 and run['conclusion']=='success' and run['head_sha']=='10c261ac06cd3337a755db984a379edd7d849fd7'
        with previous.open('xb') as target:
            done=subprocess.run(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{PREVIOUS_ARTIFACT}/zip'],stdout=target,stderr=subprocess.PIPE)
        assert done.returncode==0,'PREVIOUS_AUTHENTICATED_ARTIFACT_DOWNLOAD_FAILED'
    assert p.sha(previous)==PREVIOUS_SHA,'EXACT262_PREDECESSOR_REQUIRED'
    with ZipFile(previous) as bundle:
        assert bundle.testzip() is None and len(bundle.namelist())==len(set(bundle.namelist()))
        for leaf in ('INFINITY-QUICK-UPDATE.v1','INFINITY-QUICK-UPDATE.v1.sig'):(out/leaf).write_bytes(bundle.read(leaf))
        for aid,version in ((p.CC,'0.3.5.61'),(p.SKIN,'1.0.5.262')):
            name=aid+'-'+version+'-2103460-corrective.zip'
            f=out/name;f.write_bytes(bundle.read(name))
            with ZipFile(f) as z:
                assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
                assert {n.split('/')[0] for n in z.namelist()}=={aid}
                shutil.rmtree(addons/aid)
                for entry in z.infolist():
                    if entry.is_dir():continue
                    assert not entry.filename.startswith('/') and '..' not in Path(entry.filename).parts
                    assert not stat.S_ISLNK(entry.external_attr>>16)
                    target=addons/entry.filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(entry))
    p.run('openssl','dgst','-sha256','-verify',p.FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',out/'INFINITY-QUICK-UPDATE.v1.sig',out/'INFINITY-QUICK-UPDATE.v1')
    protected={str(f.relative_to(addons)):p.sha(f) for f in addons.rglob('*') if f.is_file()}
    marker=addons/p.CC/p.module_bundle.MANIFEST
    assert p.module_bundle.build(p.addons_for_build(addons,out))[0]==marker.read_bytes()
    p.run('openssl','dgst','-sha256','-verify',p.FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',str(marker)+'.sig',marker)
    assert ET.parse(addons/p.CC/'addon.xml').getroot().get('version')==p.VERSION
    assert ET.parse(addons/p.SKIN/'addon.xml').getroot().get('version')=='1.0.5.262'
    for rel,want in json.loads((addons/p.SKIN/'Infinity-Protected-Manifest.json').read_text())['protected_files'].items():
        assert p.sha(addons/p.SKIN/rel)==want,'PREDECESSOR_SKIN_INTEGRITY:'+rel
    recovery=out/'recovery-addons';recovery.mkdir()
    for aid in (p.CC,p.SKIN):shutil.copytree(addons/aid,recovery/aid)
    changes={}
    for source,row in inventory['changed_source_files'].items():
        rel=source.split('/overlay/assets/addons/',1)[1]
        assert rel.startswith((p.CC+'/',p.SKIN+'/')) and p.sha(p.ROOT/source)==row['candidate_sha256']
        if p.sha(p.ROOT/source)!=protected[rel]:
            assert source in runtime,'UNREVIEWED_RUNTIME_DELTA:'+source
            (addons/rel).write_bytes((p.ROOT/source).read_bytes());changes[rel]=p.sha(addons/rel)
    assert len(changes)==6,'EXACT_SIX_REMAINING_RUNTIME_FILES'
    for base,number in ((addons,264),(recovery,265)):
        skin=base/p.SKIN;xml=skin/'addon.xml';raw=xml.read_bytes()
        assert b'version="1.0.5.262"' in raw
        xml.write_bytes(raw.replace(b'version="1.0.5.262"',f'version="1.0.5.{number}"'.encode(),1))
        for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
            f=skin/leaf;d=json.loads(f.read_text());d.update(candidate=number,candidate_locked=False)
            if 'physical_device_verified' in d:d['physical_device_verified']=False
            for k in ('version','candidate_version','skin_version'):
                if k in d:d[k]=f'1.0.5.{number}'
            if 'protected_files' in d:
                for rel in d['protected_files']:
                    if (skin/rel).is_file():d['protected_files'][rel]=p.sha(skin/rel)
            p.save(f,d)
        hashes=json.loads((skin/'Infinity-Protected-Manifest.json').read_text())['protected_files'];assert len(hashes)==948
        for rel,want in hashes.items():assert p.sha(skin/rel)==want,'NEW_SKIN_INTEGRITY:'+rel
    for leaf in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'):changes[p.SKIN+'/'+leaf]=p.sha(addons/p.SKIN/leaf)
    payload,files=p.module_bundle.build(p.addons_for_build(addons,out));assert len(files)==78
    marker.write_bytes(payload);Path(str(marker)+'.sig').unlink();changes[p.CC+'/'+p.module_bundle.MANIFEST]=p.sha(marker)
    for rel,want in protected.items():
        if rel not in changes and rel!=p.CC+'/'+p.module_bundle.MANIFEST+'.sig':assert p.sha(addons/rel)==want,rel
        if rel.startswith((p.CC+'/',p.SKIN+'/')) and rel not in {p.SKIN+'/'+n for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json')}:
            assert p.sha(recovery/rel)==want,'RECOVERY_FUNCTIONAL_DIFFERENCE:'+rel
    for f in (addons/p.SKIN).rglob('*.xml'):ET.parse(f)
    for leaf in ('default.py','library_navigation.py','infinity_search.py','context.py','plugin.py'):compile((addons/p.CC/leaf).read_bytes(),leaf,'exec')
    p.save(out/'PREFLIGHT.json',dict(status='PASS_EXACT2103460_ADDON_SOURCE_AND_METADATA',
        source=p.run('git','rev-parse','HEAD').strip(),baseline_sha256=p.BASE,
        seed_apk_path=str(Path(apk).resolve()),
        device_APK=2103462,device_identity='USER_CONFIRMED',functional_reference='authenticated skin262 and CC61 artifact13495017909',
        predecessor_artifact_sha256=PREVIOUS_SHA,commandcenter_version=p.VERSION,skin_version=p.SKIN_VERSION,
        recovery_skin_version='1.0.5.265',changes=changes,protected=protected,module_file_count=78,
        old_module_manifest_sha256=protected[p.CC+'/'+p.module_bundle.MANIFEST],
        Downloads_native_required_sha256='fadfb1a08e3d125958a77d393c1d66453ec3e9c91aac3349ec5806c67c17694d',
        native_changed=False,APK_produced=False,Android='NOT_RUN',all_nine_complete=False,
        known_limitations=['Search All settings-history/ABA validation remains strict and unresolved',
                           'Actual provider-heading regression not reproduced on Android',
                           'Repeated native Search crash stability NOT RUN; no speculative engine fix']))
    print('PASS authenticated262 reference, six runtime file deltas, exact protected sources and forward265 recovery; Android NOT RUN')
