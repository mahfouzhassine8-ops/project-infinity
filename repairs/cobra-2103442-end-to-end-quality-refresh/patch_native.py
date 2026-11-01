"""Exact signed442 preimages; preserve player, lifecycle and layout calculations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cobra-next-from-2103427/cards-from-2103431'))
from projection_patch import methods
APP='Lcom/projectinfinity/kodi/InfinityLiveActivity;'
HELPER='Lcom/projectinfinity/kodi/CobraGuidePresentation;'
CHANNEL=APP[:-1]+'$Channel;'
SIX=APP[:-1]+'$CobraSix;'

def patch_preview(raw):
    before=methods(raw);sig='smallPreviewPip()V';original=before[sig]
    old='invoke-virtual {v1, v0}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V'
    assert original.count(old)==1 and 'invoke-virtual {v1, v0}, Landroid/view/View;->setVisibility(I)V' in original
    new='invoke-static {v1, v0}, '+HELPER+'->previewLayout(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V'
    return raw.replace(original,original.replace(old,new))

def patch(raw):
    before=methods(raw)
    fmt='private formatTime(J)Ljava/lang/String;'
    assert 'Ljava/text/SimpleDateFormat;' in before[fmt] and 'EEE MMM d' in before[fmt]
    replacement='.method '+fmt+'\n    .registers 3\n    invoke-static {p1, p2}, '+HELPER+'->time(J)Ljava/lang/String;\n    move-result-object p0\n    return-object p0\n.end method'
    raw=raw.replace(before[fmt],replacement)
    next_sig='private cobraNextProgram('+CHANNEL+')'+APP[:-1]+'$GuideProgram;'
    original=before[next_sig]
    old_call=APP+'->cobraPrograms('+CHANNEL+')Ljava/util/ArrayList;'
    new_call=APP+'->cobraNextProgramList('+CHANNEL+')Ljava/util/ArrayList;'
    assert original.count(old_call)==1
    raw=raw.replace(original,original.replace(old_call,new_call))
    sig='private cobraPrograms('+CHANNEL+')Ljava/util/ArrayList;'
    copied=before[sig].replace(' cobraPrograms(',' cobraNextProgramList(',1)
    old='invoke-direct {p0, v0, p1}, '+APP+'->cobraMergeProgrammeRanges(Ljava/util/List;Ljava/util/List;)Ljava/util/ArrayList;'
    assert copied.count(old)==1, copied
    copied=copied.replace(old,'invoke-static {p0, v0, p1}, '+HELPER+'->nextPrograms(Landroid/app/Activity;Ljava/util/ArrayList;Ljava/util/ArrayList;)Ljava/util/ArrayList;')
    return raw+'\n'+copied+'\n'
