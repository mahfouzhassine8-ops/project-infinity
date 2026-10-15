#!/usr/bin/env python3
"""Compile the source-built Android shell and reuse the exact accepted native APK.

No apktool/smali mutations, no native rebuild. Existing Android resources are
preserved only after an exact name/ID-map check against the compiled Java shell.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile

from infinity_background_resume import BASE_APK_SHA256, BASE_ENGINE_SHA256, BASE_COMMIT, RELEASE, VERSION_CODE

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'com.projectinfinity.kodi'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
DEX = re.compile(r'classes\d*\.dex$')
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$', re.I)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(*args, cwd=None, env=None, output=None):
    if output is not None:
        result = subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                                check=True, stdout=subprocess.PIPE, text=True)
        Path(output).write_text(result.stdout)
        return result.stdout
    subprocess.run([str(x) for x in args], cwd=cwd, env=env, check=True)


def configured(path: Path, values: dict[str, str]) -> str:
    text = path.read_text()
    for key, value in values.items():
        text = text.replace('@' + key + '@', value)
    require(not re.search(r'@[A-Z][A-Z_0-9]*@', text), 'Unresolved CMake placeholder: ' + str(path))
    return text


def resource_ids(aapt2: Path, apk: Path, output: Path) -> dict[str, str]:
    text = run(aapt2, 'dump', 'resources', apk, output=output)
    ids = {}
    for rid, name in re.findall(r'^\s*resource\s+(0x7f[0-9a-fA-F]{6})\s+([^\s]+/[^\s]+)', text, re.M):
        name = name.split(':', 1)[-1]
        require(name not in ids or ids[name] == rid, 'Ambiguous resource: ' + name)
        ids[name] = rid.lower()
    require(len(ids) > 20, 'Resource map empty or unrecognized; refusing a mixed resource/DEX APK')
    return ids


def dex_contract(archive: zipfile.ZipFile):
    """Read native declarations directly from DEX class_data, including descriptors."""
    native, classes = set(), set()
    for name in archive.namelist():
        if not DEX.fullmatch(name):
            continue
        data = archive.read(name)
        require(data[:4] == b'dex\n', 'Not a standard DEX file: ' + name)
        def u32(off):
            return struct.unpack_from('<I', data, off)[0]
        def leb(off):
            val, shift = 0, 0
            while True:
                b = data[off]; off += 1
                val |= (b & 127) << shift
                if b < 128: return val, off
                shift += 7
                require(shift <= 28, 'Invalid DEX LEB128')
        count, off = u32(56), u32(60)
        strings = []
        for i in range(count):
            _, s = leb(u32(off + 4*i))
            strings.append(data[s:data.index(b'\0', s)].decode('utf-8', errors='replace'))
        count, off = u32(64), u32(68)
        types = [strings[u32(off + 4*i)] for i in range(count)]
        count, off = u32(72), u32(76)
        protos = []
        for i in range(count):
            ret, poff = u32(off+12*i+4), u32(off+12*i+8)
            params = [] if not poff else [types[struct.unpack_from('<H',data,poff+4+2*j)[0]] for j in range(u32(poff))]
            protos.append('(' + ''.join(params) + ')' + types[ret])
        count, off = u32(88), u32(92)
        methods = []
        for i in range(count):
            owner, proto, text = struct.unpack_from('<HHI', data, off+8*i)
            methods.append((types[owner], strings[text], protos[proto]))
        count, off = u32(96), u32(100)
        for i in range(count):
            owner = types[u32(off+32*i)]
            classes.add(owner)
            pos = u32(off+32*i+24)
            if not pos: continue
            sf,pos=leb(pos); inf,pos=leb(pos); direct,pos=leb(pos); virtual,pos=leb(pos)
            for _ in range(sf+inf):
                _,pos=leb(pos); _,pos=leb(pos)
            for size in (direct,virtual):
                index=0
                for _ in range(size):
                    delta,pos=leb(pos); flags,pos=leb(pos); _,pos=leb(pos)
                    index += delta
                    if flags & 0x100:
                        native.add(methods[index])
    require(native, 'No JNI native declarations found')
    return native, classes


def source_preservation(source: Path):
    receipt = json.loads((ROOT/'engine/background-resume-source.json').read_text())
    for name, row in receipt['files'].items():
        require(sha((source/name).read_bytes()) == row['after'], 'Source changed after audit: ' + name)
    require(receipt['base_source_commit'] == BASE_COMMIT, 'Wrong Android source lineage')


def prepare(source: Path, base: Path, build: Path, out: Path):
    require(sha(base.read_bytes()) == BASE_APK_SHA256, 'Not the exact successful run-40 signed APK')
    source_preservation(source)
    sdk = Path(os.environ['ANDROID_HOME'])
    bt = sdk/'build-tools/34.0.0'
    original_ids = resource_ids(bt/'aapt2', base, out/'base-resources.txt')
    packaging = source/'tools/android/packaging'
    build.mkdir(parents=True, exist_ok=False)
    for name in ('build.gradle','settings.gradle','gradle.properties','gradlew'):
        shutil.copy2(packaging/name, build/name)
    shutil.copytree(packaging/'gradle', build/'gradle')
    (build/'gradlew').chmod(0o755)
    app=build/'xbmc'; app.mkdir()
    values = {'APP_PACKAGE': PACKAGE, 'APP_NAME': 'Kodi', 'APP_NAME_LC': 'kodi',
              'APP_VERSION': RELEASE, 'APP_VERSION_CODE_ANDROID': str(VERSION_CODE),
              'TARGET_MINSDK':'21','TARGET_SDK':'35',
              'NDKROOT':str(sdk/'ndk'/os.environ.get('NDK_VER','21.4.7075529'))}
    for name in ('AndroidManifest.xml','build.gradle'):
        (app/name).write_text(configured(packaging/'xbmc'/(name+'.in'), values))
    # Keep original resource IDs stable; additionally verify them after real AAPT2 linking.
    (build/'stable-ids.txt').write_text(''.join(f'{PACKAGE}:{name} = {rid}\n' for name,rid in sorted(original_ids.items())))
    with (app/'build.gradle').open('a') as f:
        f.write('\nandroid.aaptOptions.additionalParameters "--stable-ids", rootProject.file("stable-ids.txt").absolutePath\n')
    registered = set(re.findall(r'\bsrc/([\w/]+\.java)\b', (source/'cmake/scripts/android/Install.cmake').read_text()))
    actual = {str(p.relative_to(packaging/'xbmc/src'))[:-3] for p in (packaging/'xbmc/src').rglob('*.java.in')}
    require(registered == actual, 'CMake/Java source registration mismatch: ' + repr(registered ^ actual))
    for name in sorted(registered):
        p=app/'java'/PACKAGE.replace('.','/')/name; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(configured(packaging/'xbmc/src'/(name+'.in'), values))
    shutil.copytree(packaging/'xbmc/res', app/'res')
    for name, dest in (('strings.xml','values'),('colors.xml','values'),('searchable.xml','xml')):
        p=app/'res'/dest/name; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(configured(packaging/'xbmc'/(name+'.in'), values))
    copies = {'drawable/applaunch_screen.png': source/'media/applaunch_screen.png',
              'drawable-xxxhdpi/applaunch_screen.png': source/'media/applaunch_screen.png',
              'drawable/ic_recommendation_80dp.png':source/'media/icon80x80.png',
              'drawable-xhdpi/banner.png':packaging/'media/drawable-xhdpi/banner.png'}
    for density in ('ldpi','mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi'):
        name='drawable-'+density+'/ic_launcher.png'; copies[name]=packaging/'media'/name
    for name, origin in copies.items():
        p=app/'res'/name; p.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(origin,p)
    (build/'local.properties').write_text('sdk.dir='+str(sdk)+'\n')
    print(f'PASS: {len(registered)} registered Java sources staged, {len(original_ids)} resource IDs pinned; no native/skin source copied')
    return original_ids


def manifest_tree(text: str):
    root, stack = None, []
    for line in text.splitlines():
        stripped=line.lstrip(); indent=len(line)-len(stripped)
        if stripped.startswith('E: '):
            node={'tag':stripped.split()[1], 'attrs':{}, 'children':[]}
            while stack and stack[-1][0]>=indent: stack.pop()
            if stack: stack[-1][1]['children'].append(node)
            else:
                require(root is None,'Multiple manifest roots'); root=node
            stack.append((indent,node))
        elif stripped.startswith('A: '):
            key,value=stripped[3:].split('=',1)
            require(bool(stack),'Manifest attribute outside element')
            stack[-1][1]['attrs'][key.split('(')[0]]=value
    require(root is not None,'Empty compiled manifest'); return root


def verify_manifest_pair(original: str, compiled: str):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'): tree['attrs'].pop(key,None)
    permissions=[n for n in new['children'] if n['tag']=='uses-permission' and
                 'android.permission.FOREGROUND_SERVICE_SPECIAL_USE' in n['attrs'].get('android:name','')]
    require(len(permissions)==1,'Exactly one background service permission required')
    new['children'].remove(permissions[0])
    app=next(n for n in new['children'] if n['tag']=='application')
    services=[n for n in app['children'] if n['tag']=='service' and
              'InfinityExtendedBackgroundService' in n['attrs'].get('android:name','')]
    require(len(services)==1,'Exactly one background service component required')
    svc=services[0]
    require(svc['attrs'].get('android:exported','').endswith('0x0'),'Background service must not be exported')
    require(svc['attrs'].get('android:foregroundServiceType','').endswith('0x40000000'),'Wrong compiled foreground service type')
    app['children'].remove(svc)
    require(old==new,'Compiled manifest drift outside version and new background service; inspect both manifest reports')


def merge(base: Path, donor: Path, output: Path):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(donor) as b, zipfile.ZipFile(output,'w') as z:
        an, bn = set(a.namelist()), set(b.namelist())
        require(len(an)==len(a.namelist()) and len(bn)==len(b.namelist()), 'Duplicate APK members')
        require(not a.testzip() and not b.testzip(), 'APK CRC failure')
        require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in bn), 'Unexpected native/asset payload in Android-only compilation')
        original_native,original_classes=dex_contract(a)
        compiled_native,compiled_classes=dex_contract(b)
        require(original_native==compiled_native, 'JNI native descriptor inventory changed')
        core={n for n in original_classes if n.startswith('Lcom/projectinfinity/kodi/') and '$' not in n}
        require(core <= compiled_classes, 'Native-facing Java class lost: '+repr(core-compiled_classes))
        for info in a.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n) or SIGNATURE.fullmatch(n): continue
            z.writestr(info,a.read(n))
        for info in b.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n):
                z.writestr(info,b.read(n))
    return len(original_native),len(core)


def verify_bytes(base: Path, final: Path):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(final) as b:
        an,bn=set(a.namelist()),set(b.namelist())
        kept={n for n in an if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected=kept|{'AndroidManifest.xml'}|{n for n in bn if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(bn==expected,'Unexpected final APK member inventory')
        for name in sorted(kept): require(a.read(name)==b.read(name),'Protected APK payload changed: '+name)
        require(sha(b.read('lib/arm64-v8a/libkodi.so'))==BASE_ENGINE_SHA256,'Native engine changed')
        require(not b.testzip(),'Final APK CRC failure')
        native,_=dex_contract(b)
        require(native==dex_contract(a)[0],'Final JNI contract changed')
        joined=b''.join(b.read(n) for n in bn if DEX.fullmatch(n))
        for token in (b'InfinityExtendedBackgroundService',b'EXTENDED BACKGROUND MODE',b'InfinityCoreBridge',b'InfinityCobraDeviceBridge',b'getPlayWhenReady',b'Turn off'):
            require(token in joined,'Missing source-built runtime: '+repr(token))
        return {'native_files_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') for n in kept),
                'asset_files_byte_identical':sum(n.startswith('assets/') and not n.endswith('/') for n in kept),
                'android_resources_byte_identical':True,'other_payload_entries_preserved':len(kept)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--base-apk',type=Path,required=True)
    p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    source,base,build,out=[x.resolve() for x in (args.source,args.base_apk,args.build_dir,args.out)]
    out.mkdir(parents=True,exist_ok=True)
    ids=prepare(source,base,build,out)
    env=dict(os.environ, KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',
             KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
    run('./gradlew','--no-daemon','--console=plain',':xbmc:assembleRelease',cwd=build,env=env)
    run('./gradlew','--no-daemon','--console=plain',':xbmc:dependencies','--configuration','releaseRuntimeClasspath',cwd=build,env=env,output=out/'android-dependencies.txt')
    donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    donor_ids=resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt')
    require(ids==donor_ids,'Compiled R identifiers do not match the protected run-40 resource table')
    unsigned=out/'Infinity-1.0.9-Cobra-Background-Resume-RC1-unsigned.apk'
    natives,core=merge(base,donor,unsigned)
    manifest=run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'manifest.txt')
    run('python3',ROOT/'scripts/validate_candidate2_compiled_manifest.py',out/'manifest.txt')
    original_manifest=run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt')
    verify_manifest_pair(original_manifest,manifest)
    for token in ('InfinityExtendedBackgroundService','FOREGROUND_SERVICE_SPECIAL_USE','PROPERTY_SPECIAL_USE_FGS_SUBTYPE','action.OPEN_LIVE'):
        require(token in manifest,'Compiled manifest missing '+token)
    require('InfinityLiveLauncher' not in manifest, 'Second launcher appeared')
    # Permanent signer is mandatory. No fallback to an ephemeral key is permitted.
    for name in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)), 'Missing permanent signing configuration: '+name)
    final=out/'Infinity-1.0.9-Cobra-Background-Resume-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
    require(CERT in cert.lower(),'Signer differs from the accepted APK')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='{PACKAGE}' versionCode='{VERSION_CODE}' versionName='{RELEASE}'" in badging,'Wrong candidate identity')
    require("sdkVersion:'21'" in badging and "targetSdkVersion:'35'" in badging,'Android API contract drift')
    require("application-label:'Infinity'" in badging,'Branding changed')
    require(len(re.findall(r'^launchable-activity:',badging,re.M))==1,'Launcher count changed')
    require('application-debuggable' not in badging,'Candidate is debuggable')
    preserved=verify_bytes(base,final)
    report={'schema':1,'source_commit':os.environ.get('GITHUB_SHA'), 'base_source_commit':BASE_COMMIT,
            'base_run':35044752997,'base_apk_sha256':BASE_APK_SHA256,'native_engine_sha256':BASE_ENGINE_SHA256,
            'apk':final.name,'apk_sha256':sha(final.read_bytes()),'version_code':VERSION_CODE,'version_name':RELEASE,
            'signer_certificate_sha256':CERT,'compiled_jni_declarations_preserved':natives,
            'native_facing_java_classes_preserved':core,'resource_id_map_verified':len(ids),
            'source_built_android_layer':True,'native_recompiled':False,'smali_used':False,
            'runtime_device_tested':False,**preserved}
    (out/'background-resume-apk-audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    shutil.copy2(ROOT/'engine/background-resume-source.json',out/'background-resume-source.json')
    shutil.copy2(ROOT/'docs/background-resume-rc1.md',out/'DEVICE-TEST.md')
    unsigned.unlink()
    print('PASS: source-built Android background/resume APK; exact run-40 native engine/assets/resources; permanent signer verified')

if __name__=='__main__':main()
