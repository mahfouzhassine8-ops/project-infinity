"""Finite actual signed-APK Android journey; no shutdown or reset transport.

Only a fresh disposable API37/4KiB emulator is accepted. Normal Splash and
chooser admission, real native-provider Search and real GUI/IME actions.
Installation replaces the package normally; user data is never cleared.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse,hashlib,json,os,re,socket,subprocess,time
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
            conn.settimeout(timeout);conn.sendall(json.dumps(request).encode()+b'\n');data=b''
            while len(data)<8*1024*1024:
                chunk=conn.recv(65536)
                if not chunk:break
                data+=chunk
                try:reply=json.loads(data)
                except (ValueError,UnicodeDecodeError):continue
                if 'error' in reply:raise RuntimeError(method+': '+json.dumps(reply['error']))
                assert reply.get('id')==464
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
        self.until(lambda:self.rpc('JSONRPC.Ping')=='pong','native RPC readiness',240)
        self.alive();self.sequence=0
        return dict(pid=self.pid,entry='Original Splash and original Infinity card/default admission',chooser_tap=tapped)
    def start_qa(self):
        addon=self.rpc('Addons.GetAddonDetails',dict(addonid=QA,properties=['enabled']))['addon']
        if not addon['enabled']:assert self.rpc('Addons.SetAddonEnabled',dict(addonid=QA,enabled=True))=='OK'
        assert self.rpc('Addons.ExecuteAddon',dict(addonid=QA))=='OK'
        self.until(lambda:self.read_json(QAROOT+'/ready.json').get('pid')==self.pid,'fresh QA observer',90)
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
        report['parent_entry']=device.enter('parent462')
        inputs=json.loads((fixture/'ANDROID-INPUTS.json').read_text())
        for row in inputs['original_provider_archives']:
            aid=row['addon'];details=device.rpc('Addons.GetAddonDetails',dict(addonid=aid,properties=['enabled','version']))['addon']
            assert details['version']==row['version']
            if not details['enabled']:assert device.rpc('Addons.SetAddonEnabled',dict(addonid=aid,enabled=True))=='OK'
        device.start_qa();init=device.command('first-use',seconds=1150)
        parent_snapshot=device.command('snapshot',full=True)
        assert parent_snapshot['components']=={CC:'0.3.5.61','skin.infinity.diggz':'1.0.5.268'}
        assert parent_snapshot['skin']=='skin.infinity.diggz'
        sentinel=device.shell('cat',PROFILE+'/release-data-sentinel.txt')
        assert sentinel=='preserve-disposable-preupdate-data-464465-v1'
        passed('authenticated_current_external61_268_on_exact462',snapshot=parent_snapshot,first_use=init)
        oldpid=device.pid;device.install(candidate,'candidate464');report['candidate_entry']=device.enter('candidate464')
        assert oldpid!=device.pid
        device.start_qa();actual=verify_successor(device,candidate,2103464)
        assert device.shell('cat',PROFILE+'/release-data-sentinel.txt')==sentinel
        passed('actual_462_to464_install_over_and78_signed_module_files',snapshot=actual,user_data_sentinel_preserved=True)
        for mode,width,height,density in [('front',1080,2520,420),('inner',1600,1800,320)]:
            device.shell('wm','size',str(width)+'x'+str(height));device.shell('wm','density',str(density));time.sleep(2)
            device.command('home')
            for theme in ('yes','no'):
                device.shell('cmd','uimode','night',theme);time.sleep(3);device.alive()
                passed('layout_snapshot_'+mode+'_'+theme,screenshot=device.screenshot(mode+'-'+theme+'-home'),interpretation='Actual emulator surface for visual inspection; no automatic Fold or white-line PASS')
        device.shell('wm','size','1080x2520');device.shell('wm','density','420');device.shell('cmd','uimode','night','yes')
        queries=[('movie','The Matrix'),('movie','Just Friends'),('movie','Inception'),('movie','Toy Story'),('movie','Spirited Away'),('movie','Finding Nemo'),('tv','Re:zero'),('tv','SpongeBob')]
        for cycle,(media,query) in enumerate(queries):
            device.command('home');device.command('search',media=media)
            def keyboard():
                tree=device.nodes('search-'+str(cycle))
                edits=[n for n in tree.iter('node') if n.get('class')=='android.widget.EditText' and n.get('enabled')=='true']
                return (tree,edits[0]) if len(edits)==1 else None
            tree,edit=device.until(keyboard,'actual original Infinity Search EditText',60)
            device.tap(edit)
            device.until(lambda:'mInputShown=true' in device.shell('dumpsys','input_method'),'actual shown IME',30)
            device.shell('input','text',query.replace(' ','%s'))
            # Submit through real Android IME; no synthetic keyboard callback.
            device.shell('input','keyevent','66')
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
