#!/usr/bin/env python3
"""Five adaptive Cobra presentations over immutable, audited 2103153.

No native, renderer, decoder, EPG parser, credential, Multi-View or player lock
owner is replaced. Only presentation methods are allowed in this delta.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from infinity_cobra_2103153_refinement import method_span,inject
ROOT=Path(__file__).resolve().parents[1]
LIVE=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASELINE='00d8984b7979db9400fd2e0799ae3736b3cb579953c6a847fd3d193ab1fa6872'
MODULES=('layout','shell','mode-controls','mode-renderers','rows','timeline','navigation')

def patch(before:str)->tuple[str,list[str]]:
    digest=hashlib.sha256(before.encode()).hexdigest()
    if digest!=BASELINE:raise RuntimeError('Locked 2103153 preimage mismatch: '+digest)
    text=before;root=ROOT/'patches/cobra-2103154';changed=[];append=[]
    anchor='  private final Handler mMain = new Handler(Looper.getMainLooper());\n'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+(root/'fields.java.inc').read_text()+'\n',1)
    for name in MODULES:
        raw=(root/(name+'.java.inc')).read_text()
        parts=re.split(r'^// @(replace [A-Za-z0-9_]+|append)\s*\n',raw,flags=re.M)
        if parts[0].strip() or len(parts)%2!=1:raise RuntimeError(name+': invalid module')
        for marker,code in zip(parts[1::2],parts[2::2]):
            if marker=='append':append.append(code.rstrip());continue
            method=marker.split()[1]
            if method in changed:raise RuntimeError('duplicate method: '+method)
            a,b=method_span(text,method);text=text[:a]+code.rstrip()+'\n'+text[b:];changed.append(method)
    pos=text.rfind('\n}');assert pos>0
    text=text[:pos]+'\n\n'+'\n\n'.join(append)+text[pos:]
    # Do not alter the preview session; tag its existing overlay for compact displays.
    text=inject(text,'cobraPreviewPanel','    LinearLayout bar=new LinearLayout(this);',
                '    LinearLayout bar=new LinearLayout(this);bar.setTag("cobra_preview_controls");')
    text=inject(text,'cobraPreviewPanel','host.setOnLongClickListener(v->{if(mGuidePreviewChannel!=null)showCobraChannelActions(mGuidePreviewChannel);return true;});',
                'host.setOnLongClickListener(v->{cobraShowPreviewActions();return true;});')
    text=inject(text,'clearStage','    while (mStage.getChildCount() > 2) {',
                '    cobraRememberModeScroll();\n    mHeader.setVisibility(View.VISIBLE);mStatus.setVisibility(View.VISIBLE);\n    mStage.setPadding(dp(12),dp(10),dp(12),dp(12));\n    while (mStage.getChildCount() > 2) {')
    # Programme labels refresh in place on the existing presentation ticker.
    a,b=method_span(text,'cobraRefreshProgrammeLabels');block=text[a:b];last=block.rfind('}')
    block=block[:last]+'  cobraRefreshModeDetails();\n  '+block[last:];text=text[:a]+block+text[b:]
    # Back in a wide TV grid opens the group rail without closing the video.
    text=inject(text,'onBackPressed','mCobraGuideRoute="categories";mSearch="";cobraRenderGuideBrowser();return;',
                'mCobraGuideRoute="categories";mSearch="";mCobraModeGroupsExpanded=true;cobraLayoutGuide();cobraRenderGuideBrowser();return;')
    changed+=['cobraPreviewPanel','clearStage','cobraRefreshProgrammeLabels','onBackPressed']
    verify(before,text,changed)
    return text,changed

def verify(before:str,after:str,changed:list[str])->None:
    # Everything not explicitly enumerated by the presentation delta remains byte-identical.
    names=re.findall(r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b([A-Za-z0-9_]+)\s*\(',before,re.M)
    for name in set(names)-set(changed):
        try:a,b=method_span(before,name);x,y=method_span(after,name)
        except RuntimeError:continue # Existing overloads/classes are not targeted by this delta.
        if before[a:b]!=after[x:y]:raise RuntimeError('Unrelated method changed: '+name)
    for name in ('cobraLayoutGuide','cobraRenderGuideBrowser','cobraRenderMobileMode','cobraRenderGridMode','cobraRenderCompactMode','cobraRenderCardsMode','cobraRenderFocusMode','cobraSwitchMode'):
        a,b=method_span(after,name);block=after[a:b]
        for forbidden in ('new TextureView','.prepare(','.release(','.stop(','.setMediaItem(','.setVideoTextureView(','stopCobraPreview(','.clearVideoTextureView('):
            if forbidden in block:raise RuntimeError(name+': playback mutation '+forbidden)
    for token in ('CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow','CobraBroadcastRow','cobra_tv_time_ruler','cobra_mode_bottom_navigation','CobraModeLayout.MODES'):
        if token not in after:raise RuntimeError('Missing mode contract: '+token)
    # TV Grid remains a time grid in portrait, not a disguised mobile list.
    a,b=method_span(after,'cobraRenderGridMode')
    if 'isPortrait' in after[a:b]:raise RuntimeError('Portrait grid was replaced with another mode')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    file=a.source/LIVE;before=file.read_text();after,changed=patch(before)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    backup=a.receipt.parent/'2103153-exact.java.in';backup.write_text(before)
    file.write_text(after)
    a.receipt.write_text(json.dumps({'baseline':2103153,'candidate':2103154,'before_sha256':BASELINE,'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'changed_methods':changed,'native_changed':False,'device_verified':False,'all_five_modes':'mobile,grid,compact,cards,focus'},indent=2)+'\n')
    print('PASS: exact 2103153 preserved; five adaptive presentation renderers installed')
if __name__=='__main__':main()
