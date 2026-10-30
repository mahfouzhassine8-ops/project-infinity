"""Remove only guide-label writes that the same tick's final writer replaces.

The existing mode-details writer and every playback/favorite/indicator update
remain in their original order. Without that writer's exact readiness guard,
the original preliminary guide-update path is retained unchanged.
"""
import hashlib
from projection_patch import methods

SIGNATURE = 'private cobraRefreshProgrammeLabels()V'
PREIMAGE = '5d02c9f97fc5c7c5332c234d606fa7e63441ea7a8c07f5e761407b75318a98de'
FINAL_SIGNATURE = 'private cobraRefreshModeDetails()V'
FINAL_PREIMAGE = 'b2b6ad3345f824345a3f29b1cc48b85af2975e36864f0ae4329bb0464eac1056'
APP = 'Lcom/projectinfinity/kodi/InfinityLiveActivity;'


def patch_activity(text):
    before = methods(text)
    old = before[SIGNATURE]
    assert hashlib.sha256(old.encode()).hexdigest() == PREIMAGE
    assert hashlib.sha256(before[FINAL_SIGNATURE].encode()).hexdigest() == FINAL_PREIMAGE
    anchor = '    iget-object v1, v0, '+APP+'->mGuidePreviewChannel:Lcom/projectinfinity/kodi/InfinityLiveActivity$Channel;'
    assert old.count(anchor) == 1
    assert old.count('    :goto_5\n') == 1
    assert old.count('->cobraRefreshModeDetails()V') == 1
    guard = r'''

    iget-object v2, v0, @APP@->mCobraModeEyebrow:Landroid/widget/TextView;
    if-eqz v2, :cobra_programme_original_guide_labels
    iget-object v2, v0, @APP@->mCobraModeLayout:Lcom/projectinfinity/kodi/InfinityLiveActivity$CobraModeLayout;
    if-eqz v2, :cobra_programme_original_guide_labels

    # These constants were previously initialized inside the preliminary guide
    # block and remain live in the unchanged player-label/progress block.
    const/high16 v4, 0x447a0000
    const-string v7, "Next  "
    const/4 v8, 0x0
    const-string v9, ""
    const-wide/32 v10, 0xea5f
    const-string v12, " \u2013 "
    goto/16 :goto_5

    :cobra_programme_original_guide_labels
'''.replace('@APP@', APP)
    revised = old.replace(anchor, anchor+guard, 1)
    result = text.replace(old, revised, 1)
    after = methods(result)
    assert set(before) == set(after)
    assert {key for key in before if before[key] != after[key]} == {SIGNATURE}
    return result
