"""Final OLED chrome delta; reuse the fully verified 96 native engine and DEX.

No native source, native binary, class definition, provider or data mutation.
The originating native/ART proofs remain unchanged and retain their real commit.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'repairs/fold-targeted-2103396'))
import components96 as c
import delivery96 as previous

ORIGIN = '2d15e6ed2d4045f9ee041c81a8334afb780d2fd7'
ORIGIN_RUN = 39579955813
CODE = 2103397
NAME = '1.0.9-All-In-One-Bugfix-TEST0007'
FILENAME = 'Infinity-2103397-Fold-Corrective-EXPERIMENTAL.apk'
SURFACES = {'InfinityBrowserTop', 'InfinityBrowserIconTile', 'InfinityBrowserFooter'}
VERSIONS = {a:v for a,_,v in c.PACKAGES}
VERSIONS[c.SKIN] = '1.0.5.234'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def read_json(path):
    return json.loads(path.read_text())


def verify_origin(directory, tools):
    receipt = read_json(directory/'INFINITY-2103396-DELIVERY.json')
    c.require(receipt['source_commit'] == ORIGIN and receipt['version_code'] == 2103396,
              'exact originating source/run candidate required')
    apk = directory/'Infinity-2103396-Fold-Corrective-EXPERIMENTAL.apk'
    c.require(c.digest(apk) == receipt['apk_sha256'], 'originating signed APK mismatch')
    d,_,_=__import__('native96').old_adapters()
    signature = d.verify_signature(apk, tools)
    c.require(receipt['permanent_certificate_sha256'] == previous.CERT and
              receipt['signed_permanently'] and receipt['complete_native_engine_compiled'],
              'permanent signature and actual full native compilation required')
    # Verify every compiler input from the actual successful build, then keep
    # its original proof. Never fabricate a fresh compilation or change its SHA.
    archive = directory/'Infinity-2103396-Source-and-Build-Receipts.zip'
    with ZipFile(archive) as source:
        c.require(source.testzip() is None and len(source.namelist()) == len(set(source.namelist())),
                  'originating source archive corrupt')
        expected = json.loads(source.read('NATIVE-SOURCE-MAP.json'))
        names = {n[7:] for n in source.namelist() if n.startswith('native/') and not n.endswith('/')}
        c.require(len(names) == len(expected) == 9404 and names == set(expected),
                  'complete originating 9404-file inventory mandatory')
        for name, pin in expected.items():
            c.require(c.sha(source.read('native/'+name)) == pin, 'native compiler input drift '+name)
        engine_proof = json.loads(source.read('receipts/ENGINE-PROOF.json'))
        art = json.loads(source.read('receipts/ART-COMPONENT-VERIFICATION.json'))
        dex = json.loads(source.read('receipts/STARTUP-DEX-INTEGRATION.json'))
        c.require(engine_proof['source_commit'] == ORIGIN and
                  engine_proof['native_sha256'] == receipt['native_sha256'] and
                  engine_proof['complete_native_engine_compiled'], 'real engine compilation provenance absent')
        c.require(art['source_commit'] == dex['source_commit'] == ORIGIN and art['passed'] and
                  art['candidate_cases_passed'] == 45 and art['baseline_control_cases_passed'] == 1,
                  'originating actual Android17 execution proof mandatory')
        c.require(dex['fields']['encoded_values_and_presence_preserved'] and
                  dex['fields']['all_original_field_definitions_verified'], 'field preservation proof absent')
    with ZipFile(apk) as z:
        c.require(c.sha(z.read(previous.ENGINE)) == receipt['native_sha256'], 'compiled engine differs in APK')
        c.require(c.sha(z.read('classes.dex')) == dex['component_dex_sha256'], 'tested DEX differs in APK')
        c.require(c.sha(z.read('classes2.dex')) == previous.dex96.SHARD2, 'second DEX shard drift')
    return apk, receipt, signature, expected, engine_proof, art, dex


def skin_changes(parent):
    with ZipFile(parent) as z:
        before = {n[14:]:z.read(n) for n in z.namelist()
                  if n.startswith('assets/addons/'+c.SKIN+'/') and not n.endswith('/')}
    after = dict(before)
    count = 0
    for name, body in before.items():
        if not name.endswith('/Includes_InfinityBrowser223.xml'):
            continue
        root = ET.fromstring(body)
        found = set()
        for node in root.findall('variable'):
            if node.get('name') not in SURFACES:
                continue
            c.require(not any(v.get('condition') == c.prior.old.OLED_CONDITION
                              for v in node.findall('value')), 'OLED chrome already corrected')
            old_values = [(v.attrib.copy(), v.text) for v in node.findall('value')]
            value = ET.Element('value', {'condition':c.prior.old.OLED_CONDITION})
            value.text = 'FF000000'
            node.insert(0, value)
            c.require([(v.attrib.copy(),v.text) for v in node.findall('value')[1:]] == old_values,
                      'Light/Dark source values or order changed')
            found.add(node.get('name'))
        c.require(found == SURFACES, 'missing declared browser chrome surface '+name)
        after[name] = c.xml_bytes(root)
        count += 1
    c.require(count == 14, 'complete original skin profile family required')
    after[c.SKIN+'/addon.xml'] = c.once(after[c.SKIN+'/addon.xml'],
        b'version="1.0.5.233"', b'version="1.0.5.234"')
    for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
        key=c.SKIN+'/'+leaf;value=json.loads(after[key])
        value.update(candidate=234,skin_version='1.0.5.234',candidate_locked=False)
        for field in ('version','candidate_version'):
            if field in value:value[field]='1.0.5.234'
        if 'protected_files' in value:
            value['protected_files']={p:c.sha(after[c.SKIN+'/'+p]) for p in value['protected_files']}
        after[key]=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    changed={n:body for n,body in after.items() if before.get(n)!=body}
    c.require(len(changed)==17 and not any('cobra' in n.lower() for n in changed),
              'skin-only declared file delta required')
    for name,body in changed.items():
        if name.endswith('.xml'):ET.fromstring(body)
    return before, after, changed


def assemble(directory, out, commit):
    c.require(not out.exists() and re.fullmatch('[a-f0-9]{40}',commit), 'new destination/full source commit required')
    tools=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    parent, origin, signature, sources, engine_proof, art, dex=verify_origin(directory,tools)
    before,after,delta=skin_changes(parent)
    d,_,_=__import__('native96').old_adapters()
    c.require(all(os.environ.get(k) for k in d.KEYS),'permanent signing secrets mandatory; no fallback')
    manifest=d.module('final97_manifest',ROOT/'repairs/critical-preview-2103376/manifest_patch.py')
    manifest.PARENT_CODE=2103396;manifest.CODE=CODE
    manifest.PARENT_NAME=previous.NAME;manifest.NAME=NAME
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.infinity-final97-',dir=out.parent) as temporary:
        temp=Path(temporary);unsigned=temp/'unsigned.apk';signed=temp/FILENAME
        with ZipFile(parent) as z:
            patched,edits=manifest.patch(z.read('AndroidManifest.xml'))
            c.require(len(edits)==2 and {v['field'] for v in edits}=={'versionCode','versionName'},
                      'package identity/manifest scope changed')
            targets={'assets/addons/'+n:b for n,b in delta.items()}
            targets['AndroidManifest.xml']=patched
            evidence=json.loads(z.read('assets/infinity-2103395-components.json'))
            for name,body in delta.items():
                rel=name.split('/',1)[1]
                c.require(rel in evidence[c.SKIN],'changed source missing original fingerprint '+name)
                evidence[c.SKIN][rel]=c.sha(body)
            encoded=(json.dumps(evidence,sort_keys=True,separators=(',',':'))+'\n').encode()
            for code in (2103395,2103396,2103397):targets['assets/infinity-'+str(code)+'-components.json']=encoded
            with ZipFile(unsigned,'w',allowZip64=True) as result:
                for info in z.infolist():
                    if not previous.SIGNATURE.fullmatch(info.filename):
                        result.writestr(copy.copy(info),targets.get(info.filename,z.read(info)))
                for name in sorted(set(targets)-set(z.namelist())):
                    result.writestr(name,targets[name],compress_type=ZIP_DEFLATED,compresslevel=9)
        previous.verify_delta(parent,unsigned,targets)
        subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
        final_signature=d.verify_signature(signed,tools)
        changed=previous.verify_delta(parent,signed,targets)
        badging=d.command([tools/'aapt','dump','badging',signed])
        c.require("package: name='com.projectinfinity.kodi' versionCode='2103397'" in badging and
                  "versionName='"+NAME+"'" in badging and 'application-debuggable' not in badging,
                  'install-over identity/version/debug status failed')
        with ZipFile(parent) as old,ZipFile(signed) as z:
            for name in (previous.ENGINE,previous.RECORDER,'classes.dex','classes2.dex'):
                c.require(z.read(name)==old.read(name),'native/DEX change prohibited in final skin stage '+name)
            for addon,version in VERSIONS.items():
                filename=addon+'-'+version+'.zip'
                entries=sorted(n for n in z.namelist() if n.startswith('assets/addons/'+addon+'/') and not n.endswith('/'))
                if addon!=c.SKIN:
                    shutil.copyfile(directory/filename,temp/filename)
                else:
                    with ZipFile(temp/filename,'w',compression=ZIP_DEFLATED,compresslevel=9) as component:
                        for name in entries:component.writestr(name[14:],z.read(name))
                with ZipFile(temp/filename) as component:
                    c.require(component.testzip() is None and len(component.namelist())==len(set(component.namelist())) and
                              set(component.namelist())=={n[14:] for n in entries},'invalid matching component '+addon)
                    c.require(all(component.read(n)==z.read('assets/addons/'+n) for n in component.namelist()),
                              'component differs from final signed APK '+addon)
        receipt=dict(origin)
        receipt.update(version_code=CODE,version_name=NAME,source_commit=commit,
            parent_commit=ORIGIN,parent_apk_sha256=c.digest(parent),apk_sha256=c.digest(signed),
            protected_2103395_source_commit=c.COMMIT,protected_2103395_apk_sha256=c.PARENT,
            native_build_source_commit=ORIGIN,native_build_run=ORIGIN_RUN,
            native_compilation_reused=True,native_source_files_verified=9404,
            native_source_map_sha256=c.sha(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()),
            all_9404_compiler_inputs_verified_and_unchanged=True,native_binary_byte_identical_to_verified_2103396=True,
            original_engine_proof_not_rewritten=True,art_tested_source_commit=ORIGIN,
            tested_dex_byte_identical_to_verified_2103396=True,
            matching_component_versions=VERSIONS,apk_changed_members=changed,
            apk_changed_members_from_2103395=sorted(set(origin['apk_changed_members'])|set(changed)),
            final_skin_only_files=sorted(delta),physical_fold_verified=False,actual_install_over_tested=False,
            final_lock=False,option_b_normal_root_cause_proven=False,
            normal_option_b_status='NEEDS_EVIDENCE: eligibility unchanged, no seventh speculative repair')
        save(temp/'INFINITY-2103397-DELIVERY.json',receipt)
        save(temp/'CHANGED-FILE-MANIFEST.json',{'final_stage_changed':{
            n:{'before':c.sha(before[n]),'after':c.sha(body)} for n,body in delta.items()},
            'originating_96_changes':origin['apk_changed_members'],'final_apk_changes':changed,
            'native_and_dex_changed_in_final_stage':False,'originating_source_commit':ORIGIN,
            'final_source_commit':commit})
        (temp/'FINAL-SIGNATURE.txt').write_text(final_signature)
        (temp/'PARENT-SIGNATURE.txt').write_text(signature)
        (temp/'APK-BADGING.txt').write_text(badging)
        for leaf in ('ENGINE-PROOF.json','ART-COMPONENT-VERIFICATION.json','STARTUP-DEX-INTEGRATION.json'):
            shutil.copyfile(directory/leaf,temp/leaf)
        for leaf in ('INSTALLATION.txt','CORRECTIVE-ACCEPTANCE.md'):
            shutil.copyfile(Path(__file__).parent/leaf,temp/leaf)
        with ZipFile(directory/'Infinity-2103396-Source-and-Build-Receipts.zip') as old,ZipFile(
            temp/'Infinity-2103397-Source-and-Build-Receipts.zip','w',compression=ZIP_DEFLATED,compresslevel=9) as source_zip:
            for info in old.infolist():source_zip.writestr(copy.copy(info),old.read(info.filename))
            source_zip.writestr('FINAL-SOURCE-COMMIT.txt',commit+'\n')
            for name,body in delta.items():source_zip.writestr('final-components/'+name,body)
            for path in sorted(Path(__file__).parent.iterdir()):
                if path.is_file():source_zip.write(path,'final-corrective/'+path.name)
            for leaf in ('INFINITY-2103397-DELIVERY.json','CHANGED-FILE-MANIFEST.json'):
                source_zip.write(temp/leaf,'final-receipts/'+leaf)
        unsigned.unlink()
        save(temp/'COMPONENTS.json',{a:{'version':v,'file':a+'-'+v+'.zip',
            'sha256':c.digest(temp/(a+'-'+v+'.zip'))} for a,v in VERSIONS.items()})
        (temp/'SHA256SUMS').write_text(''.join(c.digest(p)+'  '+p.name+'\n'
            for p in sorted(temp.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
        os.rename(temp,out)
    print(json.dumps(receipt,indent=2,sort_keys=True))


if __name__=='__main__':
    c.require(len(sys.argv)==4,'origin-directory output-directory source-commit required')
    assemble(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
