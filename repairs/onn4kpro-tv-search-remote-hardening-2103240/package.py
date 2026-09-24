#!/usr/bin/env python3
"""Fast-pack the audited 2103240 RC20 inline-search/remote-hardening layer over exact signed passed 2103239 RC19 ARMv7 APK.

No Kodi native rebuild, no apktool and no smali. Java/manifest/resources are
compiled from source, resource IDs are pinned to the passed 2103237 RC17 APK, and
only compiled DEX + manifest replace their counterparts. All native libraries,
assets and compiled Android resources remain byte-identical to 2103237.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,struct,subprocess,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACKAGE='com.projectinfinity.kodi'
VERSION=2103240
RELEASE='1.0.9-Cobra-Onn4KPro-TV-Search-Remote-Hardening-RC20'
BASE_APK_SHA256='243a82db8c2dbc773b17a6feacf1f22379d9fbcd0525ec7073ab6237a085489d'
BASE_ENGINE_SHA256='670eb63be5c42a82224229215a7cb38b9e0d9ab393e394247f199d2bacc8c105'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
LIB='lib/armeabi-v7a/libkodi.so'
DEX=re.compile(r'classes\d*\.dex$')
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',re.I)

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def require(v,m):
    if not v:raise RuntimeError(m)
def run(*args,cwd=None,env=None,output=None):
    result=subprocess.run([str(x) for x in args],cwd=cwd,env=env,check=True,
                          stdout=subprocess.PIPE if output is not None else None,text=True)
    if output is not None:
        Path(output).write_text(result.stdout);return result.stdout
def configured(path:Path,values:dict[str,str])->str:
    text=path.read_text()
    for key,value in values.items():text=text.replace('@'+key+'@',value)
    require(not re.search(r'@[A-Z][A-Z_0-9]*@',text),'Unresolved CMake placeholder: '+str(path))
    return text
def resource_ids(aapt2:Path,apk:Path,output:Path)->dict[str,str]:
    text=run(aapt2,'dump','resources',apk,output=output);ids={}
    for rid,name in re.findall(r'^\s*resource\s+(0x7f[0-9a-fA-F]{6})\s+([^\s]+/[^\s]+)',text,re.M):
        name=name.split(':',1)[-1];require(name not in ids or ids[name]==rid,'Ambiguous resource '+name);ids[name]=rid.lower()
    require(len(ids)>20,'Resource map empty');return ids

def dex_contract(archive:zipfile.ZipFile):
    native,classes=set(),set()
    for name in archive.namelist():
        if not DEX.fullmatch(name):continue
        data=archive.read(name);require(data[:4]==b'dex\n','Not standard DEX '+name)
        def u32(o):return struct.unpack_from('<I',data,o)[0]
        def leb(o):
            val=shift=0
            while True:
                b=data[o];o+=1;val|=(b&127)<<shift
                if b<128:return val,o
                shift+=7;require(shift<=28,'Invalid LEB128')
        count,off=u32(56),u32(60);strings=[]
        for i in range(count):
            _,p=leb(u32(off+4*i));strings.append(data[p:data.index(b'\0',p)].decode('utf-8',errors='replace'))
        count,off=u32(64),u32(68);types=[strings[u32(off+4*i)] for i in range(count)]
        count,off=u32(72),u32(76);protos=[]
        for i in range(count):
            ret,poff=u32(off+12*i+4),u32(off+12*i+8);params=[] if not poff else [types[struct.unpack_from('<H',data,poff+4+2*j)[0]] for j in range(u32(poff))]
            protos.append('('+''.join(params)+')'+types[ret])
        count,off=u32(88),u32(92);methods=[]
        for i in range(count):
            owner,proto,text=struct.unpack_from('<HHI',data,off+8*i);methods.append((types[owner],strings[text],protos[proto]))
        count,off=u32(96),u32(100)
        for i in range(count):
            owner=types[u32(off+32*i)];classes.add(owner);pos=u32(off+32*i+24)
            if not pos:continue
            sf,pos=leb(pos);inf,pos=leb(pos);direct,pos=leb(pos);virtual,pos=leb(pos)
            for _ in range(sf+inf):_,pos=leb(pos);_,pos=leb(pos)
            for size in (direct,virtual):
                index=0
                for _ in range(size):
                    delta,pos=leb(pos);flags,pos=leb(pos);_,pos=leb(pos);index+=delta
                    if flags&0x100:native.add(methods[index])
    require(native,'No JNI declarations found');return native,classes

def source_preservation(source:Path):
    receipt=json.loads((ROOT/'engine/background-resume-source.json').read_text())
    require(receipt.get('version_code')==VERSION and receipt.get('version_name')==RELEASE,'Wrong audited 2103240 source receipt')
    require(receipt.get('tv_target_abi')=='armeabi-v7a' and receipt.get('mobile_parent_untouched') is True,'TV source scope receipt mismatch')
    require(receipt.get('tv_hardening') is True and receipt.get('tv_native_remote_architecture') is True,'2103224 native remote parent missing')
    require(receipt.get('tv_handoff_first_render') is True and receipt.get('tv_multiview_row_focus_visible') is True,'2103225 handoff/focus receipt missing')
    require(receipt.get('tv_player_footer_unclipped') is True and receipt.get('multiview_two_to_one_session_preserved') is True,'2103225 physical-TV gates missing')
    require(receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player' and receipt.get('tv_back_reverses_hierarchy') is True,'2103230 navigation hierarchy missing')
    require(receipt.get('tv_mini_player_preserved') is True and receipt.get('tv_preview_engine_preserved') is True,'2103230 mini-player preservation missing')
    require(receipt.get('tv_player_channels_control_preserved') is True and receipt.get('tv_group_counts_cached') is True,'2103230 channel/group contract missing')
    require(receipt.get('tv_hamburger_removed') is True and receipt.get('tv_grid_group_dropdown_removed') is True,'2103231 grid cleanup missing')
    require(receipt.get('tv_grid_settings_next_to_search') is True and receipt.get('tv_mini_player_adaptive_large') is True,'2103231 adaptive UI contract missing')
    require(receipt.get('tv_mini_player_preserved') is True and receipt.get('tv_navigation_hierarchy')=='drawer-groups-grid-player','2103231 preservation contract missing')
    require(receipt.get('tv_drawer_compact_integrated') is True and receipt.get('tv_drawer_stage_shift') is False,'2103232 integrated drawer contract missing')
    require(receipt.get('tv_drawer_destination_auto_close') is True and receipt.get('tv_live_flow')=='drawer-live-tv-groups-grid','2103232 drawer navigation contract missing')
    require(receipt.get('tv_glass_system') is True and receipt.get('tv_glass_reference_locked') is True,'2103233 glass-system receipt missing')
    require(receipt.get('tv_glass_real_time_blur') is False and receipt.get('tv_ambient_mode_retired') is True,'2103233 lightweight/Ambient contract missing')
    require(receipt.get('tv_glass_drawer') is True and receipt.get('tv_glass_playlist') is True and receipt.get('tv_glass_guide') is True,'2103233 glass coverage missing')
    require(receipt.get('tv_glass_preview') is True and receipt.get('tv_glass_sheets') is True and receipt.get('tv_glass_multiview') is True,'2103233 glass surface coverage missing')
    require(receipt.get('tv_drawer_inline_column') is True and receipt.get('tv_drawer_guide_overlay') is False,'2103234 inline drawer contract missing')
    require(receipt.get('tv_drawer_back_restores_underlay') is True and receipt.get('tv_drawer_groups_visible_while_open') is True,'2103234 drawer state contract missing')
    require(receipt.get('tv_playing_channel_indicator') is True and receipt.get('tv_playing_indicator_actual_session') is True,'2103234 playing indicator contract missing')
    require(receipt.get('tv_preview_instruction_removed') is True and receipt.get('tv_border_density_reduced') is True,'2103234 UI cleanup contract missing')
    require(receipt.get('tv_drawer_brand_compact') is True and receipt.get('tv_drawer_brand_single_line') is True,'2103235 drawer brand contract missing')
    require(receipt.get('tv_live_right_select_drawer') is True and receipt.get('tv_live_right_select_directory') is True and receipt.get('tv_right_select_scope')=='live-tv-only','2103235 Live TV Right-select scope missing')
    require(receipt.get('tv_vod_right_navigation_untouched') is True and receipt.get('tv_movies_dedicated_search') is True and receipt.get('tv_shows_dedicated_search') is True,'2103235 VOD navigation/search contract missing')
    require(receipt.get('tv_mini_player_playing_badge_removed') is True and receipt.get('tv_playing_channel_indicator') is True,'2103235 playing-indicator presentation contract missing')
    require(receipt.get('tv_grid_pulsing_playing_dot') is True and receipt.get('tv_playing_dot_actual_session') is True,'2103236 pulsing-dot contract missing')
    require(receipt.get('tv_playing_dot_normal_pulse_ms')==1320 and receipt.get('tv_playing_dot_night_cinema_pulse_ms')==1900,'2103236 pulse cadence missing')
    require(receipt.get('tv_playing_dot_handoff_ms')==180 and receipt.get('tv_playing_dot_color_morph_ms')==240,'2103236 dot transition contract missing')
    require(receipt.get('tv_playing_dot_oled_core_floor_alpha')==218 and receipt.get('tv_playing_dot_oled_glow_floor')==.58,'2103236 OLED dot contract missing')
    require(receipt.get('tv_playing_dot_ambient_independent') is True and receipt.get('tv_playing_dot_no_blur') is True,'2103236 lightweight dot contract missing')
    require(receipt.get('chooser_card_settings_removed') is True and receipt.get('chooser_infinity_settings_removed') is True and receipt.get('chooser_cobra_settings_removed') is True,'2103237 chooser control removal missing')
    require(receipt.get('cobra_explicit_start_destination')=='live_tv' and receipt.get('tv_cobra_startup_integrated_shell') is True and receipt.get('tv_cobra_startup_drawer_open') is True,'2103237 Cobra startup contract missing')
    require(receipt.get('tv_drawer_right_select') is True and receipt.get('tv_drawer_left_back') is True and receipt.get('tv_directory_right_select') is True and receipt.get('tv_directory_left_back') is True,'2103237 Live TV directional contract missing')
    require(receipt.get('tv_right_select_scope')=='live-tv-only' and receipt.get('tv_left_back_scope')=='live-tv-drawer-directory-only','2103237 directional scope drift')
    require(receipt.get('tv_section_owner_persistent') is True and receipt.get('tv_movies_persistent_until_drawer_change') is True and receipt.get('tv_shows_persistent_until_drawer_change') is True,'2103237 section ownership missing')
    require(receipt.get('tv_smart_return_cannot_override_vod_owner') is True,'2103237 VOD section ownership can be overridden')
    require(receipt.get('tv_vod_channels_control_removed') is True and receipt.get('tv_vod_multiview_control_removed') is True and receipt.get('tv_vod_channel_stepping_removed') is True,'2103237 VOD Live-TV control cleanup missing')
    require(receipt.get('tv_vod_live_rewind_removed') is True and receipt.get('tv_vod_go_live_removed') is True and receipt.get('tv_vod_live_timeline_removed') is True and receipt.get('tv_vod_live_record_removed') is True,'2103237 VOD live chrome cleanup missing')
    require(receipt.get('tv_vod_display_preserved') is True and receipt.get('tv_vod_more_preserved') is True and receipt.get('tv_vod_audio_subtitles_preserved') is True,'2103237 VOD applicable controls missing')
    require(receipt.get('tv_movies_tv_first_refinement') is True and receipt.get('tv_shows_tv_first_refinement') is True,'2103238 TV-first Movies/Shows refinement missing')
    require(receipt.get('tv_vod_hero_cinematic') is True and receipt.get('tv_vod_larger_poster_cards') is True,'2103238 cinematic VOD layout missing')
    require(receipt.get('tv_vod_popular_first') is True and receipt.get('tv_vod_recent_second') is True and receipt.get('tv_vod_genres_third') is True,'2103238 landing hierarchy missing')
    require(receipt.get('tv_movies_full_search') is True and receipt.get('tv_shows_full_search') is True,'2103238 full section search missing')
    require(receipt.get('tv_vod_search_live_narrowing') is True and receipt.get('tv_vod_search_on_screen_keyboard') is False,'2103239 custom-keyboard removal missing')
    require(receipt.get('tv_search_native_android_tv_ime') is True and receipt.get('tv_search_top_field_is_input') is True,'2103239 native TV search field missing')
    require(receipt.get('tv_vod_search_exact_title_priority') is True and receipt.get('tv_search_genre_text_matching') is True,'2103239 title/genre matching contract missing')
    require(receipt.get('tv_vod_search_debounce_ms')==150 and receipt.get('tv_vod_search_visible_result_cap')==35,'2103240 inline-search work budget missing')
    require(receipt.get('tv_search_results_full_width') is True and receipt.get('tv_focus_clip_protection') is True and receipt.get('tv_search_stale_refresh_guard') is True,'2103239 UI/stability polish missing')
    require(receipt.get('tv_vod_landing_search_inline') is True and receipt.get('tv_vod_search_separate_landing_button_removed') is True,'2103240 inline landing search missing')
    require(receipt.get('tv_vod_search_native_android_tv_ime') is True and receipt.get('tv_vod_search_empty_restores_cinematic_landing') is True,'2103240 landing search/IME contract missing')
    require(receipt.get('tv_remote_edge_guard_ms')==120 and receipt.get('tv_remote_repeat_suppressed') is True,'2103240 remote repeat guard missing')
    require(receipt.get('tv_remote_safe_click') is True and receipt.get('tv_directory_focus_epoch_guard') is True and receipt.get('tv_drawer_focus_epoch_guard') is True,'2103240 remote focus/click hardening missing')
    require(receipt.get('tv_remote_crash_hardening') is True and receipt.get('tv_remote_left_back_preserved') is True and receipt.get('tv_remote_right_select_preserved') is True,'2103240 remote contract missing')
    require(receipt.get('tv_live_structure_unchanged') is True and receipt.get('tv_live_end_to_end_polish') is True,'2103238 Live TV preservation/polish contract missing')
    require(receipt.get('tv_motion_lightweight') is True and receipt.get('tv_real_time_blur') is False,'2103238 lightweight motion contract missing')
    require(receipt.get('tv_performance_polish') is True and receipt.get('tv_stability_polish') is True,'2103235 stability/performance contract missing')
    require(receipt.get('tv_cache_restore_off_main') is True and receipt.get('tv_multiview_picker_focus_owner') is True,'2103224 performance/focus gates missing')
    require(receipt.get('tv_player_header_focus_graph') is True and receipt.get('tv_multiview_list_select_dispatch') is True and receipt.get('tv_grid_favorites_polished') is True,'2103224 native remote gates missing')
    require(receipt.get('multiview_fullscreen_reversible') is True,'2103222 Multi-View contract regressed')
    for name,row in receipt['files'].items():
        require(sha((source/name).read_bytes())==row['after'],'Source changed after audit: '+name)

def prepare(source:Path,base:Path,build:Path,out:Path):
    require(sha(base.read_bytes())==BASE_APK_SHA256,'Not exact passed 2103239 RC19 signed TV APK')
    source_preservation(source);sdk=Path(os.environ['ANDROID_HOME']);bt=sdk/'build-tools/34.0.0'
    original_ids=resource_ids(bt/'aapt2',base,out/'base-resources.txt');packaging=source/'tools/android/packaging'
    build.mkdir(parents=True,exist_ok=False)
    for name in ('build.gradle','settings.gradle','gradle.properties','gradlew'):shutil.copy2(packaging/name,build/name)
    shutil.copytree(packaging/'gradle',build/'gradle');(build/'gradlew').chmod(0o755);app=build/'xbmc';app.mkdir()
    values={'APP_PACKAGE':PACKAGE,'APP_NAME':'Kodi','APP_NAME_LC':'kodi','APP_VERSION':RELEASE,
            'APP_VERSION_CODE_ANDROID':str(VERSION),'TARGET_MINSDK':'21','TARGET_SDK':'35',
            'NDKROOT':str(sdk/'ndk'/os.environ.get('NDK_VER','21.4.7075529'))}
    for name in ('AndroidManifest.xml','build.gradle'):(app/name).write_text(configured(packaging/'xbmc'/(name+'.in'),values))
    (build/'stable-ids.txt').write_text(''.join(f'{PACKAGE}:{name} = {rid}\n' for name,rid in sorted(original_ids.items())))
    with (app/'build.gradle').open('a') as f:f.write('\nandroid.aaptOptions.additionalParameters "--stable-ids", rootProject.file("stable-ids.txt").absolutePath\n')
    registered=set(re.findall(r'\bsrc/([\w/]+\.java)\b',(source/'cmake/scripts/android/Install.cmake').read_text()))
    actual={str(p.relative_to(packaging/'xbmc/src'))[:-3] for p in (packaging/'xbmc/src').rglob('*.java.in')}
    require(registered==actual,'CMake/Java registration mismatch: '+repr(registered^actual))
    for name in sorted(registered):
        p=app/'java'/PACKAGE.replace('.','/')/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(configured(packaging/'xbmc/src'/(name+'.in'),values))
    shutil.copytree(packaging/'xbmc/res',app/'res')
    for name,dest in (('strings.xml','values'),('colors.xml','values'),('searchable.xml','xml')):
        p=app/'res'/dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(configured(packaging/'xbmc'/(name+'.in'),values))
    copies={'drawable/applaunch_screen.png':source/'media/applaunch_screen.png',
            'drawable-xxxhdpi/applaunch_screen.png':source/'media/applaunch_screen.png',
            'drawable/ic_recommendation_80dp.png':source/'media/icon80x80.png',
            'drawable-xhdpi/banner.png':packaging/'media/drawable-xhdpi/banner.png'}
    for density in ('ldpi','mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi'):
        name='drawable-'+density+'/ic_launcher.png';copies[name]=packaging/'media'/name
    for name,origin in copies.items():
        p=app/'res'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin,p)
    (build/'local.properties').write_text('sdk.dir='+str(sdk)+'\n')
    print(f'PASS: staged {len(registered)} Java sources and pinned {len(original_ids)} resource IDs; no native source/build')
    return original_ids

def manifest_tree(text:str):
    root=None;stack=[]
    for line in text.splitlines():
        stripped=line.lstrip();indent=len(line)-len(stripped)
        if stripped.startswith('E: '):
            node={'tag':stripped.split()[1],'attrs':{},'children':[]}
            while stack and stack[-1][0]>=indent:stack.pop()
            if stack:stack[-1][1]['children'].append(node)
            else:require(root is None,'Multiple manifest roots');root=node
            stack.append((indent,node))
        elif stripped.startswith('A: '):
            key,value=stripped[3:].split('=',1);require(stack,'Manifest attr outside element');stack[-1][1]['attrs'][key.split('(')[0]]=value
    require(root is not None,'Empty manifest');return root

def verify_manifest_pair(old_text:str,new_text:str):
    old,new=manifest_tree(old_text),manifest_tree(new_text)
    for tree in (old,new):
        tree['attrs'].pop('android:versionCode',None);tree['attrs'].pop('android:versionName',None)
    require(old==new,'Compiled manifest drift outside version identity')

def merge(base:Path,donor:Path,output:Path):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(donor) as b,zipfile.ZipFile(output,'w') as z:
        an,bn=set(a.namelist()),set(b.namelist());require(len(an)==len(a.namelist()) and len(bn)==len(b.namelist()),'Duplicate APK member')
        require(not a.testzip() and not b.testzip(),'APK CRC failure')
        require(not any(n.startswith(('lib/','assets/')) and not n.endswith('/') for n in bn),'Unexpected native/assets in Android-only donor')
        original_native,original_classes=dex_contract(a);compiled_native,compiled_classes=dex_contract(b)
        require(original_native==compiled_native,'JNI native descriptor inventory changed')
        core={n for n in original_classes if n.startswith('Lcom/projectinfinity/kodi/') and '$' not in n}
        require(core<=compiled_classes,'Native-facing Java class lost: '+repr(core-compiled_classes))
        for info in a.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n) or SIGNATURE.fullmatch(n):continue
            z.writestr(info,a.read(n))
        for info in b.infolist():
            n=info.filename
            if n=='AndroidManifest.xml' or DEX.fullmatch(n):z.writestr(info,b.read(n))
    return len(original_native),len(core)

def verify_bytes(base:Path,final:Path):
    with zipfile.ZipFile(base) as a,zipfile.ZipFile(final) as b:
        an,bn=set(a.namelist()),set(b.namelist())
        kept={n for n in an if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected=kept|{'AndroidManifest.xml'}|{n for n in bn if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(bn==expected,'Unexpected final APK member inventory')
        for name in sorted(kept):require(a.read(name)==b.read(name),'Protected APK payload changed: '+name)
        require(LIB in bn,'ARMv7 libkodi.so missing');require(sha(b.read(LIB))==BASE_ENGINE_SHA256,'ARMv7 native engine changed')
        require(not any(n.startswith('lib/arm64-v8a/') for n in bn),'arm64 payload leaked into TV candidate')
        require(not b.testzip(),'Final APK CRC failure');require(dex_contract(b)[0]==dex_contract(a)[0],'Final JNI contract changed')
        joined=b''.join(b.read(n) for n in bn if DEX.fullmatch(n))
        for token in (b'cobra_tv_grid_only_2103220',b'cobra_tv_remote_ui_2103221',b'cobra_tv_player_multiview_2103222',b'cobra_tv_hardening_2103223',
                      b'Return to Multi-View',b'Search and add',b'Enlarge screen',b'cobra_tv_player_tool_channels',b'Opening saved TV library',b'TV SYSTEM',b'cobra_tv_native_remote_2103224',b'cobra_tv_handoff_focus_2103225',b'cobra_tv_navigation_motion_2103230',b'cobra_tv_adaptive_ui_2103231',b'cobra_tv_integrated_drawer_2103232',b'cobra_tv_glass_system_2103233',b'cobra_tv_integrated_shell_playing_2103234',b'cobra_tv_final_polish_2103235',b'CobraTvPlayingDot',b'NORMAL_PULSE_MS',b'CINEMA_PULSE_MS',b'cobra_section_owner',b'cobra_start_destination',b'live_tv',b'LIVE_TV',b'MOVIES',b'SHOWS',b'Back to Movies',b'Back to Shows',b'cobraOnDemandPlayer',b'cobraSeekOnDemandBy',b'cobra_movies_search',b'cobra_shows_search',b'Search TV Shows',b'Search Movies',b'Type a title or narrow by genre',b'cobra_tv_movies_native_search_2103239',b'cobra_tv_shows_native_search_2103239',b'cobraTvVodSearchMatches',b'cobra_tv_movies_landing_search_2103240',b'cobra_tv_shows_landing_search_2103240',b'COBRA_TV_REMOTE_EDGE_GUARD_MS',b'cobraTvSafeRemoteClick',b'Find an exact movie',b'Find an exact show',b'FEATURED',b'Popular Now',b'Recent Releases',b'Lightweight Glass UI is always active.',b'PLAYING',b'Back to guide',b'cobra_tv_grid_settings',b'cobraTvShowGroupChooser',b'cobraTvSelectGroup',b'cobra_multi_filter:',b'onRenderedFirstFrame'):
            require(token in joined,'Missing 2103240 runtime marker: '+repr(token))
        require(b'experience-settings-infinity' not in joined and b'experience-settings-cobra' not in joined,'Choose Experience Settings tags survived compiled RC17 DEX')
        return {'native_files_byte_identical':sum(n.startswith('lib/') and not n.endswith('/') for n in kept),
                'asset_files_byte_identical':sum(n.startswith('assets/') and not n.endswith('/') for n in kept),
                'android_resources_byte_identical':True,'other_payload_entries_preserved':len(kept)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--base-apk',type=Path,required=True)
    p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();source,base,build,out=[x.resolve() for x in (a.source,a.base_apk,a.build_dir,a.out)]
    out.mkdir(parents=True,exist_ok=True);ids=prepare(source,base,build,out)
    env=dict(os.environ,KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',
             KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
    run('./gradlew','--no-daemon','--console=plain',':xbmc:assembleRelease',cwd=build,env=env)
    run('./gradlew','--no-daemon','--console=plain',':xbmc:dependencies','--configuration','releaseRuntimeClasspath',cwd=build,env=env,output=out/'android-dependencies.txt')
    donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk';require(donor.is_file(),'Donor APK missing')
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0';donor_ids=resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt')
    require(ids==donor_ids,'Compiled resource IDs do not match locked 2103221 table')
    unsigned=out/'Infinity-1.0.9-Cobra-Onn4KPro-TV-Search-Remote-Hardening-RC20-unsigned.apk'
    natives,core=merge(base,donor,unsigned)
    manifest=run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'manifest.txt')
    old_manifest=run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt');verify_manifest_pair(old_manifest,manifest)
    require('android.intent.category.LEANBACK_LAUNCHER' in manifest,'Leanback launcher missing')
    pip=[line for line in manifest.splitlines() if 'supportsPictureInPicture' in line]
    require(pip and all('0xffffffff' not in line.lower() for line in pip),'TV PiP unexpectedly enabled')
    for name in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):require(bool(os.environ.get(name)),'Missing permanent signing '+name)
    final=out/'Infinity-1.0.9-Cobra-Onn4KPro-TV-Search-Remote-Hardening-RC20.apk';run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt');require(CERT in cert.lower(),'Signer changed')
    badging=run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
    require(f"package: name='{PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'Wrong APK identity')
    require("application-label:'Infinity'" in badging and "native-code: 'armeabi-v7a'" in badging,'TV label/ABI changed')
    require('application-debuggable' not in badging,'Candidate is debuggable')
    preserved=verify_bytes(base,final)
    report={'schema':1,'build':VERSION,'version_name':RELEASE,'package':PACKAGE,'target_abi':'armeabi-v7a','hardening':True,'native_remote_architecture':True,'handoff_first_render':True,'multiview_focus_visible':True,'player_footer_unclipped':True,'multiview_two_to_one_session_preserved':True,'navigation_hierarchy':'drawer-groups-grid-player','back_reverses_hierarchy':True,'mini_player_preserved':True,'preview_engine_preserved':True,'player_channels_control_preserved':True,'group_counts_cached':True,'hamburger_removed':True,'grid_group_dropdown_removed':True,'settings_next_to_search':True,'mini_player_adaptive_large':True,'drawer_compact_integrated':True,'drawer_stage_shift':False,'drawer_destination_auto_close':True,'live_flow':'drawer-live-tv-groups-grid','glass_system':True,'glass_static_gradient':True,'real_time_blur':False,'ambient_mode_retired':True,'ambient_setting_exposed':False,'glass_drawer':True,'glass_playlist':True,'glass_guide':True,'glass_preview':True,'glass_sheets':True,'glass_player_surfaces':True,'glass_multiview':True,'drawer_inline_column':True,'drawer_guide_overlay':False,'drawer_back_restores_underlay':True,'drawer_groups_visible_while_open':True,'playing_channel_indicator':True,'playing_indicator_actual_session':True,'preview_instruction_removed':True,'border_density_reduced':True,'drawer_brand_compact':True,'drawer_brand_single_line':True,'drawer_power_unclipped':True,'live_right_select_drawer':True,'live_right_select_directory':True,'right_select_scope':'live-tv-only','vod_right_navigation_untouched':True,'movies_dedicated_search':True,'shows_dedicated_search':True,'mini_player_playing_badge_removed':True,'vod_session_cache_ms':300000,'performance_polish':True,'stability_polish':True,'ui_polish':True,'grid_pulsing_playing_dot':True,'playing_dot_actual_session':True,'playing_dot_focus_independent':True,'playing_dot_normal_pulse_ms':1320,'playing_dot_night_cinema_pulse_ms':1900,'playing_dot_handoff_ms':180,'playing_dot_color_morph_ms':240,'playing_dot_oled_core_floor_alpha':218,'playing_dot_oled_glow_floor':.58,'playing_dot_night_cinema_amber':'0xffffc247','playing_dot_ambient_independent':True,'playing_dot_frame_ms':33,'playing_dot_no_blur':True,'chooser_card_settings_removed':True,'chooser_infinity_settings_removed':True,'chooser_cobra_settings_removed':True,'cobra_explicit_start_destination':'live_tv','cobra_startup_integrated_shell':True,'cobra_startup_drawer_open':True,'cobra_startup_groups_visible':True,'drawer_right_select':True,'drawer_left_back':True,'directory_right_select':True,'directory_left_back':True,'left_back_scope':'live-tv-drawer-directory-only','section_owner_persistent':True,'section_owner_values':['LIVE_TV','MOVIES','SHOWS'],'movies_persistent_until_drawer_change':True,'shows_persistent_until_drawer_change':True,'live_persistent_until_drawer_change':True,'smart_return_cannot_override_vod_owner':True,'vod_player_origin_explicit':True,'vod_channels_control_removed':True,'vod_multiview_control_removed':True,'vod_channel_stepping_removed':True,'vod_last_channel_removed':True,'vod_channel_favorite_removed':True,'vod_live_rewind_removed':True,'vod_go_live_removed':True,'vod_live_timeline_removed':True,'vod_live_record_removed':True,'vod_epg_labels_removed':True,'vod_display_preserved':True,'vod_more_preserved':True,'vod_audio_subtitles_preserved':True,'vod_remote_seek_ms':30000,
            'movies_tv_first_refinement':True,'shows_tv_first_refinement':True,'vod_hero_cinematic':True,
            'vod_popular_first':True,'vod_recent_second':True,'vod_genres_third':True,'vod_larger_poster_cards':True,
            'movies_full_search':True,'shows_full_search':True,'vod_search_live_narrowing':True,
            'vod_search_on_screen_keyboard':False,'vod_search_android_text_input':True,'native_android_tv_ime':True,
            'search_top_field_is_input':True,'search_custom_keyboard_removed':True,'search_left_panel_removed':True,
            'search_genre_chips_removed':True,'search_genre_text_matching':True,'search_results_full_width':True,
            'search_results_below_input':True,'vod_search_exact_title_priority':True,'vod_search_genre_filters':False,
            'vod_search_focus_restore':True,
            'vod_search_section_scoped':True,'search_stale_refresh_guard':True,'search_ime_submit_to_results':True,
            'focus_clip_protection':True,'result_smooth_scroll':True,'ui_refinement_polish':True,
            'vod_landing_search_inline':True,'vod_search_separate_landing_button_removed':True,
            'vod_search_top_field_inline':True,'vod_search_native_android_tv_ime':True,
            'vod_search_inline_live_narrowing':True,'vod_search_empty_restores_cinematic_landing':True,
            'vod_search_debounce_ms':150,'vod_search_visible_result_cap':35,
            'remote_edge_guard_ms':120,'remote_repeat_suppressed':True,'remote_safe_click':True,
            'directory_focus_epoch_guard':True,'drawer_focus_epoch_guard':True,'remote_crash_hardening':True,
            'remote_left_back_preserved':True,'remote_right_select_preserved':True,'focus_target_attachment_guard':True,
            'live_end_to_end_polish':True,'live_structure_unchanged':True,'motion_lightweight':True,'real_time_blur':False,
            'base_build':2103239,'base_apk_sha256':BASE_APK_SHA256,'base_native_engine_sha256':BASE_ENGINE_SHA256,
            'apk':final.name,'apk_sha256':sha(final.read_bytes()),'signer_certificate_sha256':CERT,
            'compiled_jni_declarations_preserved':natives,'native_facing_java_classes_preserved':core,
            'resource_id_map_verified':len(ids),'source_built_android_layer':True,'native_recompiled':False,
            'fast_tv_packaging_lane':True,'smali_used':False,'runtime_device_tested':False,**preserved}
    (out/'ONN-TV-2103240-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    shutil.copy2(ROOT/'engine/background-resume-source.json',out/'background-resume-source.json')
    shutil.copy2(ROOT/'audit240/tv-search-remote-hardening-source.json',out/'tv-search-remote-hardening-source.json')
    unsigned.unlink()
    print('PASS: 2103240 RC20 inline VOD search + remote/focus crash hardening over exact passed 2103239 RC19 APK payload/native/resources; permanent signer verified')

if __name__=='__main__':main()
