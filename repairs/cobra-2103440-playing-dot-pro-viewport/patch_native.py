"""Retain working Cards Preview tap; Pro-only expanded portrait uses existing wide geometry.

Global Pro geometry, Pro Sports, playback and every shared/native library remain frozen.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repairs/cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods
APP='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
PRO='Lcom/projectinfinity/kodi/CobraProUi;'
TAP='synthetic lambda$cobraPreviewPanel$71$com-projectinfinity-kodi-InfinityLiveActivity(Landroid/view/View;)V'
ADJUST='private cobraAdjustProLayout(Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;)V'

def patch(raw):
    # Keep exactly the confirmed working440 tap; omit the unrelated emblem repair.
    import importlib.util
    spec=importlib.util.spec_from_file_location('preview440_patch',ROOT/'repairs/cobra-2103438-preview-restoration/patch_native.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    before=methods(raw);tap=methods(old.patch(raw))[TAP]
    raw=raw.replace(before[TAP],tap)
    adjust=before[ADJUST]
    anchor=f'    invoke-static {{v0, v1, v2, v3, v5}}, {PRO}->sportsGeometry(IIFIF)[[I\n\n    move-result-object v0'
    revised=f'''    # Only existing Pro on a genuine expanded portrait/near-square viewport.
    iget-boolean v6, p0, {APP}->mCobraProActive:Z
    if-eqz v6, :pro_original_geometry
    iget-boolean v6, p0, {APP}->mCobraProSportsActive:Z
    if-nez v6, :pro_original_geometry
    const/16 v6, 0x2bc
    if-lt v0, v6, :pro_original_geometry
    const/16 v6, 0x258
    if-lt v1, v6, :pro_original_geometry
    if-gt v0, v1, :pro_original_geometry
    invoke-static {{v0, v1, v2, v3}}, {PRO}->innerGeometry(IIFI)[[I
    move-result-object v0
    goto :pro_geometry_ready
    :pro_original_geometry
{anchor}
    :pro_geometry_ready'''
    assert adjust.count(anchor)==1
    raw=raw.replace(adjust,adjust.replace(anchor,revised))
    after=methods(raw)
    assert {k for k,v in before.items() if after[k]!=v}=={TAP,ADJUST}
    return raw

def patch_pro(raw):
    signature='static geometry(IIFI)[[I';body=methods(raw)[signature]
    # Exact existing landscape arrangement, using the real width and height.
    # Caller owns the Pro-only expanded-display guard; no dimensions are faked.
    check='    if-le v2, v3, :cond_2'
    assert body.count(check)==1
    clone=body.replace('.method '+signature,'.method static innerGeometry(IIFI)[[I',1).replace(check,'    nop',1)
    assert 'static innerGeometry(IIFI)[[I' not in methods(raw)
    return raw+'\n'+clone+'\n'
