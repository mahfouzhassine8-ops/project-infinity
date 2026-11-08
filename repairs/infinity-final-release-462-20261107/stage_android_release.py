"""Fresh disposable fixture, exact signed artifacts and unmodified providers."""
from pathlib import Path
from zipfile import ZipFile
import argparse,hashlib,io,json,re,shutil,subprocess,sys
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT/'repairs/save-later-multiimage-20261023')]
import android_inputs
from prepare_release import PARENT,CERT,ENGINE,OLD_ENGINE,CC,SKIN
from inventory import file_sha,load,save,validate_names
from release_gate import require

def stage(parent,candidate,recovery,current,sdk,out,identity_only=False):
    require(not out.exists(),'FRESH_DISPOSABLE_FIXTURE');out.mkdir(parents=True)
    require(file_sha(parent)==PARENT,'EXACT_PARENT')
    scope=load(HERE/'ANDROID-SCOPE.json')
    require(scope['operation']=='verify-signed464465' and scope['application_tests'] is True,'EXACT_SELECTED_ANDROID_SCOPE')
    inputs=[]
    for version,path,native in [(2103464,candidate,ENGINE),(2103465,recovery,OLD_ENGINE)]:
        receipt=load(path.parent/'BUILD-RECEIPT.json')
        wanted=scope['signed_APKs'][str(version)]
        require(receipt['versionCode']==version and receipt['signed_apk_sha256']==file_sha(path)==wanted['sha256'] and receipt['source']==wanted['source'],'EXACT_SOURCE_BOUND_SIGNED_APK')
        sig=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(path)],text=True)
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',sig)==[CERT],'EXACT_ONE_ORIGINAL_CERTIFICATE')
        (out/(str(version)+'-SIGNATURE.txt')).write_text(sig)
        with ZipFile(parent) as a,ZipFile(path) as b:
            for n in a.namelist():
                if n.startswith('classes') and n.endswith('.dex'):require(a.read(n)==b.read(n),'DEX_PRESERVATION:'+n)
            require(hashlib.sha256(b.read('lib/arm64-v8a/libkodi.so')).hexdigest()==native,'EXPECTED_NATIVE_ENGINE')
        inputs.append(dict(versionCode=version,sha256=file_sha(path),source=receipt['source'],certificate_sha256=CERT))
    save(out/'SIGNED-INPUT-IDENTITY.json',dict(status='PASS_EXACT_SIGNED464_AND465_INPUTS',APKs=inputs,parent_sha256=PARENT,APK_modified=False,Android='NOT_RUN'))
    if identity_only:return
    home=out/'home';addons=home/'addons';addons.mkdir(parents=True)
    ids=(CC,'script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge')
    with ZipFile(parent) as z:
        for n in validate_names(z):
            if any(n.startswith('assets/addons/'+aid+'/') for aid in ids) and not n.endswith('/'):
                p=home/n.removeprefix('assets/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    for aid,leaf,want in [
        (CC,CC+'-0.3.5.61-2103460-corrective.zip','e95f5668cd98bb3c7b5d5c22c8b7445f208b222ded07ae88dc587abd32288d6f'),
        (SKIN,SKIN+'-1.0.5.268-2103460-corrective.zip','db0ec52d2c744df7fe7cb4b203d0ea6a8324035f683e68b3e8ae9189e9a61749'),
    ]:
        require(file_sha(current/leaf)==want,'AUTHENTICATED_CURRENT_EXTERNAL_COMPONENT')
        if (addons/aid).exists():shutil.rmtree(addons/aid)
        with ZipFile(current/leaf) as z:validate_names(z);z.extractall(addons)
    # The user's saved code inventory identifies external Compat0.8.2. The
    # APK deliberately retains the old0.7.2 base plus an exact code-only patch.
    # Reproduce the existing external component; never change APK assets or
    # remove its original checkpoint/writer admission guards.
    compat=load(HERE/'COMPAT82-INPUT.json')
    original=ROOT/compat['original_source_directory']
    content={p.name:p.read_bytes() for p in original.iterdir() if p.is_file()}
    require({n:hashlib.sha256(b).hexdigest() for n,b in content.items()}==compat['before'],'EXACT_ORIGINAL_EXTERNAL_COMPAT82_SOURCE')
    with ZipFile(parent) as apk:patch_bytes=apk.read(compat['original_signed462_embedded_patch'])
    require(hashlib.sha256(patch_bytes).hexdigest()==compat['original_signed_patch_sha256'],'EXACT_ORIGINAL_SIGNED_COMPAT82_PATCH')
    with ZipFile(io.BytesIO(patch_bytes)) as patch:
        manifest=json.loads(patch.read('manifest.json'))
        require(manifest['addon_id']==compat['addon'] and manifest['addon_version']==compat['version'] and manifest['addon_xml_sha256']==hashlib.sha256(content['addon.xml']).hexdigest(),'AUTHENTICATED_EXISTING_COMPAT82_PATCH_TARGET')
        for row in manifest['files']:
            name=row['path'];require(Path(name).name==name,'FIXED_COMPAT_SOURCE_LEAF')
            if row['before'] is not None:require(hashlib.sha256(content[name]).hexdigest()==row['before'],'ORIGINAL_COMPAT_PATCH_PRECONDITION')
            raw=patch.read('payload/'+name);require(hashlib.sha256(raw).hexdigest()==row['after'],'ORIGINAL_COMPAT_PATCH_PAYLOAD');content[name]=raw
    require({n:hashlib.sha256(b).hexdigest() for n,b in content.items()}==compat['after'],'ALL_SIX_EXACT_EXISTING_COMPAT82_FILES')
    for name,want in compat['observed_installed_code']['entry_point_hashes'].items():require(hashlib.sha256(content[name]).hexdigest()==want,'OBSERVED_PHONE_COMPAT82_ENTRY_POINT')
    destination=addons/compat['addon'];destination.mkdir()
    for name,raw in content.items():(destination/name).write_bytes(raw)
    # Exact retained native-provider distributions; no account, private
    # settings, response substitution, provider patch or source shim.
    pins=load(ROOT/'repairs/save-later-multiimage-20261023/ANDROID-INPUT-PINS.json')
    known={r['addon']:r for r in pins['archives']}
    for row in load(HERE/'ANDROID-EXTRA-INPUT-PINS.json')['archives']:known[row['addon']]=row
    with ZipFile(parent) as z:
        builtins={}
        for n in z.namelist():
            if n.startswith('assets/addons/') and n.endswith('/addon.xml'):
                a=ET.fromstring(z.read(n));builtins[a.get('id')]=a.get('version')
    pending=[known['plugin.video.watchnixtoons2'],known['plugin.video.umbrella']]
    rows=[];seen=set()
    while pending:
        row=pending.pop(0);aid=row['addon']
        if aid in seen:continue
        print('Fetch exact unmodified fixture:',aid,row['version'],row['url'],flush=True)
        raw=android_inputs.fetch(row['url']);require(hashlib.sha256(raw).hexdigest()==row['sha256'],'EXACT_ORIGINAL_PROVIDER_DISTRIBUTION:'+aid)
        manifest=android_inputs.manifest(raw,aid);require(manifest.get('version')==row['version'],'PROVIDER_VERSION')
        with ZipFile(io.BytesIO(raw)) as z:
            for n in validate_names(z):
                require(Path(n).parts[0]==aid and (z.getinfo(n).external_attr>>16)&0o170000!=0o120000,'SAFE_UNMODIFIED_PROVIDER_ARCHIVE')
            z.extractall(addons)
        rows.append(row);seen.add(aid)
        for dep in manifest.findall('requires/import'):
            name=dep.get('addon')
            if name in builtins:
                if name.startswith('kodi.binary.'):require(builtins[name]==dep.get('version'),'EXACT_PACKAGED_NATIVE_DEPENDENCY_API:'+name)
                continue
            if dep.get('optional')=='true' or name in seen:continue
            require(name in known,'SEPARATELY_PINNED_DEPENDENCY_REQUIRED:'+name);pending.append(known[name])
    qa=addons/'script.infinity.finalreleaseqa';qa.mkdir()
    (qa/'addon.xml').write_text('<addon id="script.infinity.finalreleaseqa" name="Disposable final release QA" version="1.0.0" provider-name="Infinity engineering"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="qa.py"/><extension point="xbmc.addon.metadata"><summary lang="en">Disposable fixed test observer only</summary><platform>all</platform></extension></addon>')
    shutil.copyfile(HERE/'android_qa.py',qa/'qa.py')
    shutil.copyfile(ROOT/'repairs/save-later-multiimage-20261023/android_runtime_checks.py',qa/'android_runtime_checks.py')
    # RunAddon prioritizes pluginsource over script. Keep the observer script
    # separate so ExecuteAddon starts it even while first-use notices exist.
    clip=addons/'plugin.video.infinity.finalreleaseqaclip';clip.mkdir()
    (clip/'addon.xml').write_text('<addon id="plugin.video.infinity.finalreleaseqaclip" name="Disposable generated clip" version="1.0.0" provider-name="Infinity engineering"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.pluginsource" library="qa.py"><provides>video</provides></extension><extension point="xbmc.addon.metadata"><summary lang="en">Generated gray clip for selected controls only</summary><platform>all</platform></extension></addon>')
    shutil.copyfile(HERE/'android_qa.py',clip/'qa.py')
    profile=home/'userdata';profile.mkdir()
    (profile/'guisettings.xml').write_text('<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting><setting id="general.addonupdates">2</setting></settings>')
    (profile/'release-data-sentinel.txt').write_bytes(b'preserve-disposable-preupdate-data-464465-v1')
    identity=dict(schema=1,kind='movie',scope='movie',ids={'tmdb':'603','imdb':'tt0133093'})
    entry=dict(key='a'*64,media='movie',title='QA generated gray clip',label='QA generated gray clip',showtitle='',season=-1,episode=-1,identity=identity,tmdb='603',source='special://profile/infinity-final-qa.mp4',stable_source='special://profile/infinity-final-qa.mp4',position=60,duration=180,updated=10,playback_occurrence='1'*32)
    state=dict(schema=2,items={entry['key']:entry},watched={},watchlist={},collection={},lists={},sources={},later={},navigation_recovery={'unrelated':{'retained_sentinel':True}})
    save(profile/'addon_data'/CC/'continue-watching.json',state)
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=320x180:r=10','-t','180','-an','-c:v','libx264','-pix_fmt','yuv420p',str(profile/'infinity-final-qa.mp4')],check=True)
    report=dict(status='PASS_EXACT_INPUTS_AND_DISPOSABLE_FIXTURE_PREPARATION',parent_sha256=PARENT,APKs=inputs,original_provider_archives=rows,external_compat82=compat,provider_sources_modified=False,test_QA_addon_packaged_in_APK=False,generated_content='Gray180second clip; synthetic tracking metadata references TMDb603 only for alias/watched validation; no actual movie playback claim',actual_installed_Fold_provider_versions='NOT_CLAIMED',physical_Fold='NOT_RUN',shutdown='NOT_SELECTED')
    save(out/'ANDROID-INPUTS.json',report);print(report['status'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('parent','candidate','recovery','current','sdk','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--identity-only',action='store_true')
    stage(**vars(p.parse_args()))
