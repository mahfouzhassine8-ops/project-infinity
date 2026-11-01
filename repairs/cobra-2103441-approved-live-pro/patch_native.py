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
ADJUST='private cobraAdjustProLayout(Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;)V'
RENDER='private cobraRenderFocusMode(Landroid/widget/LinearLayout;Ljava/util/ArrayList;)V'
RESTORE='private cobraRestoreModeScroll()V'
EXPANDED='Lcom/projectinfinity/kodi/CobraProExpandedLayout;'

def patch_row(raw):
    original=methods(raw)
    layout='protected onLayout(ZIIII)V'
    anchor='    :goto_0\n    add-int v9, v3, v4'
    assert original[layout].count(anchor)==1
    changed=original[layout].replace(anchor,'    :goto_0\n    invoke-static {v0, v7}, '+EXPANDED+'->rowWide(Landroid/view/View;Z)Z\n\n    move-result v7\n\n    add-int v9, v3, v4')
    raw=raw.replace(original[layout],changed)
    measure='protected onMeasure(II)V'
    anchor='    invoke-virtual {p0, p1, p2}, Lcom/projectinfinity/kodi/CobraProUi$ChannelRow;->setMeasuredDimension(II)V'
    assert original[measure].count(anchor)==1
    changed=original[measure].replace(anchor,'    invoke-static {p0, p2}, '+EXPANDED+'->rowHeight(Landroid/view/View;I)I\n\n    move-result p2\n\n'+anchor)
    raw=raw.replace(original[measure],changed)
    assert {k for k,v in original.items() if methods(raw)[k]!=v}=={layout,measure}
    return raw

def patch(raw):
    original=methods(raw)
    spec=importlib.util.spec_from_file_location('retained_preview440',ROOT/'repairs/cobra-2103438-preview-restoration/patch_native.py')
    prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
    raw=raw.replace(original[TAP],methods(prior.patch(raw))[TAP])
    anchor='    invoke-static {v0, v1, v2, v3, v5}, Lcom/projectinfinity/kodi/CobraProUi;->sportsGeometry(IIFIF)[[I\n\n    move-result-object v0'
    assert original[ADJUST].count(anchor)==1
    adjust=original[ADJUST].replace(anchor,anchor+'\n\n    invoke-static {p0, v0, p1}, '+EXPANDED+'->layout(Landroid/app/Activity;[[ILjava/lang/Object;)[[I\n\n    move-result-object v0')
    raw=raw.replace(original[ADJUST],adjust)
    anchor='    invoke-virtual {v0, v2}, Landroid/widget/ListView;->setClipToPadding(Z)V'
    assert original[RENDER].count(anchor)==1
    render=original[RENDER].replace(anchor,anchor+'\n\n    invoke-static {p0}, '+EXPANDED+'->sync(Landroid/app/Activity;)V')
    raw=raw.replace(original[RENDER],render)
    anchor='    invoke-virtual {v2, v1}, Landroid/widget/AbsListView;->setSelection(I)V'
    assert original[RESTORE].count(anchor)==1
    restore=original[RESTORE].replace(anchor,'    aget v0, v0, v3\n\n    invoke-static {v2, v1, v0}, '+EXPANDED+'->restoreSelection(Landroid/widget/AbsListView;II)V')
    raw=raw.replace(original[RESTORE],restore)
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
    assert {k for k,v in original.items() if after[k]!=v}=={TAP,ADJUST,RENDER,RESTORE}
    assert after.keys()-original.keys()=={LIVE}
    return raw
