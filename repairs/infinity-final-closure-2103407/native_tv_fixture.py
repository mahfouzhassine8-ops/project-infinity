"""Fresh disposable API37 library fixture; never replace a user's database."""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

ROOT=Path(__file__).parent
PROFILE='/sdcard/Android/data/com.projectinfinity.kodi/files/.kodi/userdata'
NATIVE_PROFILE='/storage/emulated/0/Android/data/com.projectinfinity.kodi/files/.kodi/userdata/'
FOLDER=NATIVE_PROFILE+'infinity-cw-qa/'
EPISODES=((1,1,2,'QA.S01E02.mp4','900000000002'),(2,2,1,'QA.S02E01.mp4','900000020001'))
ANCHOR="                xbmc.Player().stop();passed('actual-new-playback-and-short-rewind-update-original-progress-key')"
TAIL="\n                from native_tv_observer import run as observe_native_tv\n                observe_native_tv(ui,hub,profile,result)"


def database(path):
    path=Path(path)
    if path.exists() or path.is_symlink():raise ValueError('Existing database refused')
    raw=(ROOT/'TV-LIBRARY-131-EMPTY-SCHEMA.sql').read_bytes()
    plan=json.loads((ROOT/'TV-CONTINUE-WATCHING-PLAN.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=plan['schema_origin']['sql_sha256']:
        raise ValueError('Exact native131 empty schema required')
    with sqlite3.connect(path) as conn:
        conn.executescript(raw.decode())
        if conn.execute('select idVersion from version').fetchone()!=(131,):raise ValueError('Native131 required')
        for table in ('movie','tvshow','episode','path','files','uniqueid','bookmark'):
            if conn.execute('select count(*) from '+table).fetchone()!=(0,):raise ValueError('Only an empty native schema is permitted')
        conn.execute('insert into path(idPath,strPath,strContent,noUpdate,exclude) values(1,?,?,1,0)',(FOLDER,'tvshows'))
        conn.execute('insert into tvshow(idShow,c00,c01,c05,c12) values(1,?,?,?,?)',
                     ('Breaking Bad','Synthetic QA library catalogue','2008-01-20','1'))
        conn.execute('insert into tvshowlinkpath(idShow,idPath) values(1,1)')
        conn.execute('insert into uniqueid(uniqueid_id,media_id,media_type,value,type) values(1,1,?,?,?)',('tvshow','1396','tmdb'))
        for dbid,season,episode,file,tmdb in EPISODES:
            conn.execute('insert into seasons(idSeason,idShow,season) values(?,1,?)',(dbid,season))
            conn.execute('insert into files(idFile,idPath,strFilename,playCount) values(?,1,?,0)',(dbid,file))
            conn.execute('insert into uniqueid(uniqueid_id,media_id,media_type,value,type) values(?,?,?,?,?)',
                         (dbid+1,dbid,'episode',tmdb,'tmdb'))
            conn.execute('insert into episode(idEpisode,idFile,c00,c01,c05,c09,c12,c13,c18,c19,c20,idShow,idSeason) '
                         'values(?,?,?,?,?,?,?,?,?,?,?,1,?)',
                         (dbid,dbid,'QA S%02dE%02d'%(season,episode),'Full synthetic episode synopsis',
                          '2008-01-27','180',str(season),str(episode),FOLDER+file,1,dbid+1,dbid))
        if conn.execute('pragma integrity_check').fetchone()!=('ok',):raise ValueError('Fixture integrity failed')
    return path


def stage(device,args,report,expected,allow_participant=False):
    allowed=('final-continue','final-participant') if allow_participant else ('final-continue',)
    if args.case not in allowed or expected.get('verify_tv_completion') is not True:
        raise ValueError('Only explicitly selected native TV completion is permitted')
    if (device.PACKAGE!='com.projectinfinity.kodi' or device.PROFILE!=PROFILE or
            device.shell('getprop','ro.kernel.qemu').strip()!='1' or
            device.shell('getprop','ro.build.version.sdk').strip()!='37'):
        raise ValueError('Only fresh disposable API37 permitted')
    receipt=json.loads((args.out/'INSTALL-OVER-EVIDENCE.json').read_text())
    if (receipt.get('candidate_sha256')!=expected['candidate_apk_sha256'] or
            receipt.get('baseline_launched') is not False or receipt.get('test_sentinel_preserved') is not True or
            receipt.get('uninstall_or_data_clear') is not False or device.running_engine() or
            device.shell('pidof',device.PACKAGE,check=False).strip()):
        raise ValueError('No fixture writes after launch or on existing data')
    remote_db=PROFILE+'/Database/MyVideos131.db';remote_folder=PROFILE+'/infinity-cw-qa'
    for target in (remote_db,remote_folder):
        device.shell('test','!','-e',target);device.shell('test','!','-L',target)
    clip=args.out/'final-profile/infinity-final-qa.mp4'
    if not clip.is_file() or report.get('generated_clip_format',{}).get('fps')!=24:
        raise ValueError('Original actual24fps/180sec clip required')
    folder=args.out/'native-tv-fixture';folder.mkdir(exist_ok=False)
    db=database(folder/'MyVideos131.db');video=folder/'infinity-cw-qa';video.mkdir()
    for _,_,_,file,_ in EPISODES:shutil.copyfile(clip,video/file)
    device.shell('mkdir','-p',PROFILE+'/Database')
    device.adb('push',db,remote_db);device.adb('push',video,remote_folder)
    def checked(local,remote):
        want=hashlib.sha256(local.read_bytes()).hexdigest()
        raw=device.adb('exec-out','cat',remote,binary=True)
        if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=want:
            raise ValueError('Actual native TV fixture readback differs')
        return want
    hashes={remote_db:checked(db,remote_db)}
    for _,_,_,file,_ in EPISODES:hashes[FOLDER+file]=checked(video/file,FOLDER+file)
    report['native_TV_fixture']=dict(native_database_version=131,before_first_launch=True,
        replaced_existing_database=False,synthetic_metadata=True,generated_clip_seconds=180,
        actual_movie_content=False,episode_coordinates=[[1,2],[2,1]],readback_sha256=hashes,
        runtime_firstparty_imports=False,additional_writer_grant=False)


def instrument(text):
    if text.count(ANCHOR)!=1 or TAIL in text:raise ValueError('Original Continue completion boundary differs')
    return text.replace(ANCHOR,ANCHOR+TAIL,1)


def restore(text):return text.replace(TAIL,'',1)
