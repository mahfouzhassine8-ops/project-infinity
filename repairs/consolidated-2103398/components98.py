"""Reviewed component overlay over the actual permanently signed 2103397 APK."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'fold-targeted-2103396'))
import components96 as previous
require,once,sha,digest=previous.require,previous.once,previous.sha,previous.digest
CC,UI,WB,SKIN,HEALTH=previous.CC,previous.UI,previous.WB,previous.SKIN,previous.HEALTH
LATEST='plugin.infinity.latestreleases'
PARENT='d4d39f51f9d4dbe4e666e245d18d9cf3aab901aeeb49df03ed47bbf6511cc63c'
COMMIT='51836289d1aa2d8fb7295a51894af8daec203a81'
PACKAGES=[(CC,'0.3.5.26','0.3.5.27'),(UI,'0.1.8','0.1.9'),(WB,'1.0.7','1.0.8'),
          (SKIN,'1.0.5.234','1.0.5.235'),(HEALTH,'2.5.23','2.5.24'),
          ('script.infinity.rails','0.2.7','0.2.7'),(LATEST,None,'0.1.0')]


def read_parent(apk):
    require(digest(apk)==PARENT,'actual signed 2103397 APK required')
    with ZipFile(apk) as z:
        require(len(z.namelist())==len(set(z.namelist())) and z.testzip() is None,'invalid parent ZIP')
        return {n[14:]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and not n.endswith('/') and n.split('/')[2] in {a for a,_,_ in PACKAGES}}


def xml(root):return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def home(raw):
    root=ET.fromstring(raw)
    # Only the two exact existing feed sources and their View All routes change.
    # All control positions, visibility, limits, ordering and navigation stay.
    for node in root.iter():
        if not node.text:continue
        text=node.text
        for section,selector in [('movies','action=movies'),('tvshows','action=tvshows')]:
            if 'plugin://plugin.video.umbrella/' not in text or selector not in text:continue
            if (section=='movies' and '5308818' not in text) or (section=='tvshows' and 'url=trakttrending_recent' not in text):continue
            start=text.index('plugin://plugin.video.umbrella/')
            reload=text.find('&reload=',start)
            end=reload if reload>=0 else len(text)
            if reload<0:
                # Builtin SetProperty wrappers end with ",Home)"; content does not.
                suffix=text.find(',Home)',start)
                if suffix>=0:end=suffix
            text=text[:start]+'plugin://plugin.infinity.latestreleases/?action=feed&section='+section+text[end:]
        node.text=text
    # The old ambient layer precedes the opaque layout backgrounds and is
    # overpainted. Move only this existing edge-mask layer above those backgrounds
    # and below the drawer/header. Its no-media visibility remains unchanged.
    controls=root.find('controls')
    backdrop=next((n for n in controls if n.tag=='include' and n.get('content')=='InfinityExperienceBackdrop'),None)
    if backdrop is not None:
        owner=controls.find('control[@id="40001"]')
        require(owner is not None,'Home composition owner absent')
        controls.remove(backdrop);controls.insert(list(controls).index(owner)+1,backdrop)
    return xml(root)


def popup(raw):
    root=ET.fromstring(raw)
    for ident,font in [(120,'InfinityOptionBTitle'),(121,'InfinityOptionBMeta'),(122,'InfinityOptionBMeta'),(123,'InfinityOptionBMeta'),(124,'InfinityOptionBMeta'),(125,'InfinityOptionBMeta'),(126,'InfinityOptionBText'),(101,'InfinityOptionBAction'),(102,'InfinityOptionBAction'),(103,'InfinityOptionBAction'),(104,'InfinityOptionBAction')]:
        root.find('.//control[@id="%d"]/font'%ident).text=font
    close=root.find('.//control[@id="9"]');close.find('label').text=''
    for tag in ('texturefocus','texturenofocus'):
        close.find(tag).set('colordiffuse','$VAR[InfinityLegacyField]')
    image=ET.SubElement(root.find('.//control[@id="100"]'),'control',{'type':'image','id':'113'})
    ET.SubElement(image,'aspectratio').text='keep'
    ET.SubElement(image,'texture',{'colordiffuse':'$VAR[InfinityLegacyText]'}).text='infinity_ui/icons/close.png'
    body=root.find('.//control[@id="126"]')
    for tag,value in [('onup','9'),('ondown','104'),('onright','104'),('autoscroll','0')]:
        n=body.find(tag)
        if n is None:n=ET.SubElement(body,tag)
        n.text=value
    ET.SubElement(body,'pagecontrol').text='128'
    bar=ET.SubElement(root.find('.//control[@id="100"]'),'control',{'type':'scrollbar','id':'128'})
    for tag,value in [('visible','String.IsEqual(Window.Property(Infinity.HomeOptionB.Expanded),true)'),('showonepage','true'),('onleft','104'),('onright','104'),('onup','128'),('ondown','128')]:ET.SubElement(bar,tag).text=value
    for tag,color in [('texturesliderbackground','InfinityLegacyField'),('texturesliderbar','InfinityLegacyTrack'),('texturesliderbarfocus','InfinityLegacyAccent')]:ET.SubElement(bar,tag,{'border':'6','colordiffuse':'$VAR['+color+']'}).text='infinity_legacy/track.png'
    return xml(root)


def fonts(raw):
    root=ET.fromstring(raw)
    for fontset in root.findall('fontset'):
        for name,size,bold in [('InfinityOptionBTitle',34,True),('InfinityOptionBMeta',22,False),('InfinityOptionBText',28,False),('InfinityOptionBAction',22,False)]:
            f=ET.SubElement(fontset,'font');ET.SubElement(f,'name').text=name
            ET.SubElement(f,'filename').text='Roboto-Regular.ttf';ET.SubElement(f,'size').text=str(size)
            if bold:ET.SubElement(f,'style').text='bold'
    return xml(root)


def components(before):
    after=dict(before)
    for leaf in ('default.py','identity.py','addon.xml'):
        after[LATEST+'/'+leaf]=(HERE/LATEST/leaf).read_bytes()
    after[UI+'/latest_identity.py']=(HERE/LATEST/'identity.py').read_bytes()
    runtime=(HERE/'home_option_b.py').read_bytes()
    runtime=once(runtime,b"for ident,key in ((110,'surface'),(111,'surface'),(9,'close')):",b"for ident,key in ((110,'surface'),(111,'surface'),(9,'close'),(113,'close')):")
    after[UI+'/home_option_b.py']=runtime
    popup_key=UI+'/resources/skins/Default/1080i/InfinityHomeOptionB.xml'
    after[popup_key]=popup(before[popup_key]);after[SKIN+'/unified/InfinityHomeOptionB.xml']=after[popup_key]
    for name,body in before.items():
        if name.startswith(SKIN+'/') and name.endswith('/Home.xml'):after[name]=home(body)
        if name.startswith(SKIN+'/') and name.endswith('/Font.xml'):after[name]=fonts(body)
    # CC already stops its experience observer on checkpoint; retain ownership.
    # Publish independent applied-input/lifecycle facts, never certify pixels.
    key=CC+'/experience.py'
    after[key]=once(before[key],b"self.publish('AmbientHome.SubmittedMode', ambient if submitted else 'off')",b"self.publish('AmbientHome.SubmittedMode', ambient if submitted else 'off')\n                self.publish('AmbientHome.RenderInputReady', 'true' if submitted else 'false')")
    after[CC+'/checkpoint_runtime.py']=once(before[CC+'/checkpoint_runtime.py'],b'ADDON_VERSION = "0.3.5.26"',b'ADDON_VERSION = "0.3.5.27"')
    after[WB+'/controller.py']=once(before[WB+'/controller.py'],b'"0.3.5.26"',b'"0.3.5.27"')
    # Health recorder output is optional. Do not begin a fresh diagnostic write
    # after the native cooperative abort; existing buffers remain observer-owned.
    key=HEALTH+'/khc_kodi.py';raw=before[key]
    raw=once(raw,b"        store.event('observer_error', {'type': type(error).__name__})",b"        if not monitor.abortRequested():\n            store.event('observer_error', {'type': type(error).__name__})")
    raw=once(raw,b"        if healthy_abort:\n            store.finish(",b"        if healthy_abort and not monitor.abortRequested():\n            store.finish(")
    marker=b"    return result\n\n\ndef native_roots()"
    raw=once(raw,marker,b"    from khc_close_attempts import collect as close_attempt_history\n    result['close_attempts'] = close_attempt_history(xbmcvfs.translatePath('special://profile/addon_data/script.infinity.commandcenter/.android-checkpoint'))\n"+marker)
    after[key]=raw
    after[HEALTH+'/khc_close_attempts.py']=(HERE/'khc_close_attempts.py').read_bytes()
    identity_key=HEALTH+'/infinity_runtime_identity.py'
    after[identity_key]=before[identity_key].replace(b"'service.infinity.compat')",b"'service.infinity.compat','plugin.infinity.latestreleases')").replace(b"   if aid=='script.infinity.uirepair':",b"   if aid=='plugin.infinity.latestreleases':names.update(('default.py','identity.py'))\n   if aid=='script.infinity.uirepair':").replace(b"('home_option_b.py','runtime.py'",b"('home_option_b.py','latest_identity.py','runtime.py'")
    # Keep incident categories separate; a recovered freeze is not a fatal crash.
    key=HEALTH+'/khc_causal.py';raw=before[key]
    raw=once(raw,b"(('segv', 'fatal_signal', 'native_crash'), 'native'),",b"(('freeze_recovered',), 'ui'),\n        (('segv', 'fatal_signal', 'native_crash'), 'native'),")
    raw=once(raw,b"    return dict(category=category,",b"    classification = ('recovered_ui_freeze' if operation == 'internal_native_ui_freeze_recovered' else\n                      'essential_checkpoint_failed' if operation in ('CHECKPOINT_FAILED', 'checkpoint.failed') else\n                      'engine_termination_observed' if operation in ('engine.death', 'exit.engineDeath') else\n                      'whole_package_termination_unverified')\n    return dict(classification=classification, category=category,")
    after[key]=raw
    for addon,old,new in PACKAGES:
        if old and old!=new:after[addon+'/addon.xml']=once(after[addon+'/addon.xml'],('version="'+old+'"').encode(),('version="'+new+'"').encode())
    pins={n.split('/',1)[1]:sha(b) for n,b in after.items() if n.startswith(CC+'/') and (n.endswith('.py') or n.endswith('/addon.xml') or n==CC+'/resources/settings.xml')}
    require(len(pins)==17,'controller source inventory changed')
    for addon in (UI,WB):after[addon+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
    for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
        key=SKIN+'/'+leaf;data=json.loads(after[key]);data.update(candidate=235,skin_version='1.0.5.235',candidate_locked=False)
        for field in ('version','candidate_version'):
            if field in data:data[field]='1.0.5.235'
        if 'protected_files' in data:data['protected_files']={p:sha(after[SKIN+'/'+p]) for p in data['protected_files']}
        after[key]=(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
    for n,b in list(after.items()):
        if n.startswith(HEALTH+'/') and n.endswith('.py'):
            after[n]=b=b.replace(b'2.5.23',b'2.5.24')
        if n.endswith('.py'):ast.parse(b.decode(),filename=n)
        if n.endswith('.xml'):ET.fromstring(b)
    return after


def evidence_manifest(after):
    # Same production collector contract, extended with the separately owned feed.
    result=json.loads(previous.evidence_manifest(after))
    return (json.dumps(result,indent=2,sort_keys=True)+'\n').encode()


def ledger(before,after):
    changed={n:{'before':sha(before[n]) if n in before else None,'after':sha(after[n])} for n in sorted(after) if before.get(n)!=after[n]}
    require(not any('cobra' in n.lower() for n in changed),'Cobra source change forbidden')
    require(all(before[n]==after[n] for n in before if n.startswith('script.infinity.rails/')),'Rails changed')
    return dict(parent_apk_sha256=PARENT,parent_source_commit=COMMIT,versions={a:v for a,_,v in PACKAGES},changed=changed,removed=sorted(set(before)-set(after)),cobra_changed=False,physical_fold_verified=False,final_lock=False)


def stage(apk,out):
    before=read_parent(apk);after=components(before);require(not out.exists(),'stage exists')
    for n,b in after.items():p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return ledger(before,after)

if __name__=='__main__':print(json.dumps(stage(Path(sys.argv[1]),Path(sys.argv[2])),indent=2,sort_keys=True))
