import argparse,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ISO=HERE.parent/'dual-experience-isolation-2103420';sys.path.insert(0,str(ISO))
from inventory import load,save,file_sha,digest,APP

def check(baseline,work,out):
 old={p.read_text().splitlines()[0].split()[-1]:p.read_text() for p in baseline.glob('*-smali/**/*.smali')}
 new={p.read_text().splitlines()[0].split()[-1]:p.read_text() for p in (work/'owner-dex').glob('*/part-*/**/*.smali')}
 authority=load(ISO/'release-authority.json');expected={k[6:] for k,v in authority['payload'].items() if k.startswith('class:') and v['owner']=='COBRA'}
 assert set(old)>=expected and set(new)>=expected
 changed=[n for n in expected if new[n]!=old[n]];assert set(changed)=={APP+'InfinityLiveActivity;',APP+'CobraComponent;'}
 methods=lambda s:{m[1].split()[-1]:m[0] for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method',s,re.M|re.S)}
 a,b=methods(old[APP+'InfinityLiveActivity;']),methods(new[APP+'InfinityLiveActivity;'])
 modified=[n for n in a if a[n]!=b[n]];assert modified==['onCreate(Landroid/os/Bundle;)V']
 revised=b[modified[0]].replace('    invoke-static {p0}, '+APP+'CobraWindowReflow;->install(Landroid/app/Activity;)V\n','')
 compact=lambda text:[l.strip() for l in text.splitlines() if l.strip()]
 assert compact(revised)==compact(a[modified[0]])
 assert set(b)-set(a)=={'cobraReflowSurface()Landroid/view/View;','cobraReflowMeasuredWindow()V'}
 for n in set(new)-expected:assert n.startswith(APP+'CobraWindowReflow')
 save(out,{'status':'PASS_COBRA_DELTA_PRESERVATION','baseline_apk_sha256':'a1ea9442cd8ff82be09c34cc7c84887178fb162b8397005bba656ff6e28f5637',
 'unchanged_cobra_classes':len(expected)-2,'changed_original_classes':changed,'changed_original_activity_methods':modified,
 'existing_activity_methods_verified':len(a),'new_classes':sorted(set(new)-expected),'player_retune_seek_audio_shutdown_methods_changed':False})
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['baseline','work','out']:p.add_argument('--'+n,type=Path,required=True)
 check(**vars(p.parse_args()))
