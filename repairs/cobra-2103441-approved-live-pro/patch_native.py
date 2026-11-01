"""Accepted438 managed Cobra methods plus retained working Preview tap.

No shared/JNI code. Cards LIVE eligibility reads the existing actual session.
"""
import importlib.util
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repairs/cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods
APP='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
CHANNEL=APP[:-1]+'$Channel;'
BINDING=APP[:-1]+'$CobraPlayerBinding;'
TAP='synthetic lambda$cobraPreviewPanel$71$com-projectinfinity-kodi-InfinityLiveActivity(Landroid/view/View;)V'
LIVE='private cobraCardsLivePulse('+CHANNEL+')Z'

def patch(raw):
    original=methods(raw)
    spec=importlib.util.spec_from_file_location('retained_preview440',ROOT/'repairs/cobra-2103438-preview-restoration/patch_native.py')
    prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
    raw=raw.replace(original[TAP],methods(prior.patch(raw))[TAP])
    assert LIVE not in original
    raw+='''
.method '''+LIVE+'''
    .registers 4
    const-string v0, "cards"
    iget-object v1, p0, '''+APP+'''->mCobraGuideStyle:Ljava/lang/String;
    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :static_live
    invoke-direct {p0, p1}, '''+APP+'''->cobraChannelActuallyPlaying('''+CHANNEL+''')Z
    move-result v0
    if-eqz v0, :static_live
    invoke-direct {p0}, '''+APP+'''->cobraPlayingIndicatorOwner()'''+BINDING+'''
    move-result-object v0
    if-eqz v0, :static_live
    iget-object v0, v0, '''+BINDING+'''->player:Landroidx/media3/exoplayer/ExoPlayer;
    if-eqz v0, :static_live
    invoke-interface {v0}, Landroidx/media3/exoplayer/ExoPlayer;->isPlaying()Z
    move-result v0
    return v0
    :static_live
    const/4 v0, 0x0
    return v0
.end method
'''
    after=methods(raw)
    assert {k for k,v in original.items() if after[k]!=v}=={TAP}
    assert after.keys()-original.keys()=={LIVE}
    return raw
