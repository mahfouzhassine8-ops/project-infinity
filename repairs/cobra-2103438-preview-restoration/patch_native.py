"""Two Cards-preview-only methods in the COBRA-owned Activity. No JNI/shared changes."""
import sys,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repairs/cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods
TAP='synthetic lambda$cobraPreviewPanel$71$com-projectinfinity-kodi-InfinityLiveActivity(Landroid/view/View;)V'
PULSE='private cobraVisualPulseState(Landroidx/media3/exoplayer/ExoPlayer;)Lcom/projectinfinity/kodi/CobraPresentationEffects$PulseState;'
APP='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
STATE='Lcom/projectinfinity/kodi/CobraPresentationEffects$PulseState;'
def patch(raw):
    original=methods(raw);tap=original[TAP]
    assert tap.count('.registers 2')==1
    branch=f'''
    const-string v0, "cards"
    iget-object v1, p0, {APP}->mCobraGuideStyle:Ljava/lang/String;
    invoke-virtual {{v0, v1}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :preview_legacy_tap
    iget-boolean v0, p0, {APP}->mCobraProActive:Z
    if-nez v0, :preview_legacy_tap
    iget-boolean v0, p0, {APP}->mCobraProSportsActive:Z
    if-nez v0, :preview_legacy_tap
    iput-object p1, p0, {APP}->mCobraNextSheetAnchor:Landroid/view/View;
    invoke-direct {{p0}}, {APP}->cobraShowPreviewActions()V
    return-void
    :preview_legacy_tap
'''
    revised=tap.replace('    .registers 2\n','    .registers 4\n'+branch,1)
    raw=raw.replace(tap,revised)
    pulse=original[PULSE]
    assert pulse.count('.registers 15')==1 and re.search(r'\bv1[34]\b',pulse) is None
    revised=pulse.replace('    .registers 15\n','    .registers 16\n    move-object v13, p1\n',1)
    anchor=f'''    invoke-static/range {{v5 .. v12}}, Lcom/projectinfinity/kodi/CobraPresentationEffects;->pulseState(ZZZZZZZZ){STATE}

    move-result-object p1

    return-object p1'''
    guard=f'''    invoke-static/range {{v5 .. v12}}, Lcom/projectinfinity/kodi/CobraPresentationEffects;->pulseState(ZZZZZZZZ){STATE}
    move-result-object p1
    sget-object v0, {STATE}->NONE:{STATE}
    if-ne p1, v0, :preview_pulse_result
    if-eqz v5, :preview_pulse_result
    iget-object v0, p0, {APP}->mCobraPreviewPlayer:Landroidx/media3/exoplayer/ExoPlayer;
    if-ne v13, v0, :preview_pulse_result
    const-string v0, "cards"
    iget-object v1, p0, {APP}->mCobraGuideStyle:Ljava/lang/String;
    invoke-virtual {{v0, v1}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :preview_pulse_result
    iget-boolean v0, p0, {APP}->mCobraProActive:Z
    if-nez v0, :preview_pulse_result
    iget-boolean v0, p0, {APP}->mCobraProSportsActive:Z
    if-nez v0, :preview_pulse_result
    if-eqz v12, :preview_pulse_normal
    sget-object p1, {STATE}->LIVE:{STATE}
    return-object p1
    :preview_pulse_normal
    sget-object p1, {STATE}->NORMAL:{STATE}
    :preview_pulse_result
    return-object p1'''
    assert revised.count(anchor)==1
    raw=raw.replace(pulse,revised.replace(anchor,guard,1))
    revised=methods(raw)
    assert {n for n in original if original[n]!=revised[n]}=={TAP,PULSE}
    return raw

PULSE_VIEW='Lcom/projectinfinity/kodi/CobraPresentationEffects$PulseView;'
def patch_pulse_view(raw):
    original=methods(raw);body=original['private restart()V']
    anchor='    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraPresentationEffects$PulseState;->animated()Z\n\n    move-result v0\n\n    if-eqz v0, :cond_1'
    replacement='    invoke-virtual {v0}, Lcom/projectinfinity/kodi/CobraPresentationEffects$PulseState;->animated()Z\n    move-result v0\n    if-nez v0, :preview_original_motion_gate\n    invoke-static {p0}, Lcom/projectinfinity/kodi/CobraCardsLayout;->previewPulseAnimated(Landroid/view/View;)Z\n    move-result v0\n    if-eqz v0, :cond_1\n    :preview_original_motion_gate'
    assert body.count(anchor)==1
    return raw.replace(body,body.replace(anchor,replacement,1))
