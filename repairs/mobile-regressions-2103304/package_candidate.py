#!/usr/bin/env python3
"""Package matched, source-built Java/native repair layers over verified 2103302.

A successful build is a device-test candidate, not physical acceptance.
"""
from pathlib import Path
import argparse,copy,json,os,re,shutil,struct,zipfile
from packaging_checks import (sha,require,run,configured,resource_ids,dex_contract,
                             verify_manifest_pair,DEX,SIGNATURE)
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PACKAGE='com.projectinfinity.kodi'
BASE_APK_SHA256='ee9d82463f35594ed595e50dc8913499e79110b63fbf27ad456a0b87b396fa83'
BASE_COMMIT='0a8d8a13efff44cc8be0c99416a1d239b3066e8c'
BASE_ENGINE_SHA256='cb7cb5a51cd8c059629d7bcdabec9eff719de480cd75541f865f596198c59162'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
RELEASE='1.0.9-Responsive-Repair-RC1'
VERSION_CODE=2103304
ENGINE='lib/arm64-v8a/libkodi.so'
JNI_ADDITIONS={('Lcom/projectinfinity/kodi/Main;','_infinityHeartbeat','()[J'),
               ('Lcom/projectinfinity/kodi/InfinityAndroidKeyboard;','changed','(JLjava/lang/String;ZZ)V')}


def verify_source(source, receipt, proof):
    actual={str(p.relative_to(source)):sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    require(actual==proof['files'],'Android source differs from the successfully tested export')
    validated_commit = '70309e66ab33d3f12df93b7a46ddb153f1f02f97'
    require(proof['source_commit'] in (validated_commit, os.environ['GITHUB_SHA']), 'Android tests used an unapproved source commit')
    require(proof['weather_isolation_audit_passed'] is True,'Weather isolation gate missing')
    for name in ('InfinityChooserWeather','InfinityStartupPreparation'):
        path='tools/android/packaging/xbmc/src/'+name+'.java.in'
        base=json.loads((HERE/'baseline-source-sha256.json').read_text())
        require(actual[path]==base[path],'Protected working weather/preparation source changed')
    return len(actual)


def prepare(source: Path, base: Path, build: Path, out: Path):
    require(sha(base.read_bytes()) == BASE_APK_SHA256, 'Not the exact 2103302 signed APK')
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
        text=configured(packaging/'xbmc'/(name+'.in'), values)
        if name=='build.gradle':
            require(text.count('versionCode 2103302')==1,'Unexpected Gradle version preimage')
            require(text.count('versionName "1.0.9-Chooser-Weather-Snapshot-RC1"')==1,'Unexpected Gradle name preimage')
            text=text.replace('versionCode 2103302',f'versionCode {VERSION_CODE}')
            text=text.replace('versionName "1.0.9-Chooser-Weather-Snapshot-RC1"',f'versionName "{RELEASE}"')
        (app/name).write_text(text)
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


def elf_identity(path, output):
    data=path.read_bytes()
    require(data[:6]==b'\x7fELF\x02\x01','Expected ELF64 little-endian native engine')
    require(struct.unpack_from('<HH',data,16)==(3,183),'Expected ARM64 shared library')
    notes=run('readelf','-h','-n','-W',path,output=output)
    ids=re.findall(r'Build ID: ([0-9a-f]+)',notes)
    require(len(ids)<=1,'Native engine has multiple build IDs')
    # The Kodi/NDK21 link is reproducible but does not emit a GNU build-ID.
    # Preserve the exact unstripped SHA in the proof and require strip to
    # preserve the ELF metadata state when no linker build-ID is present.
    return ('build-id',ids[0]) if ids else ('content-sha256',sha(data))


def prepare_native(engine, out):
    proof=json.loads((engine/'ENGINE-PROOF.json').read_text())
    native_source_commit=os.environ.get('INFINITY_NATIVE_SOURCE_COMMIT',os.environ['GITHUB_SHA'])
    require(proof['source_commit']==native_source_commit,'Native source commit mismatch')
    require(proof['baseline_kodi_commit']=='a3a448d26b8d560a65655dab2cd122994dc4e146','Wrong Kodi parent')
    require(proof['skin_id']=='skin.infinity.diggz','Wrong skin ID')
    original=engine/'libkodi.so'
    require(sha(original.read_bytes())==proof['native_sha256'],'Native engine differs from full-build proof')
    identity=elf_identity(original,out/'unstripped-elf-identity.txt')
    require(all(token in original.read_bytes() for token in
                (b'/InfinityAndroidKeyboard',b'_infinityHeartbeat')),'Matched JNI registration not found')
    packaged=out/'libkodi.so'
    shutil.copy2(original,packaged)
    strip=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ.get('NDK_VER','21.4.7075529')/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip,'--strip-unneeded',packaged)
    packaged_identity=elf_identity(packaged,out/'packaged-elf-identity.txt')
    require(packaged_identity[0]==identity[0],'Stripping changed native ELF identity kind')
    if identity[0]=='build-id':
        require(packaged_identity==identity,'Stripping changed native build ID')
    shutil.copy2(engine/'ENGINE-PROOF.json',out/'ENGINE-PROOF.json')
    shutil.copy2(engine/'source-manifest.json',out/'native-source-manifest.json')
    return packaged, {'unstripped_native_sha256':proof['native_sha256'],
                      'packaged_native_sha256':sha(packaged.read_bytes()),
                      'native_build_id':identity[1] if identity[0]=='build-id' else None,
                      'native_identity_kind':identity[0]}


def merge(base, donor, native, output):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(donor) as b,zipfile.ZipFile(output,'w') as z:
        an,bn=set(a.namelist()),set(b.namelist())
        require(len(an)==len(a.namelist()) and len(bn)==len(b.namelist()),'Duplicate APK members')
        require(not a.testzip() and not b.testzip(),'APK CRC failure')
        require(sha(a.read(ENGINE))==BASE_ENGINE_SHA256,'Wrong parent native engine')
        require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in bn),
                'Unexpected native/asset payload in Android-only donor')
        old_native,old_classes=dex_contract(a)
        new_native,new_classes=dex_contract(b)
        require(new_native==old_native|JNI_ADDITIONS,'JNI delta exceeds the two declared native bridges')
        core={n for n in old_classes if n.startswith('Lcom/projectinfinity/kodi/') and '$' not in n}
        require(core<=new_classes,'Existing core Java class lost: '+repr(core-new_classes))
        for info in a.infolist():
            n=info.filename
            if n in ('AndroidManifest.xml',ENGINE) or DEX.fullmatch(n) or SIGNATURE.fullmatch(n):
                continue
            z.writestr(copy.copy(info),a.read(n))
        for info in b.infolist():
            if info.filename=='AndroidManifest.xml' or DEX.fullmatch(info.filename):
                z.writestr(copy.copy(info),b.read(info.filename))
        z.write(native,ENGINE,compress_type=zipfile.ZIP_STORED)
    return len(old_native),len(core)


def verify_bytes(base, final, native):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        an,bn=set(a.namelist()),set(b.namelist())
        kept={n for n in an if n not in ('AndroidManifest.xml',ENGINE)
              and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected=kept|{'AndroidManifest.xml',ENGINE}|{n for n in bn if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(bn==expected and len(bn)==len(b.namelist()),'Unexpected final APK members')
        for name in sorted(kept):
            require(a.read(name)==b.read(name),'Protected APK payload changed: '+name)
        require(b.read(ENGINE)==native.read_bytes(),'Wrong packaged native engine')
        require(dex_contract(b)[0]==dex_contract(a)[0]|JNI_ADDITIONS,'Final JNI contract mismatch')
        require(not b.testzip(),'Final APK CRC failure')
        return {'other_native_libraries_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') for n in kept),
                'asset_files_byte_identical':sum(n.startswith('assets/') and not n.endswith('/') for n in kept),
                'android_resources_byte_identical':True,'protected_entries':len(kept)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('source','base-apk','build-dir','out','source-proof','source-receipt','engine'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    source,base,build,out,engine=[p.resolve() for p in (a.source,a.base_apk,a.build_dir,a.out,a.engine)]
    out.mkdir(parents=True,exist_ok=True)
    proof=json.loads(a.source_proof.read_text());receipt=json.loads(a.source_receipt.read_text())
    source_count=verify_source(source,receipt,proof)
    native,native_report=prepare_native(engine,out)
    ids=prepare(source,base,build,out)
    env=dict(os.environ,KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',
             KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
    run('./gradlew','--no-daemon','--console=plain',':xbmc:assembleRelease',cwd=build,env=env)
    run('./gradlew','--no-daemon','--console=plain',':xbmc:dependencies','--configuration',
        'releaseRuntimeClasspath',cwd=build,env=env,output=out/'android-dependencies.txt')
    donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    require(ids==resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt'),'Compiled Android resource IDs drifted')
    unsigned=out/'Infinity-2103303-unsigned.apk'
    natives,core=merge(base,donor,native,unsigned)
    manifest=run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'manifest.txt')
    original_manifest=run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt')
    verify_manifest_pair(original_manifest,manifest)
    # Permanent signer is mandatory for the install-over candidate.
    for name in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)),'Missing permanent signing configuration: '+name)
    final=out/'Infinity-2103304-1.0.9-Responsive-Repair-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
    require(CERT in cert.lower(),'Signer differs from exact 2103302')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='{PACKAGE}' versionCode='{VERSION_CODE}' versionName='{RELEASE}'" in badging,'Wrong version identity')
    require("sdkVersion:'21'" in badging and "targetSdkVersion:'35'" in badging,'Android API contract changed')
    require("application-label:'Infinity'" in badging,'User-facing branding changed')
    require(len(re.findall(r'^launchable-activity:',badging,re.M))==1,'Launcher count changed')
    require('application-debuggable' not in badging,'Candidate is debuggable')
    preserved=verify_bytes(base,final,native)
    report={'schema':1,'source_commit':os.environ['GITHUB_SHA'],'base_source_commit':BASE_COMMIT,
            'base_run':37146313126,'base_apk_sha256':BASE_APK_SHA256,'base_native_sha256':BASE_ENGINE_SHA256,
            'apk':final.name,'apk_sha256':sha(final.read_bytes()),'version_code':VERSION_CODE,'version_name':RELEASE,
            'signer_certificate_sha256':CERT,'existing_jni_declarations_preserved':natives,
            'jni_additions':sorted(JNI_ADDITIONS),'core_java_classes_preserved':core,
            'resource_id_map_verified':len(ids),'verified_source_files':source_count,
            'source_built_android_layer':True,'native_recompiled':True,'smali_used':False,
            'skin_id':'skin.infinity.diggz','required_skin_version':'1.0.5.194',
            'required_controller_version':'unchanged','runtime_device_tested':False,
            'accepted':False,'historical_crash_owner_proven':False,**native_report,**preserved}
    (out/'APK-AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    shutil.copy2(a.source_proof,out/'ANDROID-SOURCE-PROOF.json')
    shutil.copy2(a.source_receipt,out/'android-repair-changes.json')
    unsigned.unlink();native.unlink()
    print('PASS: matched source-built Java/ARM64 candidate; protected assets/resources/native companions preserved; not device accepted')


if __name__=='__main__':main()
