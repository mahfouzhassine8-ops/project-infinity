"""Disposable independent negative control; never shipped in the APK."""
from pathlib import Path
import json
import time

ADDON='script.infinity.unsafeproof.7fa29'
CONTENTS='controlled unsafe write\n'
SCRIPT='''import json,os,subprocess,time
from pathlib import Path
import xbmcaddon,xbmcvfs
root=Path(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
root.mkdir(parents=True,exist_ok=True)
marker=root/'unknown-native-write.txt'
# Deliberately outside all reviewed read-only child contracts. Real system
# shell writes only this disposable test add-on's marker, then exits naturally.
child=subprocess.Popen(['/system/bin/sh','-c','printf "controlled unsafe write\\\\n" > "$1"; /system/bin/sleep 12',
    'infinity-unsafe-control',str(marker)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
deadline=time.monotonic()+10
while time.monotonic()<deadline and not marker.exists():time.sleep(.05)
if not marker.exists():raise RuntimeError('Actual controlled write was not observed')
(root/('unsafe-ready-'+str(os.getpid())+'.json')).write_text(json.dumps(dict(
    pid=os.getpid(),child_pid=child.pid,marker=str(marker),child_scope_readonly=False)))
child.communicate(timeout=20)
'''


def require(value,message):
    if not value:raise AssertionError(message)


def stage(folder,args,report,device,aid):
    import android17_candidate_probe as candidate
    candidate.require_disposable(device)
    if args.case!='final-participant' or aid!='service.future.persistence.7fa29' or Path(folder).resolve()!=args.out.resolve()/'fixture':
        raise ValueError('Only exact disposable independent participant stage may contain the negative control')
    target=Path(folder)/ADDON
    if target.exists() or target.is_symlink():raise ValueError('Existing unsafe test fixture refused')
    target.mkdir()
    (target/'addon.xml').write_text('<addon id="'+ADDON+'" name="Disposable independent safety control" version="1.0.0" provider-name="Disposable CI"><requires><import addon="xbmc.python" version="3.0.0"/></requires><extension point="xbmc.python.script" library="default.py"/><extension point="xbmc.addon.metadata"><summary lang="en_GB">Independently selected controlled unsafe writer</summary><description lang="en_GB">Fresh emulator fixture, never shipped</description><platform>all</platform><license>GPL-2.0-or-later</license></extension></addon>')
    (target/'default.py').write_text(SCRIPT)
    report['controlled_unsafe_fixture']=dict(addon=ADDON,automatically_started=False,production_APK_changed=False)


def verify_refusal(receipt,owner,processes):
    require(receipt.get('owner')==owner['owner'] and receipt.get('pid')==owner['pid'],'Unsafe case receipt identity differs')
    require(receipt.get('phase')=='CHECKPOINT_FAILED','Opaque writer was not refused')
    require(all(receipt.get(k) is False for k in ('checkpoint_saved','authorization_consumed','process_death_confirmed')),'Unsafe writer received a save or death claim')
    native=receipt.get('last_native_status',{})
    require(native.get('owner')==owner['owner'] and native.get('pid')==owner['pid'],'Native unsafe refusal identity differs')
    blockers=native.get('script_persistence',{}).get('blockers',[])
    require(any(row.get('writer','').startswith(ADDON+':') and row.get('blocking') is True and
        row.get('reason') in ('external_or_opaque_writer_requires_explicit_participant','unobserved_native_child_process') for row in blockers),
        'Actual native refusal does not identify the controlled writer')
    require(any(row.get('pid')==owner['pid'] for row in processes),'Engine died after unsafe refusal')
    require(native.get('essential_writes_durable') is False and native.get('essential_write_blockers'),'Unsafe essential write accounting was waived')
    require(any(ADDON in str(value) for value in native['essential_write_blockers']),'Controlled writer is not an actual essential blocker')


def enable(device,out):
    value=device.rpc('Addons.GetAddonDetails',{'addonid':ADDON,'properties':['version','enabled']})['addon']
    require(value.get('version')=='1.0.0','Unexpected disposable unsafe control')
    if not value.get('enabled'):
        require(device.rpc('Addons.SetAddonEnabled',{'addonid':ADDON,'enabled':True})=='OK','Cannot enable disposable unsafe control')


def run(transport,owner,out):
    out=Path(out);report=dict(passed=False,expected='actual opaque writer refusal; no successful Close claim',owner=owner)
    save=lambda:(out/'UNSAFE-WRITER-CONTROL.json').write_text(json.dumps(report,indent=2)+'\n')
    profile=transport.PROFILE+'/addon_data/'+ADDON
    target=profile+'/unsafe-ready-'+str(owner['pid'])+'.json'
    try:
        transport.rpc('Addons.ExecuteAddon',{'addonid':ADDON,'wait':False})
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            ready=transport.read_json(target)
            if ready.get('pid')==owner['pid']:break
            time.sleep(.1)
        else:raise AssertionError('Actual controlled unsafe writer did not start')
        report['actual_writer']=ready;save()
        require(type(ready.get('child_pid')) is int and ready['child_pid']>0 and ready['child_pid']!=owner['pid'],'Actual child identity absent')
        require(ready.get('child_scope_readonly') is False,'Unknown child claimed read-only scope')
        canonical_profile=transport.shell('readlink','-f',profile).strip()
        require(canonical_profile=='/storage/emulated/0/Android/data/'+transport.PACKAGE+'/files/.kodi/userdata/addon_data/'+ADDON,
                'Controlled profile canonical identity unavailable')
        require(ready.get('marker')==canonical_profile+'/unknown-native-write.txt','Controlled write escaped own profile')
        marker=transport.shell('cat',ready['marker']);report['actual_marker']=marker
        require(marker==CONTENTS,'Actual controlled write contents differ')
        transport.shell('test','-d','/proc/'+str(ready['child_pid']))
        before=transport.read_json(transport.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json')
        report['request']=transport.shell('am','start','-n',transport.PACKAGE+'/.InfinityPowerControlActivity','-a',transport.PACKAGE+'.action.CLOSE_KODI')
        deadline=time.monotonic()+35
        receipt={}
        while time.monotonic()<deadline:
            receipt=transport.read_json(transport.PRIVATE+'/files/infinity-checkpoint-close.json')
            if receipt.get('owner')==owner['owner'] and receipt.get('phase') in ('CHECKPOINT_FAILED','COMPLETE'):break
            time.sleep(.1)
        report['receipt']=receipt;report['after_processes']=transport.processes();save()
        verify_refusal(receipt,owner,report['after_processes'])
        after=transport.read_json(transport.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json')
        for bucket in ('items','watched','watchlist','collection','lists','sources','navigation_recovery'):
            require(before.get(bucket)==after.get(bucket),'Unsafe refusal changed protected records: '+bucket)
        report['protected_records_unchanged']=True;report['passed']=True;save();return report
    finally:save()
