"""Selected install-over and forward-recovery checks on unchanged Java code.

Host filesystem/Android API transport only; never packaged into the APK.
Does not claim Android, provider, lifecycle, or physical Fold acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FIRST=ROOT/'repairs/infinity-final-closure-2103407'
sys.path.insert(0,str(FIRST))
import module_dex
import module_bundle
CC='script.infinity.commandcenter'
MANIFEST='INFINITY-MODULES.v1'

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}

def extract_prepared(prepared,target):
    """Read original-key signed modules from authenticated owner artifacts."""
    with ZipFile(prepared/'components/INFINITY.zip') as z:
        for name in z.namelist():
            if any(name.startswith('payload/assets/addons/'+aid+'/') for aid in module_bundle.IDS) and not name.endswith('/'):
                dest=target/name.removeprefix('payload/assets/addons/')
                assert '..' not in dest.parts
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))

def audit(parent,candidate,recovery,current,out):
    assert not out.exists();out.mkdir(parents=True)
    reference=json.loads((ROOT/'repairs/infinity-2103460-nine-corrections-20261106/fold-regressions/CC-AUDIT-REFERENCE.json').read_text())
    source=module_dex.source()
    assert hashlib.sha256(source.encode()).hexdigest()==reference['java_source_sha256']
    host={str(p.relative_to(FIRST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (FIRST/'host-java').rglob('*.java')}
    assert host==reference['host_java_sha256']
    rows=[]
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        temp=Path(temporary);base=temp/'base';base.mkdir()
        with ZipFile(parent) as z:
            for name in z.namelist():
                if any(name.startswith('assets/addons/'+aid+'/') for aid in module_bundle.IDS) and not name.endswith('/'):
                    dest=base/name.removeprefix('assets/addons/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
        shutil.rmtree(base/CC)
        with ZipFile(current/(CC+'-0.3.5.61-2103460-corrective.zip')) as z:
            z.extractall(base)
        versions={61:base}
        for version,prepared in [(62,candidate),(63,recovery)]:
            directory=temp/str(version)/'assets/addons';directory.mkdir(parents=True)
            extract_prepared(prepared,directory);versions[version]=directory
        for version,directory in versions.items():
            payload,files=module_bundle.build(directory)
            assert len(files)==78 and payload==(directory/CC/MANIFEST).read_bytes()
            assert payload.splitlines()[1]==('package\t0.3.5.'+str(version)).encode()
            subprocess.run(['openssl','dgst','-sha256','-verify',str(FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'),'-signature',str(directory/CC/(MANIFEST+'.sig')),str(directory/CC/MANIFEST)],check=True,capture_output=True)
        # Forward recovery differs from current61 only in authenticated version
        # metadata; all functional controller/shim source must be identical.
        old,restored=hashes(base),hashes(versions[63])
        assert old.keys()==restored.keys()
        assert {p for p in old if old[p]!=restored[p]}=={CC+'/'+p for p in ('addon.xml',MANIFEST,MANIFEST+'.sig')}
        java=temp/'InfinityInstalledCheckpointInstaller.java';java.write_text(source)
        classes=temp/'classes';classes.mkdir()
        subprocess.run(['javac','--release','8','-g:none','-d',str(classes),str(java),*map(str,(FIRST/'host-java').rglob('*.java'))],check=True)
        def fixture(label,version=61):
            storage=temp/label;shutil.copytree(versions[version],storage/'.kodi/addons')
            data=storage/'.kodi/userdata/addon_data/plugin.video.sentinel/settings.xml'
            data.parent.mkdir(parents=True);data.write_bytes(b'<settings>preserve user data</settings>')
            unknown=storage/'.kodi/addons'/CC/'user-retained-file.txt';unknown.write_bytes(b'preserve unknown unlisted source')
            return storage,data,unknown
        def call(storage,version=62,assets=None):
            return subprocess.run(['java','-cp',str(classes),'com.projectinfinity.kodi.Main',str(storage),str(assets or versions[version].parent)],capture_output=True,text=True)
        def complete(storage,version):
            assert all((storage/'.kodi/addons'/p).read_bytes()==(versions[version]/p).read_bytes() for p in hashes(versions[version]))
        def passing(label,storage,data,unknown,version,**details):
            result=call(storage,version)
            assert result.returncode==0,(label,result.stderr)
            assert 'VERIFIED_VERSION=0.3.5.'+str(version) in result.stdout
            complete(storage,version)
            assert data.read_bytes()==b'<settings>preserve user data</settings>'
            assert unknown.read_bytes()==b'preserve unknown unlisted source'
            rows.append(dict(case=label,status='PASS_REAL_JAVA_HOST',version=version,user_data_and_unlisted_source_preserved=True,**details))
        storage,data,unknown=fixture('normal61_to62')
        passing('authenticated61_to62_upgrade',storage,data,unknown,62)
        before=hashes(storage);passing('same62_noop',storage,data,unknown,62);assert hashes(storage)==before
        passing('authenticated62_to63_forward_recovery',storage,data,unknown,63,all_functional61_source_restored=True)
        before=hashes(storage);result=call(storage,62)
        assert result.returncode==0 and 'VERIFIED_VERSION=0.3.5.63' in result.stdout and hashes(storage)==before
        rows.append(dict(case='older62_APK_retains_valid63',status='PASS_NO_DOWNGRADE',all_files_preserved=True))
        storage,data,unknown=fixture('known_partial_source')
        leaf=CC+'/infinity_search.py'
        assert (base/leaf).read_bytes()!=(versions[62]/leaf).read_bytes()
        (storage/'.kodi/addons'/leaf).write_bytes((versions[62]/leaf).read_bytes())
        passing('signed61_pair_and_known62_partial_source_resume',storage,data,unknown,62)
        for label,change in [
            ('unknown_known_source',lambda root:(root/CC/'infinity_search.py').write_bytes(b'unknown source must remain')),
            ('unmatched_partial_signature',lambda root:(root/CC/(MANIFEST+'.sig')).write_bytes((versions[62]/CC/(MANIFEST+'.sig')).read_bytes())),
            ('missing_installed_signature',lambda root:(root/CC/(MANIFEST+'.sig')).unlink()),
        ]:
            storage,data,unknown=fixture(label);change(storage/'.kodi/addons');before=hashes(storage)
            result=call(storage);assert result.returncode!=0,(label,result.stdout)
            assert hashes(storage)==before,'REFUSAL_MUST_PRESERVE_ALL_SOURCE_AND_DATA'
            rows.append(dict(case=label,status='REFUSED_AS_REQUIRED',all_files_preserved=True,reason=result.stderr.strip()))
        storage,data,unknown=fixture('tampered_APK_asset')
        damaged=temp/'tampered/assets';shutil.copytree(versions[62].parent,damaged)
        (damaged/'addons'/CC/'infinity_search.py').write_bytes(b'asset not in signed inventory')
        before=hashes(storage);result=call(storage,assets=damaged)
        assert result.returncode!=0 and hashes(storage)==before
        rows.append(dict(case='signed_manifest_but_tampered_APK_source',status='REFUSED_AS_REQUIRED',all_files_preserved=True,reason=result.stderr.strip()))
    report=dict(status='PASS_NINE_FOCUSED_REAL_JAVA_UPGRADE_AND_RECOVERY_CASES',cases=rows,
                java_source_sha256=hashlib.sha256(source.encode()).hexdigest(),host_transport_sha256=host,
                original_installer_changed=False,APK_or_DEX_changed_by_test=False,signing_keys_accessed=False,
                Android='NOT_RUN_BY_HOST_TEST',Fold='NOT_RUN',shutdown='NOT_SELECTED')
    assert len(rows)==9
    (out/'MODULE-UPGRADE-RECOVERY.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('parent','candidate','recovery','current','out'):p.add_argument('--'+n,type=Path,required=True)
    audit(**vars(p.parse_args()))
