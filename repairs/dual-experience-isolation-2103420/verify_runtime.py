"""Independent instruction-level preservation checks on repacked production DEX."""
import argparse
from pathlib import Path
import re
from inventory import APP,HERE,load,save,digest,file_sha
from prepare_runtime import methods,map_types

def compact(text):
    return '\n'.join(l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#'))

def check(work,baseline,out):
    originals={p.read_text().splitlines()[0].split()[-1]:p.read_text() for p in baseline.glob('*-smali/**/*.smali')}
    candidate={p.read_text().splitlines()[0].split()[-1]:p.read_text() for p in (work/'owner-dex').glob('*/part-*/**/*.smali')}
    report=load(work/'MODULE-BUILD.json');delta=load(work/'DELTA.json')
    old_methods=0;copied_methods=0;changed=[]
    aliases={'CobraJavaPersistence':'InfinityJavaPersistence','ShellJavaPersistence':'InfinityJavaPersistence',
             'CobraJavaWriteBarrier':'InfinityJavaWriteBarrier','ShellJavaWriteBarrier':'InfinityJavaWriteBarrier',
             'CobraBackgroundService':'InfinityExtendedBackgroundService','CobraBackgroundApiOutline':'CobraProUi$Hero$$ExternalSyntheticApiModelOutline1'}
    for name,old in originals.items():
        if name not in candidate:raise ValueError('Original class deleted')
        before=methods(old);raw_after=methods(candidate[name])
        after={map_types(s,aliases):body for s,body in raw_after.items()}
        if len(after)!=len(raw_after):raise ValueError('Type relocation merged overloads')
        extras=set(after)-set(before)
        allowed={'ownerLock()Ljava/lang/Object;','canBegin(Ljava/lang/String;)Z'} if name==APP+'InfinityJavaWriteBarrier;' else set()
        if extras!=allowed or not set(before)<=set(after):raise ValueError('Original method set changed: '+name)
        old_shape=old;new_shape=candidate[name]
        for body in before.values():old_shape=old_shape.replace(body,'')
        for body in after.values():new_shape=new_shape.replace(body,'')
        new_shape=map_types(new_shape,aliases)
        if name in (APP+'InfinityCobraDeviceBridge;',APP+'InfinityLiveActivity;'):new_shape=new_shape.replace('"cobra_player_rotation"','"infinity_player_rotation"')
        if name==APP+'Splash;':new_shape=new_shape.replace('.implements '+APP+'ExperienceChooserRefresh;','')
        if compact(old_shape)!=compact(new_shape):raise ValueError('Original fields/class metadata changed: '+name)
        for signature,prior in before.items():
            actual=after[signature]
            if actual==prior:old_methods+=1;continue
            revised=map_types(actual,aliases)
            revised=revised.replace(APP+'CobraPreferencePort;->preferences(',APP+'InfinityJavaPersistence;->preferences(')
            revised=revised.replace(APP+'ExperienceLaunchPreferences;->preferences(',APP+'InfinityJavaPersistence;->preferences(')
            revised=re.sub(re.escape(APP+'CombinedDurability;->')+r'(begin|sealIfReady|authorized|whileAuthorized|pending|cancel)(?=\()',
                           lambda m:APP+'InfinityJavaWriteBarrier;->'+m[1],revised)
            revised=revised.replace(APP+'CombinedDurability;->finishCoordinator(',APP+'InfinityJavaWriteBarrier;->whileAuthorized(')
            # Only these newly introduced boundary invocations may be removed.
            revised=re.sub(r'^\s*invoke-static \{p[01]\}, '+re.escape(APP)+
                r'(?:ContainerUpgrade;->beforeOwnerEntry\(Landroid/content/Context;\)V|CobraBackgroundSettings;->initialize\(Landroid/content/Context;\)V|CobraRefreshFiles;->directory\(Landroid/content/Context;\)Ljava/io/File;|CobraRuntimeLease;->(?:acquire|release)\(Ljava/lang/Object;\)V)\n',
                '',revised,flags=re.M)
            if name==APP+'CobraSportsReminderJob;':
                revised=re.sub(r'^\s*invoke-static \{v3\}, '+re.escape(APP)+r'CobraRuntimeLease;->release\(Ljava/lang/Object;\)V\n','',revised,flags=re.M)
            if name==APP+'InfinityStartupPreparation;' and signature.startswith('subscribe('):
                revised=revised.replace('    invoke-static {p1}, '+APP+'InfinityJavaPersistence;->userEntry(Landroid/content/Context;)V\n','')
            if name in (APP+'InfinityLiveActivity;',APP+'InfinityCobraDeviceBridge;'):
                revised=revised.replace('"cobra_player_rotation"','"infinity_player_rotation"')
            if name==APP+'InfinityCobraDeviceBridge;':revised=revised.replace('".cobra/refresh"','".kodi/userdata/addon_data/service.infinity.refresh"')
            if name==APP+'CobraPresentationSafety;':
                revised=revised.replace(APP+'ExperienceChooserRefresh;',APP+'Splash;')
                revised=revised.replace('invoke-interface {p0}, '+APP+'Splash;->cobraRefreshSafetyChooser()V',
                                        'invoke-virtual {p0}, '+APP+'Splash;->cobraRefreshSafetyChooser()V')
            if name==APP+'Splash;' and signature=='cobraRefreshSafetyChooser()V':
                revised=revised.replace('.method public cobraRefreshSafetyChooser()V','.method cobraRefreshSafetyChooser()V')
            if compact(revised)!=compact(prior):
                import difflib
                raise ValueError('Non-boundary instruction changed: '+name+'->'+signature+'\n'+'\n'.join(list(difflib.unified_diff(compact(prior).splitlines(),compact(revised).splitlines()))[:45]))
            old_methods+=1;changed.append({'class':name,'method':signature,'before':digest(prior.encode()),'after':digest(actual.encode())})
    for new,origin in delta['origins'].items():
        original_methods=methods(originals[origin]);actual_methods=methods(candidate[new])
        for signature,actual in actual_methods.items():
            if signature in ('ownerLock()Ljava/lang/Object;','canBegin(Ljava/lang/String;)Z'):continue
            restored_signature=map_types(signature,aliases)
            if restored_signature not in original_methods:raise ValueError('Copied method missing original: '+new+signature)
            revised=map_types(actual,aliases)
            revised=revised.replace('".cobra/refresh/runtime.properties"','".kodi/userdata/addon_data/service.infinity.refresh/runtime.properties"')
            if new.startswith(APP+'CobraBackgroundService'):
                revised=re.sub(r'(?<![0-9a-f])0x3ab([4-8])(?![0-9a-f])',r'0x2ab\1',revised)
                revised=revised.replace('com.projectinfinity.kodi.action.COBRA_','com.projectinfinity.kodi.action.')
                revised=re.sub(r'^\s*invoke-static \{p0\}, '+re.escape(APP)+r'CobraRuntimeLease;->(?:acquire|release)\(Ljava/lang/Object;\)V\n','',revised,flags=re.M)
                if signature=='preferences(Landroid/content/Context;)Landroid/content/SharedPreferences;':
                    expected='invoke-static {p0}, '+APP+'CobraBackgroundSettings;->preferences(Landroid/content/Context;)Landroid/content/SharedPreferences;'
                    if expected not in actual or len([l for l in actual.splitlines() if l.strip().startswith('invoke-')])!=1:
                        raise ValueError('Background preference delegation changed')
                    continue
            if compact(revised)!=compact(original_methods[restored_signature]):raise ValueError('Copied algorithm changed: '+new+signature)
            copied_methods+=1
    save(out,{'status':'EXACT_OR_EXPLICIT_BOUNDARY_INSTRUCTIONS_VERIFIED','original_methods_checked':old_methods,
              'copied_methods_checked':copied_methods,'explicit_original_method_deltas':changed,
              'untouched_class_definitions_exact':report['untouched_baseline_classes_verified'],
              'new_source_sha256':{p.name:file_sha(p) for p in (HERE/'runtime').glob('*.java')},
              'native_termination_callbacks_rewritten':False,'persistence_sync_readback_rollback_algorithms_rewritten':False})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('work','baseline','out'):p.add_argument('--'+n,type=Path,required=True)
    check(**vars(p.parse_args()))
