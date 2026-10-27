"""Produce reviewed source/DEX module deltas from exact shipped definitions.

No source template is assumed to match the APK. Production persistence and
background copies originate in the verified signed DEX, not old Java overlays.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from inventory import APP, APK_SHA, HERE, ROOT, digest, file_sha, load, save

COBRA_ROOTS = {
    'InfinityLiveActivity','InfinityCobraBootReceiver','InfinityCobraDeviceBridge',
    'InfinityCobraDiagnostics','InfinityCobraFeatureRuntime','InfinityCobraRecordingService',
    'InfinityCobraReminderReceiver','CobraSportsReminderJob','CobraSportsPreferences',
    'CobraDiagnosticArchive','CobraEmbeddedCrop','CobraEmblem','CobraImmersiveAmbient',
    'CobraNetworkIntelligence','CobraPresentationEffects','CobraPresentationSafety',
    'CobraProUi','CobraQuickPeekSession','CobraSmartReturn','CobraVisualCatalog',
    'CobraVisualGeometry','CobraVisualRenderer','CobraVisualScene','CobraVisualTheme'
}
SHELL_ROOTS = {'Splash','InfinityAskEveryTimeActivity',
               'InfinityGlassChooser','InfinityGlassHealth','InfinityGlassOptions',
               'InfinityGlassRecovery','InfinityGlassArt','InfinityCosmicArt',
               }
COORDINATORS = {'InfinityCloseGuardService','InfinityCloseNativeLease'}
PERSISTENCE = ('InfinityJavaPersistence','InfinityJavaWriteBarrier')
SERVICE = 'InfinityExtendedBackgroundService'
METHOD = re.compile(r'^\.method ([^\n]+)\n.*?^\.end method\s*$', re.M|re.S)


def methods(text):
    return {m[1].split()[-1]:m[0] for m in METHOD.finditer(text)}


def map_types(text, mapping):
    for old,new in sorted(mapping.items(),key=lambda x:-len(x[0])):
        text=re.sub(re.escape(APP+old)+r'(?=[$;])',lambda _:APP+new,text)
    return text


def replace_method(text, signature, replacement):
    prior=methods(text)[signature]
    if text.count(prior)!=1:raise ValueError('Ambiguous method')
    return text.replace(prior,replacement.rstrip()+'\n\n')


def entry(text,signature,instruction):
    prior=methods(text)[signature]
    changed=re.sub(r'(\n    \.registers [0-9]+\n)',lambda m:m[0]+'\n    '+instruction+'\n',prior,count=1)
    if changed==prior:raise ValueError('No method register declaration')
    return replace_method(text,signature,changed)


def normal_exit(text,signature,instruction):
    prior=methods(text)[signature]
    if '    return-void' not in prior:raise ValueError('Missing void return')
    return replace_method(text,signature,prior.replace('    return-void','    '+instruction+'\n\n    return-void'))


def barrier_accessors(name):
    c=APP+name+';'
    return f'''\n.method public static ownerLock()Ljava/lang/Object;
    .registers 1
    sget-object v0, {c}->LOCK:Ljava/lang/Object;
    return-object v0
.end method

.method public static canBegin(Ljava/lang/String;)Z
    .registers 2
    sget-boolean v0, {c}->closing:Z
    if-eqz v0, :allowed
    sget-object v0, {c}->session:Ljava/lang/String;
    invoke-virtual {{v0, p0}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    return v0
    :allowed
    const/4 v0, 0x1
    return v0
.end method
'''


def wiring():
    ports=[]
    for name in ('InfinityJavaWriteBarrier','CobraJavaWriteBarrier','ShellJavaWriteBarrier'):
        ports.append('''new CombinedDurability.Port() {
          public Object lock(){return BARRIER.ownerLock();}
          public boolean canBegin(String t){return BARRIER.canBegin(t);}
          public boolean begin(String t){return BARRIER.begin(t);}
          public String sealIfReady(String t){return BARRIER.sealIfReady(t);}
          public boolean authorized(String t,String p){return BARRIER.authorized(t,p);}
          public String pending(){return BARRIER.pending();}
          public void cancel(String t){BARRIER.cancel(t);}
        }'''.replace('BARRIER',name))
    return '''package com.projectinfinity.kodi;
final class OwnerDurabilityWiring {
  static CombinedDurability.Group create() {
    return new CombinedDurability.Group('''+',\n'.join(ports)+''',new CombinedDurability.Retention() {
      public Object lock(){return CobraRuntimeLease.ownerLock();}
      public boolean active(){return CobraRuntimeLease.active();}
    });
  }
}
'''


def prepare(smali,out):
    smali,out=Path(smali),Path(out)
    if out.exists():raise ValueError('Fresh output required')
    baseline=load(HERE/'evidence/DEX-MEMBERS.json.gz')
    source={}
    for p in smali.glob('*-smali/**/*.smali'):
        text=p.read_text();name=text.splitlines()[0].split()[-1]
        if name not in baseline or digest(text.encode())!=baseline[name]['sha256']:
            raise ValueError('Unverified baseline definition: '+name)
        source[name]=text
    if set(source)!=set(baseline):raise ValueError('Incomplete source baseline')
    out.mkdir(parents=True)
    transformed=dict(source); origins={}; deltas={}
    for descriptor,text in source.items():
        if not descriptor.startswith(APP):continue
        short=descriptor[len(APP):-1];root=short.split('$')[0]
        mapping={}
        if root in COBRA_ROOTS and 'ExternalSyntheticApiModelOutline' not in short:
            mapping.update({n:n.replace('Infinity','Cobra',1) for n in PERSISTENCE})
            mapping[SERVICE]='CobraBackgroundService'
        elif root in SHELL_ROOTS:
            mapping.update({n:n.replace('Infinity','Shell',1) for n in PERSISTENCE})
        revised=map_types(text,mapping)
        if root in ('InfinityLiveActivity','InfinityCobraDeviceBridge'):
            revised=revised.replace('"infinity_player_rotation"','"cobra_player_rotation"')
        if short=='InfinityCobraDeviceBridge':
            revised=revised.replace('".kodi/userdata/addon_data/service.infinity.refresh"','".cobra/refresh"')
            revised=entry(revised,'<init>(Landroid/app/Activity;'+APP+'InfinityCobraDeviceBridge$PlaybackOwner;)V',
                          'invoke-static {p1}, '+APP+'CobraRefreshFiles;->directory(Landroid/content/Context;)Ljava/io/File;')
        if root in SHELL_ROOTS:
            for signature,body in list(methods(revised).items()):
                if '"infinity_cobra_live"' in body:
                    # The enumerated appearance readers each have one store.
                    token=APP+'ShellJavaPersistence;->preferences('
                    if body.count(token)!=1:raise ValueError('Ambiguous chooser store '+signature)
                    revised=replace_method(revised,signature,body.replace(token,APP+'CobraPreferencePort;->preferences('))
        if root=='InfinityLiveActivity':
            for signature,body in list(methods(revised).items()):
                if '"infinity_experience"' in body:
                    token=APP+'CobraJavaPersistence;->preferences('
                    if body.count(token)!=1:raise ValueError('Ambiguous launch preference '+signature)
                    revised=replace_method(revised,signature,body.replace(token,APP+'ExperienceLaunchPreferences;->preferences('))
        if short=='CobraPresentationSafety':
            revised=map_types(revised,{'Splash':'ExperienceChooserRefresh'})
            revised=revised.replace('invoke-virtual {p0}, '+APP+'ExperienceChooserRefresh;->cobraRefreshSafetyChooser()V',
                                    'invoke-interface {p0}, '+APP+'ExperienceChooserRefresh;->cobraRefreshSafetyChooser()V')
        if short=='Splash':
            revised=revised.replace('.super Landroid/app/Activity;',
                                    '.super Landroid/app/Activity;\n.implements '+APP+'ExperienceChooserRefresh;')
            revised=revised.replace('.method cobraRefreshSafetyChooser()V','.method public cobraRefreshSafetyChooser()V')
        if short=='InfinityStartupPreparation':
            revised=entry(revised,'subscribe(Landroid/content/Context;'+APP+'InfinityStartupTrace;'+APP+'InfinityStartupPreparation$Callback;)'+APP+'InfinityStartupPreparation$Ticket;',
                          'invoke-static {p1}, '+APP+'InfinityJavaPersistence;->userEntry(Landroid/content/Context;)V')
        if root in COORDINATORS:
            # Only the coordinator's existing static protocol calls change.
            # Native authorization, receipts, task retirement and kills remain.
            revised=re.sub(re.escape(APP+'InfinityJavaWriteBarrier;->')+r'(begin|sealIfReady|authorized|whileAuthorized|pending|cancel)(?=\()',
                           lambda m:APP+'CombinedDurability;->'+m[1],revised)
        if short=='InfinityCloseGuardService':
            # Existing verified engine-death and owner-retirement boundary.
            signature='finishCoordinatorProcess('+APP+'InfinityCloseGuardService$Session;)V'
            prior=methods(revised)[signature]
            revised=replace_method(revised,signature,prior.replace('CombinedDurability;->whileAuthorized(',
                                                                  'CombinedDurability;->finishCoordinator('))
        if short=='InfinityJavaWriteBarrier':revised+=barrier_accessors(short)
        if short in ('Splash','Main','InfinityLiveActivity'):
            hook='CobraBackgroundSettings;->initialize' if short=='InfinityLiveActivity' else 'ContainerUpgrade;->beforeOwnerEntry'
            revised=entry(revised,'onCreate(Landroid/os/Bundle;)V',
                          'invoke-static {p0}, '+APP+hook+'(Landroid/content/Context;)V')
        if short in ('InfinityLiveActivity','InfinityCobraRecordingService'):
            create='onCreate(Landroid/os/Bundle;)V' if short=='InfinityLiveActivity' else 'onCreate()V'
            revised=entry(revised,create,
                          'invoke-static {p0}, '+APP+'CobraRuntimeLease;->acquire(Ljava/lang/Object;)V')
            revised=normal_exit(revised,'onDestroy()V','invoke-static {p0}, '+APP+'CobraRuntimeLease;->release(Ljava/lang/Object;)V')
        if short=='CobraSportsReminderJob':
            revised=entry(revised,'onStartJob(Landroid/app/job/JobParameters;)Z',
                          'invoke-static {p1}, '+APP+'CobraRuntimeLease;->acquire(Ljava/lang/Object;)V')
            signature='lambda$onStartJob$0$com-projectinfinity-kodi-CobraSportsReminderJob(ILandroid/app/job/JobParameters;)V'
            prior=methods(revised)[signature]
            # The exact shipped worker saves its JobParameters in v3 and
            # exits through one normal return or its final catch-all throw.
            final_throw='    :cond_13\n    throw v0\n.end method'
            if prior.count('    return-void')!=1 or prior.count(final_throw)!=1:
                raise ValueError('Reminder worker exit contract changed')
            release='    invoke-static {v3}, '+APP+'CobraRuntimeLease;->release(Ljava/lang/Object;)V\n\n'
            revised=replace_method(revised,signature,prior.replace('    return-void',release+'    return-void').replace(final_throw,'    :cond_13\n'+release+'    throw v0\n.end method'))
        if short in ('InfinityCobraBootReceiver','InfinityCobraReminderReceiver'):
            signature='onReceive(Landroid/content/Context;Landroid/content/Intent;)V'
            prior=methods(revised)[signature]
            if re.search(r'^\s*(?:move-result-object|move-object(?:/\w+)?|new-instance|const-[\w/]+) p0',prior,re.M):
                raise ValueError('Receiver overwrites retention identity')
            revised=entry(revised,signature,'invoke-static {p0}, '+APP+'CobraRuntimeLease;->acquire(Ljava/lang/Object;)V')
            revised=normal_exit(revised,signature,'invoke-static {p0}, '+APP+'CobraRuntimeLease;->release(Ljava/lang/Object;)V')
        if short==SERVICE:
            revised=entry(revised,'setEnabled(Landroid/app/Activity;Z)Z',
                          'invoke-static {p0}, '+APP+'ContainerUpgrade;->beforeOwnerEntry(Landroid/content/Context;)V')
            revised=entry(revised,'onCreate()V',
                          'invoke-static {p0}, '+APP+'ContainerUpgrade;->beforeOwnerEntry(Landroid/content/Context;)V')
        transformed[descriptor]=revised
    # Clone the original, byte-grounded persistence algorithms and all nested
    # types. No sync, rollback, readback or failed-write branch is removed.
    for owner in ('Cobra','Shell'):
        mapping={n:n.replace('Infinity',owner,1) for n in PERSISTENCE}
        for descriptor,text in source.items():
            short=descriptor.removeprefix(APP).removesuffix(';');root=short.split('$')[0]
            if root not in PERSISTENCE or not descriptor.startswith(APP):continue
            new=map_types(descriptor,mapping);revised=map_types(text,mapping)
            if owner=='Cobra' and short=='InfinityJavaPersistence':
                # Keep the original diagnostic classification safeguards,
                # including hard-link/canonical-path checks, at Cobra's path.
                revised=revised.replace('".kodi/userdata/addon_data/service.infinity.refresh/runtime.properties"',
                                        '".cobra/refresh/runtime.properties"')
            if short=='InfinityJavaWriteBarrier':revised+=barrier_accessors(mapping[short])
            transformed[new]=revised;origins[new]=descriptor
    # Cobra's complete existing background implementation, in its activity's
    # existing process. Original Infinity component/process remains intact.
    mapping={SERVICE:'CobraBackgroundService',**{n:n.replace('Infinity','Cobra',1) for n in PERSISTENCE},
             'CobraProUi$Hero$$ExternalSyntheticApiModelOutline1':'CobraBackgroundApiOutline'}
    for descriptor,text in source.items():
        short=descriptor.removeprefix(APP).removesuffix(';')
        if short.split('$')[0]!=SERVICE:continue
        new=map_types(descriptor,mapping);revised=map_types(text,mapping)
        revised=re.sub(r'(?<![0-9a-f])0x2ab([4-8])(?![0-9a-f])',r'0x3ab\1',revised)
        for action in ('DISABLE_EXTENDED_BACKGROUND','MINI_MEDIA_COMMAND','MINI_BACKGROUND_START','MINI_BACKGROUND_STOP'):
            revised=revised.replace('com.projectinfinity.kodi.action.'+action,'com.projectinfinity.kodi.action.COBRA_'+action)
        if short==SERVICE:
            signature='preferences(Landroid/content/Context;)Landroid/content/SharedPreferences;'
            revised=replace_method(revised,signature,f'''.method private static {signature}
    .registers 1
    invoke-static {{p0}}, {APP}CobraBackgroundSettings;->preferences(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object p0
    return-object p0
.end method''')
            revised=entry(revised,'onCreate()V','invoke-static {p0}, '+APP+'CobraRuntimeLease;->acquire(Ljava/lang/Object;)V')
            revised=normal_exit(revised,'onDestroy()V','invoke-static {p0}, '+APP+'CobraRuntimeLease;->release(Ljava/lang/Object;)V')
        transformed[new]=revised;origins[new]=descriptor
    outline=APP+'CobraProUi$Hero$$ExternalSyntheticApiModelOutline1;'
    new=APP+'CobraBackgroundApiOutline;'
    transformed[new]=map_types(source[outline],mapping);origins[new]=outline
    # Keep only OS adapter methods referenced by Cobra's copied service. The
    # original shared compiler outline also contains unrelated Infinity APIs.
    needed=set()
    for descriptor,text in transformed.items():
        if descriptor.startswith(APP+'CobraBackgroundService'):
            needed.update(re.findall(re.escape(new)+r'->([^\s,{}]+)',text))
    needed.update(n for n in methods(transformed[new]) if n.startswith(('<init>','<clinit>')))
    for signature,body in list(methods(transformed[new]).items()):
        if signature not in needed:transformed[new]=transformed[new].replace(body,'')
    changed=out/'changed-smali';changed.mkdir()
    for descriptor,text in transformed.items():
        if source.get(descriptor)==text:continue
        p=changed/(descriptor[1:-1]+'.smali');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        old=source.get(descriptor,source.get(origins.get(descriptor,''),''))
        before,after=methods(old),methods(text)
        deltas[descriptor]={'origin':origins.get(descriptor,descriptor),'before':digest(old.encode()),'after':digest(text.encode()),
                           'changed_methods':[n for n in sorted(set(before)|set(after)) if before.get(n)!=after.get(n)]}
    java=out/'java/com/projectinfinity/kodi';java.mkdir(parents=True)
    for p in (HERE/'runtime').glob('*.java'):shutil.copyfile(p,java/p.name)
    (java/'OwnerDurabilityWiring.java').write_text(wiring())
    save(out/'DELTA.json',{'baseline_apk_sha256':APK_SHA,'classes':deltas,'origins':origins,
                         'unchanged_classes':len(source)-sum(n in source for n in deltas)})
    return {'changed_existing':sum(n in source for n in deltas),'cloned_classes':len(origins)}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--smali',required=True,type=Path);parser.add_argument('--out',required=True,type=Path)
    print(json.dumps(prepare(**vars(parser.parse_args())),indent=2))
