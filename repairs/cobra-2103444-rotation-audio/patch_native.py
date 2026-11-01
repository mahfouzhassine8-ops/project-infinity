"""Only exact signed444 Cobra method preimages; no shared/native/Infinity patch."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods
APP='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
SIX=APP[:-1]+'$CobraSix;'
BRIDGE='Lcom/projectinfinity/kodi/InfinityCobraDeviceBridge;'
ROT='Lcom/projectinfinity/kodi/CobraRotationPolicy;'
AUDIO='Lcom/projectinfinity/kodi/CobraFullscreenAudio;'

def replace(raw,sig,new):
 old=methods(raw)[sig]
 return raw.replace(old,new)

def patch_app(raw):
 sig='private cobraTogglePlayerRotation()V'
 old=methods(raw)[sig]
 # Preserve independent padlock, liveness checks and existing chrome visibility.
 start=old.index('    invoke-direct {p0}, '+APP+'->cobraPlayerRotationMode()I')
 end=old.index('    const-string v1, "button"',start)
 old=old[:start]+('    invoke-static {p0}, '+ROT+'->toggle(Landroid/app/Activity;)V\n\n')+old[end:]
 start=old.index('    if-ne v0, v2, :cond_2')
 end=old.index('    .line 11602',start)
 old=old[:start]+old[end:]
 raw=replace(raw,sig,old)
 sig='private cobraPlayerRotationDescription()Ljava/lang/String;'
 raw=replace(raw,sig,'.method '+sig+'\n    .registers 2\n    invoke-static {p0}, '+ROT+'->description(Landroid/app/Activity;)Ljava/lang/String;\n    move-result-object v0\n    return-object v0\n.end method')
 sig='private cobraRefreshCallControls()V';old=methods(raw)[sig]
 raw=replace(raw,sig,old.replace('    return-void','    invoke-static {p0}, '+AUDIO+'->refresh(Landroid/app/Activity;)V\n\n    return-void'))
 return raw

def patch_bridge(raw):
 sig='private applyRotation(Ljava/lang/String;)V';old=methods(raw)[sig]
 needle='    .line 171'
 hook='''    invoke-direct {p0}, '''+BRIDGE+'''->constrainedWindow()Z
    move-result v0
    iget-boolean v1, p0, '''+BRIDGE+'''->paused:Z
    or-int/2addr v0, v1
    iget-object v1, p0, '''+BRIDGE+'''->activity:Landroid/app/Activity;
    invoke-static {v1, v0}, '''+ROT+'''->apply(Landroid/app/Activity;Z)Z
    move-result v0
    if-eqz v0, :universal_original
    return-void
    :universal_original

'''
 assert old.count(needle)==1
 return replace(raw,sig,old.replace(needle,hook+needle))

def patch_six(raw):
 sig='controls(Landroid/widget/LinearLayout;I)Landroid/view/View;';old=methods(raw)[sig]
 # Add after native PiP/Stats composition so original callback objects and indices survive.
 hook='''    iget-object v0, p0, '''+SIX+'''->this$0:'''+APP+'''
    invoke-static {v0, p1}, '''+AUDIO+'''->insert(Landroid/app/Activity;Landroid/widget/LinearLayout;)V
'''
 # Non-Pro returns immediately; Pro has finished appending Stats before constructing scroll wrapper.
 needle='    return-object p1'
 # Initial !phone return intentionally remains native behavior; every Fold view uses phone path.
 assert old.count(needle)==2
 pos=old.rindex(needle);old=old[:pos]+hook+old[pos:]
 needle='    new-instance v0, Landroid/widget/HorizontalScrollView;'
 assert old.count(needle)==1;old=old.replace(needle,hook+needle)
 old=old.replace('const/16 v4, 0x48','const/16 v4, 0x30').replace('div-int/2addr p2, v1','div-int/lit8 p2, p2, 0x5')
 return replace(raw,sig,old)


def patch_binding(raw):
 sig='public synthetic onVolumeChanged(F)V';old=methods(raw)[sig]
 owner=raw.splitlines()[0].split()[-1]
 new=old.replace('.registers 2','.registers 3').replace('    return-void',
     '    iget-object v0, p0, '+owner+'->this$0:'+APP+'\n    invoke-static {v0}, '+AUDIO+'->refresh(Landroid/app/Activity;)V\n    return-void')
 return replace(raw,sig,new)
