"""Extend the retained passing Android harness without editing shared files."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=ROOT/'repairs/universal-persistence-2103401'
FUTURE='service.future.persistence.7fa29'
NAVFUTURE='plugin.video.future.navigation.7fa29'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def once(text,old,new):
    if text.count(old)!=1:raise RuntimeError('Retained Android fixture preimage differs')
    return text.replace(old,new)

def extra(stage,args,report):
    inputs=ROOT/'android-provider-inputs'
    pins=json.loads((HERE/'ANDROID-INPUT-PINS.json').read_text())
    for row in pins['archives']:
        shutil.copytree(inputs/row['addon'],stage/row['addon'])
    # A compatible future fork is explicitly a disposable test fixture. All
    # reviewed API bodies are unchanged apart from its own add-on identity.
    shutil.copytree(stage/'plugin.video.pov',stage/NAVFUTURE)
    for p in (stage/NAVFUTURE).rglob('*'):
        if p.is_file() and p.suffix in ('.py','.xml'):
            p.write_bytes(p.read_bytes().replace(b'plugin.video.pov',NAVFUTURE.encode()))
    fixture=stage/FUTURE
    shutil.copyfile(HERE/'android_runtime_checks.py',fixture/'android_runtime_checks.py')
    service=(OLD/'android_future_service.py').read_text()
    require_hash='7abb08a3f5a587f25449531c9cb6e687dd65d9b32793d1b8c596cccbb6274ad8'
    if sha(service.encode())!=require_hash:raise RuntimeError('Retained service changed')
    service=once(service,"versioncheck=xbmcaddon.Addon('service.xbmc.versioncheck')",
        "import android_runtime_checks\nandroid_runtime_checks.run(root,cycle,mode)\nversioncheck=xbmcaddon.Addon('service.xbmc.versioncheck')")
    (fixture/'service.py').write_text(service)
    xml=fixture/'resources/skins/Default/1080i/multiimage-probe.xml';xml.parent.mkdir(parents=True)
    imagepath=('resource://resource.images.weathericons.default/' if args.mode=='native-opaque' else
        'special://profile/addon_data/'+FUTURE+'/images/')
    xml.write_text('<window type="dialog"><defaultcontrol always="true">941</defaultcontrol><controls>'
        '<control type="multiimage" id="941"><left>0</left><top>0</top><width>64</width><height>64</height>'
        '<imagepath>'+imagepath+'</imagepath><timeperimage>1000</timeperimage><fadetime>0</fadetime>'
        '<randomize>false</randomize></control></controls></window>')
    report['test_provider_inputs']=pins
    report['future_provider_fixture_only']=NAVFUTURE
    # The original service's pending test remains independent of navigation.
    # Extra fixture-mode settings are explicitly staged, never production data.
    settings=fixture/'resources/settings.xml'
    settings.write_text(settings.read_text().replace('default="safe"','default="'+args.mode+'"'))
    profile=args.out/'profile-fixture';profile.mkdir()
    addondata=profile/'addon_data';(addondata/FUTURE/'images').mkdir(parents=True)
    # Read real PNG bytes from the signed APK; no image generation or decoder patch.
    with ZipFile(args.apk) as z:
        image=next(n for n in z.namelist() if n.endswith('.png') and z.getinfo(n).file_size>100)
        (addondata/FUTURE/'images/probe.png').write_bytes(z.read(image))
    def entry(key,title,tmdb,imdb,kind='tvshow'):
        route=('mode=play_media&mediatype=movie&tmdb_id='+tmdb if kind=='movie' else
               'mode=build_episode_list&season=all&tmdb_id='+tmdb)
        return dict(key=key*64,title=title,showtitle=title,media='movie' if kind=='movie' else 'tv',
            season=-1,episode=-1,tmdb=tmdb,imdb=imdb,source='plugin://plugin.video.pov/?'+route,
            identity=dict(schema=1,kind=kind,scope='movie' if kind=='movie' else 'show',ids=dict(tmdb=tmdb,imdb=imdb)))
    rows=[entry('a','Breaking Bad','1396','tt0903747'),entry('b','The Matrix','603','tt0133093','movie'),
          entry('c','Love After Lockup: Relationship Rehab','330430','tt48447471'),
          entry('d','Breaking Bad','1396','tt0903747')]
    later={e['key']:e for e in rows}
    resume=dict(rows[0],position=147.356,duration=2557.536,season=1,episode=3)
    resume.update(key='f'*64,source='plugin://plugin.video.pov/?mode=play_media&mediatype=episode&tmdb_id=1396&season=1&episode=3')
    resume['identity']=dict(schema=1,kind='episode',scope='show_episode',ids=rows[0]['identity']['ids'],season=1,episode=3)
    data=dict(schema=1,revision=1,later=later,watchlist=later,watched={'e'*64:dict(rows[1],watched=True)},
              items={'f'*64:resume},sources={},collection={},ratings={},lists={})
    target=addondata/'script.infinity.commandcenter/continue-watching.json';target.parent.mkdir()
    target.write_text(json.dumps(data,sort_keys=True)+'\n')
    report['preserved_fixture_sha256']=sha(target.read_bytes())
    probe=globals()['runtime']['probe']
    probe.adb('push',addondata,probe.PROFILE+'/addon_data')

def verify_runtime(args,entry,owner,probe):
    path=probe.PROFILE+'/addon_data/'+FUTURE+'/navigation-ready-'+str(owner['pid'])+'.json'
    result=probe.read_json(path)
    entry['navigation_and_multiimage']=result
    if not result.get('passed'):raise RuntimeError('Actual navigation checks failed: '+str(result.get('failure')))
    log=probe.shell('cat',probe.PROFILE+'/../temp/kodi.log',check=False)
    lines=[line for line in log.splitlines() if 'INFINITY_MULTIIMAGE_' in line and 'control=941;' in line]
    entry['actual_multiimage_evidence']=lines
    if not any('INFINITY_MULTIIMAGE_BEGIN' in line for line in lines):raise RuntimeError('Actual multi-image control did not create the tested job')
    retired=[line for line in lines if 'INFINITY_MULTIIMAGE_RETIRED' in line]
    if not retired:raise RuntimeError('No native multi-image completion evidence')
    expected='unchanged_receipt=false' if args.mode=='native-opaque' else 'unchanged_receipt=true'
    if not any(expected in line for line in retired):raise RuntimeError('Unexpected native persistence boundary: '+repr(retired))
    if args.mode=='safe' and not result.get('poisoned_cache_failure_and_explicit_alternative'):
        raise RuntimeError('Provider failure recovery was not executed')

def wait_navigation_ready(probe,owner,ready_path):
    import time
    deadline=time.monotonic()+1200
    while time.monotonic()<deadline:
        navigation=probe.read_json(probe.PROFILE+'/addon_data/'+FUTURE+'/navigation-ready-'+str(owner['pid'])+'.json')
        if navigation and not navigation.get('passed'):
            raise RuntimeError('Actual navigation check failed: '+str(navigation.get('failure')))
        ready=probe.read_json(ready_path)
        if ready:return ready
        time.sleep(.25)
    raise RuntimeError('Actual service did not reach its verified ready boundary')

def main():
    # Keep original platform, SELinux, APK digest, all real VFS/SQLite tests,
    # mandatory-owner checks, actual process-death and data readback assertions.
    original=(OLD/'android_probe.py').read_text()
    if sha(original.encode())!='fc6be3851836c3c159d5ee1627bc8d5c5796b9d58e9488449c5338e0c6b82c34':
        raise RuntimeError('Retained Android harness changed')
    modes=('safe','pending','opaque','native-opaque','lost-file','provider-pov','provider-umbrella','provider-seren','provider-future')
    compatible=tuple(m for m in modes if m!='opaque')
    success=tuple(m for m in modes if m=='safe' or m.startswith('provider-'))
    text=once(original,"['safe','pending','baseline','opaque','lost-file']",repr(list(modes)))
    # Run39935367720 loaded Estuary in all eight booted jobs: the retained
    # persistence-only fixture neither selected Infinity nor supplied the
    # <resolutions> required by CDisplaySettings::Load. CSettings::Load then
    # reset the invalid fixture to defaults. Seed a valid fresh-test profile;
    # do not change the APK, a shared harness, or an existing user profile.
    text=once(text,
        '<settings version="2"><setting id="general.addonupdates">2</setting></settings>',
        '<settings version="2"><resolutions />'
        '<setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
        '<setting id="general.addonupdates">2</setting></settings>')
    text=once(text,"\n        if a.mode in ('safe','pending','lost-file'):","\n        if a.mode in "+repr(compatible)+":")
    # Second occurrence validates the existing archived compatible version.
    text=once(text,"            if a.mode in ('safe','pending','lost-file'):","            if a.mode in "+repr(compatible)+":")
    text=once(text,"            if a.mode!='safe':", "            if a.mode not in "+repr(success)+":")
    oldblock="""            name='script.infinity.commandcenter';prefix='assets/addons/'+name+'/'
            for member in z.namelist():
                if member.startswith(prefix) and not member.endswith('/'):
                    target=stage/name/member[len(prefix):];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(member))"""
    newblock="""            for name in ('script.infinity.commandcenter','script.infinity.watchedbridge','script.infinity.uirepair'):
                prefix='assets/addons/'+name+'/'
                for member in z.namelist():
                    if member.startswith(prefix) and not member.endswith('/'):
                        target=stage/name/member[len(prefix):];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(member))"""
    text=once(text,oldblock,newblock)
    text=once(text,"        report['fixture_manifest']=", "        extra(stage,a,report)\n        report['fixture_manifest']=")
    text=once(text,"'script.infinity.commandcenter':'0.3.5.29','service.infinity.compat':'0.8.2'",
        "'script.infinity.commandcenter':'0.3.5.31','script.infinity.watchedbridge':'1.0.12','script.infinity.uirepair':'0.1.14','service.infinity.compat':'0.8.2'")
    text=once(text,"ready=until(lambda:probe.read_json(ready_path),60)","ready=wait_navigation_ready(probe,owner,ready_path)")
    text=once(text,"            entry['service_ready']=ready", "            entry['service_ready']=ready\n            verify_runtime(a,entry,owner,probe)")
    text=once(text,"                elif a.mode=='lost-file':", "                elif a.mode=='native-opaque':\n                    assert 'multiimage_directory_backend_unverified' in evidence and 'background_jobs' in evidence\n                elif a.mode=='lost-file':")
    text=once(text,"ready-'+str(owner['pid'])+'.json'),60)","ready-'+str(owner['pid'])+'.json'),1200)")
    # Persist the precise harness-only patch for review; no original file edited.
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--out',type=Path,required=True)
    args,_=parser.parse_known_args();args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'RETAINED-HARNESS.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),'retained/android_probe.py','disposable/extended_android_probe.py')))
    global runtime
    runtime=dict(__file__=str(OLD/'android_probe.py'),__name__='retained_targeted_android',extra=extra,verify_runtime=verify_runtime,wait_navigation_ready=wait_navigation_ready)
    exec(compile(text,str(OLD/'android_probe.py'),'exec'),runtime)
    runtime['main']()

if __name__=='__main__':main()
