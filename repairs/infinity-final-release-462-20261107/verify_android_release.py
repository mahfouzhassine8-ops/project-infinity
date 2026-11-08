"""Finite actual signed-APK Android journey; no shutdown or reset transport.

Only a fresh disposable API37/4KiB emulator is accepted. Normal Splash and
chooser admission, real native-provider Search and real GUI/IME actions.
Installation replaces the package normally; user data is never cleared.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse,codecs,hashlib,json,os,re,socket,subprocess,time
import xml.etree.ElementTree as ET

PACKAGE='com.projectinfinity.kodi'
CC='script.infinity.commandcenter'
QA='script.infinity.finalreleaseqa'
HOME='/sdcard/Android/data/'+PACKAGE+'/files/.kodi'
PROFILE=HOME+'/userdata'
QAROOT=PROFILE+'/addon_data/'+QA
PROVIDERS={'plugin.video.watchnixtoons2','plugin.video.umbrella'}

class Device:
    def __init__(self,out):
        self.out=out;self.adb_bin=Path(os.environ['ANDROID_HOME'])/'platform-tools/adb'
        devices=self.run([self.adb_bin,'devices']).stdout
        found=re.findall(r'^(emulator-\d+)\s+device$',devices,re.M)
        assert len(found)==1,'ONE_DISPOSABLE_EMULATOR_REQUIRED';self.serial=found[0]
        assert self.shell('getprop','ro.kernel.qemu').strip()=='1'
        assert self.shell('getprop','ro.build.version.sdk').strip()=='37'
        assert self.shell('getconf','PAGESIZE').strip()=='4096'
        self.sequence=0;self.pid=None
    def run(self,args,timeout=60,binary=False):
        return subprocess.run(list(map(str,args)),capture_output=True,text=not binary,timeout=timeout)
    def adb(self,*args,timeout=60,check=True):
        result=self.run([self.adb_bin,'-s',self.serial,*args],timeout)
        if check:assert result.returncode==0,(args,result.stdout,result.stderr)
        return result.stdout+result.stderr
    def shell(self,*args,timeout=60,check=True):return self.adb('shell',*args,timeout=timeout,check=check)
    def until(self,fn,label,seconds=90):
        end=time.monotonic()+seconds;last=None
        while time.monotonic()<end:
            try:
                value=fn()
                if value:return value
            except (OSError,ValueError,RuntimeError,TimeoutError,socket.timeout) as error:last=repr(error)
            time.sleep(.5)
        raise RuntimeError('Timed out: '+label+'; '+str(last))
    def alive(self):
        current=self.shell('pidof',PACKAGE+':kodi',check=False).strip()
        assert current==str(self.pid),'NATIVE_ENGINE_DIED_OR_RESTARTED'
    def rpc(self,method,params=None,timeout=25):
        request=dict(jsonrpc='2.0',id=464,method=method)
        if params is not None:request['params']=params
        with socket.create_connection(('127.0.0.1',19090),timeout=timeout) as conn:
            conn.settimeout(timeout);conn.sendall(json.dumps(request).encode())
            decoder=json.JSONDecoder();utf8=codecs.getincrementaldecoder('utf-8')();pending='';received=0
            while received<8*1024*1024:
                chunk=conn.recv(65536)
                if not chunk:break
                received+=len(chunk);pending+=utf8.decode(chunk)
                while pending.strip():
                    pending=pending.lstrip()
                    try:reply,end=decoder.raw_decode(pending)
                    except ValueError:break
                    pending=pending[end:]
                    if reply.get('id')!=464:continue
                    if 'error' in reply:raise RuntimeError(method+': '+json.dumps(reply['error']))
                    return reply.get('result')
        raise RuntimeError('Incomplete bounded JSONRPC reply: '+method)
    def read_json(self,path):return json.loads(self.shell('cat',path,check=False))
    def nodes(self,label):
        self.shell('uiautomator','dump','/sdcard/Download/infinity-final-ui.xml',timeout=45)
        raw=self.shell('cat','/sdcard/Download/infinity-final-ui.xml')
        (self.out/(label+'.xml')).write_text(raw)
        return ET.fromstring(raw)
    @staticmethod
    def center(node):
        m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''));assert m
        a,b,c,d=map(int,m.groups());assert c>a and d>b
        return (a+c)//2,(b+d)//2
    def tap(self,node):self.shell('input','tap',*self.center(node))
    def enter(self,label):
        self.shell('am','start','-W','-n',PACKAGE+'/.Splash',timeout=90)
        end=time.monotonic()+120;tapped=False
        while time.monotonic()<end:
            pid=self.shell('pidof',PACKAGE+':kodi',check=False).strip()
            if pid.isdigit():self.pid=int(pid);break
            tree=self.nodes(label+'-chooser');parents={c:p for p in tree.iter() for c in p}
            cards=[]
            for node in tree.iter('node'):
                if node.get('text','').strip().lower()!='infinity':continue
                owner=node
                while owner is not None and owner.get('clickable')!='true':owner=parents.get(owner)
                if owner is not None:cards.append(owner)
            if cards and not tapped:
                centers={self.center(n) for n in cards};assert len(centers)==1
                self.shell('input','tap',*next(iter(centers)));tapped=True
            time.sleep(1)
        else:raise RuntimeError('NORMAL_CHOOSER_DID_NOT_START_KODI')
        self.adb('forward','tcp:19090','tcp:9090')
        def native_ready():
            self.alive()
            return self.rpc('JSONRPC.Ping')=='pong'
        self.until(native_ready,'native RPC readiness',240)
        self.alive();self.sequence=0
        return dict(pid=self.pid,entry='Original Splash and original Infinity card/default admission',chooser_tap=tapped)
    def start_qa(self):
        for aid in (QA,'plugin.video.infinity.finalreleaseqaclip'):
            addon=self.rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['enabled']))['addon']
            if not addon['enabled']:assert self.rpc('Addons.SetAddonEnabled',dict(addonid=aid,enabled=True))=='OK'
        assert self.rpc('Addons.GetAddonDetails',dict(addonid=QA))['addon']['type']=='xbmc.python.script','OBSERVER_MUST_BE_SCRIPT_ONLY'
        assert self.rpc('Addons.ExecuteAddon',dict(addonid=QA))=='OK'
        self.until(lambda:self.read_json(QAROOT+'/ready.json').get('pid')==self.pid,'fresh QA observer',90)
        self.dismiss_immersive_education()
    def dismiss_immersive_education(self):
        # Original stock OS tutorial only, acknowledged with measured input.
        # Never disable an OS/app guard or click an unknown provider prompt.
        def visible():
            dump=self.shell('dumpsys','window','windows')
            rows=[r for r in re.split(r'(?m)^  Window #\d+ ',dump) if 'ImmersiveModeConfirmation}' in r.split('\n')[0] and 'isVisible=true' in r]
            return dump,rows
        dump,rows=visible()
        if not rows:return False
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'infinity-preview-2103450-fullscreen-display/android-qa'))
        from immersive_prompt import locate
        from PIL import Image
        (self.out/'OS-immersive-window.txt').write_text(dump)
        deadline=time.monotonic()+8;previous=None;number=0
        while time.monotonic()<deadline:
            dump,rows=visible();assert len(rows)==1,'ONE_ACTUAL_OS_TUTORIAL_WINDOW_REQUIRED'
            row=rows[0]
            assert 'mOwnerUid=1000' in row or re.search(r'package(?:Name)?=com\.android\.systemui\b',row),'TRUSTED_SYSTEM_UI_OWNER_REQUIRED'
            region=re.search(r'touchable region=SkRegion\(\((-?\d+),(-?\d+),(-?\d+),(-?\d+)\)\)',row)
            assert region,'OS_TUTORIAL_TOUCHABLE_REGION_REQUIRED'
            region=list(map(int,region.groups()));name=self.screenshot('OS-immersive-'+str(number));number+=1
            try:bounds=locate(Image.open(self.out/name).convert('RGB'),region,self.out/('OS-immersive-OCR-'+str(number)))
            except AssertionError:previous=None;time.sleep(.1);continue
            target=(bounds,region)
            if target==previous:
                a,b,c,d=bounds;self.shell('input','tap',str((a+c)//2),str((b+d)//2));break
            previous=target;time.sleep(.1)
        else:raise RuntimeError('OS_TUTORIAL_HAS_NO_STABLE_VERIFIED_GOT_IT_TARGET')
        self.until(lambda:not visible()[1],'actual OS fullscreen tutorial closes',3.5)
        return True
    def command(self,action,seconds=90,**params):
        self.alive();self.sequence+=1
        req=dict(pid=self.pid,sequence=self.sequence,action=action,**params)
        local=self.out/'request.json';local.write_text(json.dumps(req))
        self.adb('push',local,QAROOT+'/request.json')
        def answer():
            reply=self.read_json(QAROOT+'/reply.json')
            return reply if reply.get('pid')==self.pid and reply.get('sequence')==self.sequence else None
        reply=self.until(answer,'selected '+action,seconds)
        (self.out/('%03d-%s.json'%(self.sequence,action))).write_text(json.dumps(reply,indent=2)+'\n')
        assert reply['passed'],reply
        self.alive();return reply['result']
    def screenshot(self,label):
        result=self.run([self.adb_bin,'-s',self.serial,'exec-out','screencap','-p'],binary=True)
        assert result.returncode==0 and result.stdout.startswith(b'\x89PNG\r\n\x1a\n')
        path=self.out/(label+'.png');path.write_bytes(result.stdout);return path.name
    def submit_search_all(self,query,cycle):
        # Native Search focuses its EditText and asynchronously shows the IME.
        # Never tap bounds captured before that resize: they may now hit a
        # provider row. Require the actual focused editor and selected All row.
        self.until(lambda:'mInputShown=true' in self.shell('dumpsys','input_method'),'actual shown Search IME',45)
        def form(label):
            tree=self.nodes(label)
            edits=[n for n in tree.iter('node') if n.get('class')=='android.widget.EditText' and n.get('enabled')=='true' and n.get('package')==PACKAGE]
            alls=[n for n in tree.iter('node') if n.get('content-desc') in ('Search All, selected','Search All, select provider') and n.get('clickable')=='true']
            submits=[n for n in tree.iter('node') if n.get('content-desc')=='Submit Infinity Search']
            assert len(edits)==len(alls)==len(submits)==1,'ONE_REAL_SEARCH_FORM_REQUIRED'
            return edits[0],alls[0],submits[0]
        prefix='search-'+str(cycle)
        edit,allrow,submit=form(prefix+'-IME-ready')
        assert edit.get('focused')=='true','NATIVE_SEARCH_EDITOR_MUST_ALREADY_HAVE_FOCUS'
        self.shell('input','text',query.replace(' ','%s'))
        # Two consecutive fresh layouts must agree before touching the All row.
        first=form(prefix+'-typed-1');second=form(prefix+'-typed-2')
        assert first[1].get('bounds')==second[1].get('bounds'),'SEARCH_LAYOUT_MUST_BE_STABLE_AFTER_IME'
        assert second[0].get('text')==query,'EXACT_QUERY_MUST_BE_VISIBLE_IN_REAL_EDITOR'
        self.tap(second[1])
        edit,allrow,submit=form(prefix+'-All-selected')
        assert allrow.get('content-desc')=='Search All, selected' and submit.get('text')=='Search All','ACTUAL_SEARCH_ALL_SELECTION_REQUIRED'
        assert edit.get('focused')=='true' and edit.get('text')==query,'EXACT_FOCUSED_QUERY_BEFORE_REAL_IME_SUBMISSION'
        self.shell('input','keyevent','66')
    def install(self,path,label):
        result=self.adb('install','--no-streaming','-r',path,timeout=300)
        (self.out/(label+'-INSTALL.txt')).write_text(result)
        assert 'Success' in result

def expected_modules(apk):
    with ZipFile(apk) as z:
        base='assets/addons/';payload=z.read(base+CC+'/INFINITY-MODULES.v1').decode()
        module_files={row[2]:row[1] for line in payload.splitlines() if (row:=line.split('\t'))[0]=='file'}
        controller={n:hashlib.sha256(z.read(base+CC+'/'+n)).hexdigest() for n in ('infinity_search.py','plugin.py','addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')}
        skin={n:hashlib.sha256(z.read(base+'skin.infinity.diggz/'+n)).hexdigest() for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json','unified/DialogVideoInfo.xml','unified/Includes_InfinityMediaLists.xml')}
    return module_files,controller,skin

def verify_successor(device,apk,version):
    wanted={CC:'0.3.5.'+('62' if version==2103464 else '63'),'skin.infinity.diggz':'1.0.5.'+('270' if version==2103464 else '271')}
    def ready():
        values={aid:device.rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['version']))['addon']['version'] for aid in wanted}
        return values==wanted
    device.until(ready,'actual installed component versions'+str(version),240)
    actual=device.command('snapshot',full=True)
    assert actual['components']==wanted and actual['skin']=='skin.infinity.diggz'
    modules,controller,skin=expected_modules(apk)
    assert actual['module_files']==modules and len(modules)==78,'ACTUAL_78_INSTALLED_MODULE_FILES_MUST_MATCH_APK'
    assert actual['controller_files']==controller,'ACTUAL_INSTALLED_CONTROLLER_IDENTITY'
    assert actual['skin_files']==skin,'ACTUAL_INSTALLED_SKIN_SOURCE_AND_METADATA'
    assert actual['controller_path'].endswith('/.kodi/addons/'+CC),'EXTERNAL_INSTALL_OVER_WAS_NOT_VERIFIED'
    return actual

def verify(parent,candidate,recovery,fixture,out):
    assert not out.exists();out.mkdir(parents=True)
    report=dict(status='RUNNING_SELECTED_ANDROID_GATES',parent=2103462,candidate=2103464,recovery=2103465,cases=[],actual_provider_versions='PinnedWatchNixtoons2 0.14.24 and Umbrella6.7.729; not claimed as installed Fold versions',physical_Fold='NOT_RUN',shutdown='NOT_SELECTED',accepted_pointer_updated=False,public_release=False)
    def save(): (out/'ANDROID-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    def passed(case,**detail):report['cases'].append(dict(case=case,status='PASS',**detail));save()
    device=None
    try:
        scope=json.loads((Path(__file__).parent/'ANDROID-SCOPE.json').read_text())
        assert scope['operation']=='verify-signed464465' and scope['application_tests'] is True
        device=Device(out)
        assert not device.shell('pm','list','packages',PACKAGE).strip(),'FRESH_DISPOSABLE_INSTALL_ONLY'
        report['target']={n:device.shell('getprop',n).strip() for n in ('ro.build.fingerprint','ro.build.version.sdk','ro.product.cpu.abilist','ro.dalvik.vm.native.bridge')}
        device.shell('wm','size','1080x2520');device.shell('wm','density','420')
        device.install(parent,'parent462')
        for args in [('appops','set',PACKAGE,'MANAGE_EXTERNAL_STORAGE','allow'),('pm','grant',PACKAGE,'android.permission.RECORD_AUDIO'),('pm','grant',PACKAGE,'android.permission.POST_NOTIFICATIONS')]:device.shell(*args)
        device.shell('mkdir','-p',HOME)
        device.adb('push',str(fixture/'home')+'/.',HOME)
        # ADB-created backing directories initially belong to shell/root.
        # Restore the normal app UID/SELinux labels on this fresh qemu fixture;
        # never change an APK, Android protection or a real-device directory.
        device.adb('root');device.adb('wait-for-device')
        uid=device.shell('stat','-c','%u','/data/user/0/'+PACKAGE).strip()
        assert uid.isdigit() and int(uid)>=10000,'EXACT_FRESH_APP_UID_REQUIRED'
        backing='/data/media/0/Android/data/'+PACKAGE
        ownership_before=device.shell('ls','-ldn',backing,backing+'/files',backing+'/files/.kodi')
        device.shell('chown','-R',uid+':'+uid,backing)
        device.shell('restorecon','-RF',backing)
        ownership_after=device.shell('ls','-ldn',backing,backing+'/files',backing+'/files/.kodi')
        report['fresh_fixture_ownership']=dict(app_uid=int(uid),before=ownership_before,after=ownership_after,only_disposable_package_tree=True,APK_modified=False,app_security_changed=False)
        # Keep this disposable debuggable emulator's ADB transport privileged
        # so it can read the app-owned observer/profile files. The application
        # itself keeps the ordinary UID above; SELinux and app guards stay on.
        report['fresh_fixture_ownership']['ADB_transport']='Debug-emulator root retained only for test-file observation; application UID unchanged'
        # The exact parent's normal entry is already qualified in42423578286.
        # Do not repeat buggy old-engine execution before testing its successor.
        # Actual install-over remains mandatory: exact parent package, same UID,
        # authenticated61/268 files and existing-data sentinel, then normal464.
        parent_package=device.shell('dumpsys','package',PACKAGE)
        assert re.search(r'\bversionCode=2103462\b',parent_package)
        fixture_addons=fixture/'home/addons'
        manifest=(fixture_addons/CC/'INFINITY-MODULES.v1').read_text()
        names=[row[2] for line in manifest.splitlines() if (row:=line.split('\t'))[0]=='file']
        names += [CC+'/'+n for n in ('addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')]
        names += ['skin.infinity.diggz/'+n for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json','unified/DialogVideoInfo.xml','unified/Includes_InfinityMediaLists.xml')]
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
        expected={HOME+'/addons/'+n:hashlib.sha256((fixture_addons/n).read_bytes()).hexdigest() for n in names}
        actual={line.split(None,1)[1].lstrip('*'):line.split(None,1)[0] for line in device.shell('sha256sum',*expected).splitlines()}
        assert actual==expected,'EXACT_PREUPDATE_EXTERNAL61_268_ON_ANDROID'
        sentinel=device.shell('cat',PROFILE+'/release-data-sentinel.txt')
        assert sentinel=='preserve-disposable-preupdate-data-464465-v1'
        report['parent_entry']=dict(status='REUSED_EXISTING_PARENT_QUALIFICATION',run=42423578286,execution_in_this_run='NOT_REPEATED',reason='Selected successor correction does not require repeating original native-engine startup')
        passed('authenticated_current_external61_268_before_exact462_update',app_uid=int(uid),package_version=2103462,authenticated_existing_files=actual,user_data_sentinel_present=True,parent_runtime_evidence_reused=42423578286)
        device.install(candidate,'candidate464');report['candidate_entry']=device.enter('candidate464')
        assert device.shell('stat','-c','%u','/data/user/0/'+PACKAGE).strip()==uid,'INSTALL_OVER_UID_PRESERVED'
        inputs=json.loads((fixture/'ANDROID-INPUTS.json').read_text())
        for row in inputs['original_provider_archives']:
            aid=row['addon'];details=device.rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['enabled','version']))['addon']
            assert details['version']==row['version']
            if not details['enabled']:assert device.rpc('Addons.SetAddonEnabled',dict(addonid=aid,enabled=True))=='OK'
        device.start_qa();init=device.command('first-use',seconds=1150)
        actual=verify_successor(device,candidate,2103464)
        assert device.shell('cat',PROFILE+'/release-data-sentinel.txt')==sentinel
        passed('actual_462_to464_install_over_and78_signed_module_files',snapshot=actual,user_data_sentinel_preserved=True,app_uid_preserved=True,first_use=init)
        for mode,width,height,density in [('front',1080,2520,420),('inner',1600,1800,320)]:
            device.shell('wm','size',str(width)+'x'+str(height));device.shell('wm','density',str(density));time.sleep(2)
            device.command('home')
            for theme in ('yes','no'):
                device.shell('cmd','uimode','night',theme);time.sleep(3);device.alive()
                appearance=device.command('snapshot')['appearance_observation']
                passed('layout_snapshot_'+mode+'_'+theme,screenshot=device.screenshot(mode+'-'+theme+'-home'),appearance_observation=appearance,interpretation='Actual emulator surface for visual inspection; no automatic Fold or white-line PASS')
        device.shell('wm','size','1080x2520');device.shell('wm','density','420');device.shell('cmd','uimode','night','yes')
        queries=[('movie','The Matrix'),('movie','Just Friends'),('movie','Inception'),('movie','Toy Story'),('movie','Spirited Away'),('movie','Finding Nemo'),('tv','Re:zero'),('tv','SpongeBob')]
        for cycle,(media,query) in enumerate(queries):
            device.command('home');device.command('search',media=media)
            device.submit_search_all(query,cycle)
            def results():
                value=device.command('snapshot')
                if value['window']!=10025 or 'action=search-all' not in value['labels']['Container.FolderPath']:return None
                headings=[r for r in value.get('rows',[]) if r['provider'] in PROVIDERS and re.search(r' — \d+ results$',r['label'])]
                providers={r['provider'] for r in headings}
                good=[r for r in value.get('rows',[]) if r['provider'] in PROVIDERS and not re.search(r' — \d+ results$',r['label']) and r['file'].startswith('plugin://'+r['provider']+'/')]
                if providers==PROVIDERS and good:return value,headings,good
                return None
            value,headings,good=device.until(results,'actual two-provider grouped native results',160)
            assert not any('state changed' in r['label'].lower() for r in value['rows'])
            if query=='Re:zero':assert any(r['provider']=='plugin.video.watchnixtoons2' for r in good),'ACTUAL_NIXTOONS_POSITIVE_RESULT_REQUIRED'
            device.alive()
            device.shell('input','swipe','820','1650','820','750','500');device.shell('input','swipe','820','750','820','1650','500')
            if cycle in (0,7):device.command('select-row',index=headings[0]['index'],file=headings[0]['file'],seconds=160)
            passed('real_native_Search_cycle_'+str(cycle+1),query=query,providers=sorted(PROVIDERS),visible_provider_rows=len(good),heading_navigation_tested=cycle in (0,7),pid=device.pid)
        device.command('home');watched=device.command('watched',seconds=120)
        passed('actual_watched_and_unwatched_popup_callbacks',details=watched)
        for control,name in [(8,'Play'),(9012,'Trailer')]:
            device.command('home');info=device.command('info',seconds=60)
            image=device.screenshot('Info-'+name)
            playback=device.command('info-click',control=control,seconds=75)
            passed('actual_Info_'+name+'_control',Info=info,playback=playback,screenshot=image)
        device.command('home');files=device.command('downloads')
        passed('native_Downloads_Files_observation',snapshot=files,screenshot=device.screenshot('Downloads-Files'),interpretation='Native Files route; exact visible entries require report inspection')
        device.command('home');device.alive()
        oldpid=device.pid;device.install(recovery,'recovery465');report['recovery_entry']=device.enter('recovery465')
        assert oldpid!=device.pid;device.start_qa();restored=verify_successor(device,recovery,2103465)
        assert device.shell('cat',PROFILE+'/release-data-sentinel.txt')==sentinel
        passed('actual_464_to465_forward_recovery78_files_and_data_preservation',snapshot=restored,restored_functional_reference='Authenticated current268 plus exact462 native, with monotonic metadata; original Search limitations restored',user_data_sentinel_preserved=True)
        report['status']='PASS_SELECTED_ANDROID_EXECUTION_VISUAL_REVIEW_PENDING'
        report['remaining']='Inspect screenshots/Downloads observations and white-line evidence; actual Samsung/Fold acceptance pending once only'
    except BaseException as error:
        report.update(status='FAIL_SELECTED_ANDROID_GATE',failure=type(error).__name__+': '+str(error),traceback=__import__('traceback').format_exc())
        raise
    finally:
        if device:
            try:(out/'KODI-LOG.txt').write_text(device.shell('cat',HOME+'/temp/kodi.log',check=False))
            except Exception as e:report['log_error']=str(e)
            try:(out/'LOGCAT.txt').write_text(device.adb('logcat','-d','-v','threadtime',timeout=60,check=False))
            except Exception as e:report['logcat_error']=str(e)
            try:device.screenshot('final-observation')
            except Exception:pass
        save();print(report['status'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('parent','candidate','recovery','fixture','out'):p.add_argument('--'+n,type=Path,required=True)
    verify(**vars(p.parse_args()))
