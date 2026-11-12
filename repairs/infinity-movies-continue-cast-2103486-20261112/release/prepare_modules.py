"""Exact signed86 -> complete candidate/recovery modules; no signing/installer.

Uses byte-identical original manifest tooling and public key. Original sources
are never installed/executed here; profiles, data and providers are not inputs.
Version labels below are module generations only, not APK reservations.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse,hashlib,importlib.util,json,shutil,subprocess,tempfile

TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[1]
LOCK='e1ef672a6f24aed6c19a14ab96d2df6fe3380460'
BASE='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
CC='script.infinity.commandcenter'
MANIFEST='INFINITY-MODULES.v1'
TOOLROOT='repairs/infinity-final-closure-2103407/'
TOOLS={'module_bundle.py':'e74faeb0636e7a3f2bc85ba6b70c6eebf948121e3ac06e85cf42267698ac97c1',
       'FIRSTPARTY-COMPOSITION-PLAN.json':'ec89814db22a4bcca251c8453b3bf48bc440e41499d84e13839785904461cfc6',
       'ORIGINAL-INFINITY-PUBLIC-KEY.pem':'bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8'}
CHANGED={'experience.py','plugin.py','service.py','default.py'}
ADDED={'cast_runtime.py'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def hashes(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
def stage(apk,out):
    assert not out.exists(),'Fresh staging required'
    with apk.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==BASE
    with tempfile.TemporaryDirectory(prefix='infinity86-manifest-tools-') as temporary:
        tools=Path(temporary)
        for name,wanted in TOOLS.items():
            raw=subprocess.check_output(['git','show',LOCK+':'+TOOLROOT+name],cwd=ROOT)
            assert sha(raw)==wanted,'Original manifest tool changed'
            (tools/name).write_bytes(raw)
        spec=importlib.util.spec_from_file_location('unchanged_original_module_bundle',tools/'module_bundle.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        baseline=out/'baseline-modules'
        with ZipFile(apk) as z:
            assert len(z.namelist())==len(set(z.namelist())),'No duplicate baseline ZIP members'
            for name in z.namelist():
                if not name.startswith('assets/addons/') or name.endswith('/'):continue
                relative=name[len('assets/addons/'):]
                if relative.split('/')[0] not in module.IDS:continue
                assert module.safe(relative)
                target=baseline/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
        original,before=module.build(baseline)
        assert len(before)==80 and sha(original)=='c67327c9683ec21be4aae58fe9add45d04372c91b16f1e1b2ee49e5dca50f2b9'
        assert original==(baseline/CC/MANIFEST).read_bytes(),'Complete signed86 manifest/source generation required'
        subprocess.run(['openssl','dgst','-sha256','-verify',str(tools/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
            '-signature',str(baseline/CC/(MANIFEST+'.sig')),str(baseline/CC/MANIFEST)],check=True,capture_output=True)
        source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        entries={}
        for label,version in [('candidate','0.3.5.81'),('recovery','0.3.5.82')]:
            work=out/label;modules=work/'modules';shutil.copytree(baseline,modules)
            if label=='candidate':
                for name in CHANGED|ADDED:(modules/CC/name).write_bytes((TASK/'overlay'/CC/name).read_bytes())
            addon=modules/CC/'addon.xml';raw=addon.read_bytes();assert raw.count(b'version="0.3.5.78"')==1
            addon.write_bytes(raw.replace(b'version="0.3.5.78"',('version="'+version+'"').encode(),1))
            (modules/CC/(MANIFEST+'.sig')).unlink()
            payload,files=module.build(modules)
            expected={CC+'/addon.xml'}|({CC+'/'+n for n in CHANGED} if label=='candidate' else set())
            assert {name for name in before if before[name]!=files.get(name)}==expected
            assert set(files)-set(before)==({CC+'/'+n for n in ADDED} if label=='candidate' else set())
            assert not set(before)-set(files) and len(files)==(81 if label=='candidate' else 80)
            (modules/CC/MANIFEST).write_bytes(payload)
            record=dict(schema=1,label=label,baseline=2103486,baseline_APK_sha256=BASE,baseline_lock=LOCK,
                source_commit=source,CC_version=version,files=len(files),manifest_sha256=sha(payload),modules=hashes(modules),
                code_restores_exact_2103486=label=='recovery',original_baseline_signature_verified=True,
                signature='PENDING_ORIGINAL_SignInfinityModules',APK=False,APK_version_reserved=False,owner_installable=False,
                protected_data_read=False,provider_changes=False,shutdown_changes=False,Cobra_changes=False)
            (work/'INPUTS.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
            entries[label]=sha((work/'INPUTS.json').read_bytes())
        report=dict(schema=1,baseline=2103486,baseline_APK_sha256=BASE,original_tools=TOOLS,inputs=entries,
            candidate_source={n:sha((TASK/'overlay'/CC/n).read_bytes()) for n in sorted(CHANGED|ADDED)},
            scope='Complete canonical 81-source candidate and exact-code 80-source forward recovery; no key access or installer',
            registry_mutated=False,APK=False,original_signer='UNCHANGED_SignInfinityModules.java')
        (out/'PREPARATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print('PASS_SIGNED86_BASELINE_AND_COMPLETE_CANDIDATE81_RECOVERY80_STAGING; NOT_SIGNED_NOT_INSTALLABLE')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apk',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();stage(args.apk,args.out)
