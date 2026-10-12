#!/usr/bin/env python3
"""Exact, independently authored six-change overlay; no rejected patch is imported."""
import hashlib
import json
from pathlib import Path
import difflib

HERE=Path(__file__).resolve().parent
RUNTIME='tools/android/packaging/xbmc/src/'
EXPECTED={'InfinityLiveActivity.java.in':'02111d4971307e5e0e0e9f22c319305e2924bc1942fa03f68b7b3a3a50f2f9ba','CobraProUi.java.in':'68b5eee8a3783594cbb8da86474279b34e9181b65530e30e6bede1bf809b4ec3'}
def digest(text): return hashlib.sha256(text.encode()).hexdigest()

def apply(root,out):
    out.mkdir(exist_ok=True,parents=True)
    sources={n:(root/RUNTIME/n).read_text() for n in EXPECTED}
    for n,h in EXPECTED.items():
        if digest(sources[n])!=h: raise RuntimeError('Approved runtime identity mismatch: '+n)
    original=dict(sources);inventory=[]
    def edit(file,method,requirement,old,new):
        if sources[file].count(old)!=1: raise RuntimeError('Exact preimage count is not one: '+file+' / '+method+' / '+repr(old[:100]))
        sources[file]=sources[file].replace(old,new,1)
        inventory.append({'file':RUNTIME+file,'method':method,'requirement':requirement,'before_sha256':digest(old),'after_sha256':digest(new)})
    a='InfinityLiveActivity.java.in';u='CobraProUi.java.in'
    edit(a,'cobraRenderPlayerDrawer',1,
         'mPendingResumeMs=0;startSinglePlayer(c.primaryUrl);cobraBuildPlayerChrome();',
         'mPendingResumeMs=0;mCobraSix.tune(c,()->startSinglePlayer(c.primaryUrl));cobraBuildPlayerChrome();')
    edit(a,'buildPlayer',1,
         'CobraPlayerBinding binding=new CobraPlayerBinding(player,channel);',
         'mCobraSix.seed(player,channel,texture);\n    CobraPlayerBinding binding=new CobraPlayerBinding(player,channel);')
    edit(a,'cobraSportsWatch',[1,5],
         'private void cobraSportsWatch(CobraSportsGame game){final boolean embedded=',
         'private void cobraSportsWatch(CobraSportsGame game){if(mCobraSix.watchFromChannels(game))return;final boolean embedded=')
    edit(a,'cobraPreviewPanel',2,
         '    host.addView(bar,new FrameLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraPreviewPanel.dimensions.12",50)),Gravity.BOTTOM));',
         '    mCobraSix.previewButton(bar);\n    host.addView(bar,new FrameLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraPreviewPanel.dimensions.12",50)),Gravity.BOTTOM));')
    edit(a,'cobraBuildPlayerChrome',[2,3,4],
         'footer.addView(tools,new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.35",52))))',
         'footer.addView(mCobraSix.controls(tools,Math.max(1,width-footer.getPaddingLeft()-footer.getPaddingRight())),new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.35",52))))')
    edit(a,'CobraIconButton.onDraw',4,
         '      if(vtheme().draw(canvas,getTag() instanceof String&&((String)getTag()).startsWith("cobra-drawer-icon:")',
         '      if(mCobraSix.drawStats(this,canvas,cx,cy))return;\n      if(vtheme().draw(canvas,getTag() instanceof String&&((String)getTag()).startsWith("cobra-drawer-icon:")')
    edit(a,'showCobraSportsStats',4,
         'private void showCobraSportsStats(CobraSportsGame game){if(cobraSportsHidden(game)){',
         'private void showCobraSportsStats(CobraSportsGame game){if(mCobraSix.stats(game))return;if(cobraSportsHidden(game)){')
    edit(a,'cobraInstallProHeroOverlay',2,
         '      public void controlsChanged(){/* Control visibility does not own video geometry. */}',
         '      public void controlsChanged(){/* Control visibility does not own video geometry. */}\n      public boolean pipSupported(){return mCobraSix.phone();}\n      public void pip(){mCobraSix.miniPip();}')
    edit(a,'cobraProControl',2,
         '    if(index==2&&cobraProSportsHeroActive()){',
         '    if(index==8){mCobraSix.miniPip();return;}\n    if(index==2&&cobraProSportsHeroActive()){')
    edit(a,'onPictureInPictureModeChanged',2,
         '    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;cobraRefreshScoreTicker();',
         '    super.onPictureInPictureModeChanged(inPictureInPictureMode,configuration);mInPictureInPicture=inPictureInPictureMode;cobraRefreshScoreTicker();mCobraSix.pipChanged(inPictureInPictureMode);')
    edit(a,'onResume',2,
         '    configureCobraPip(hasCobraVideo() && mMultiOverlay == null);',
         '    configureCobraPip(hasCobraVideo() && mMultiOverlay == null);\n    mCobraSix.restoreMiniPip(false);')
    edit(a,'cobraRestoreAfterPipFailure',2,
         '  private void cobraRestoreAfterPipFailure() {',
         '  private void cobraRestoreAfterPipFailure() {mCobraSix.restoreMiniPip(true);')
    edit(a,'cobraSwitchMode',[2,3,4],
         '    mCobraGuideStyle=mode;mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;cobraShowGuideShell();',
         '    mCobraGuideStyle=mode;mCobraGuideRoute="channels";mCobraInspectedChannel=null;mCobraInspectedProgram=null;cobraShowGuideShell();\n    mCobraSix.modeChanged();')
    edit(a,'cobraBuildProChrome',6,
         'new CobraProUi.Ink(this,dark?Color.WHITE:CobraProUi.INK,22,true)',
         'new CobraProUi.Ink(this,cobraModeColor("text"),22,true)')
    edit(a,'cobraBuildProChrome',6,
         'new CobraProUi.Ink(this,dark?0xffaac2d3:CobraProUi.MUTED,10,false)',
         'new CobraProUi.Ink(this,cobraModeColor("muted"),10,false)')
    edit(a,'cobraBuildProChrome',6,
         'mCobraModeToolbar.addView(cobraIcon("multi","Choose view mode",dark,v->showCobraViewModeMenu()),new LinearLayout.LayoutParams(dp(48),-1));mCobraModeRail.removeAllViews();mCobraModeFooter.removeAllViews();',
         'mCobraModeToolbar.addView(cobraIcon("multi","Choose view mode",dark,v->showCobraViewModeMenu()),new LinearLayout.LayoutParams(dp(48),-1));mCobraModeRail.removeAllViews();mCobraModeFooter.removeAllViews();mCobraSix.headerTheme();')
    edit(a,'cobraRefreshVisualEffects',6,
         '    cobraRefreshAmbient();if(mCobraEffects==null)return;',
         '    cobraRefreshAmbient();mCobraSix.headerTheme();if(mCobraEffects==null)return;')
    fragment=(HERE/'CobraSix.fragment.java').read_text()
    last=sources[a].rfind('}')
    if sources[a][last+1:].strip(): raise RuntimeError('Unexpected activity suffix')
    sources[a]=sources[a][:last]+fragment+'\n'+sources[a][last:]
    inventory.append({'file':RUNTIME+a,'method':'CobraSix controller (new methods individually listed in fragment)','requirement':[1,2,3,4,5,6],'added_fragment_sha256':digest(fragment)})

    edit(u,'Actions',2,
         'interface Actions {',
         'interface Actions {default boolean pipSupported(){return false;} default void pip(){} ')
    edit(u,'Hero fields',2,'final Action[] player=new Action[8];','final Action[] player=new Action[9];')
    edit(u,'Hero fields',2,'final long[] lastControlClick=new long[8];','final long[] lastControlClick=new long[9];')
    edit(u,'Hero fields',2,
         'final Action preview,unmute,left,right,sportsWatch,sportsStats,sportsMulti;',
         'final Action preview,unmute,left,right,sportsWatch,sportsStats,sportsMulti; final Action pip; boolean pipAvailable;')
    edit(u,'Hero constructor',2,
         '      java.util.Arrays.fill(lastControlClick,-1L);',
         '      pip=new Action(c,"pip","",true,false,actions::pip);pip.setContentDescription("Picture-in-Picture");pip.setTag("cobra_pro_preview_pip");addView(pip);\n      java.util.Arrays.fill(lastControlClick,-1L);')
    edit(u,'Hero constructor',2,
         'String[] glyphs={"pause","favorite","cc","audio","fullscreen","more","stats","groups"},names={"Pause","Favorite","Subtitles","Audio","Fullscreen","More","Stats","Multi-View"};',
         'String[] glyphs={"pause","favorite","cc","audio","fullscreen","more","stats","groups","pip"},names={"Pause","Favorite","Subtitles","Audio","Fullscreen","More","Stats","Multi-View","PiP"};')
    edit(u,'Hero constructor',2,'new int[]{0,1,2,3,4,6,7,5}','new int[]{0,1,2,3,4,8,6,7,5}')
    edit(u,'Hero.applyModeVisibility',2,
         'show&&(i<6||sportsMode)?VISIBLE:GONE',
         'show&&(i<6||(i==8?actions.pipSupported():sportsMode))?VISIBLE:GONE')
    edit(u,'Hero.applyModeVisibility',2,
         'controlScroll.setVisibility(show?VISIBLE:INVISIBLE);transport.setVisibility((watching?!show:false)?INVISIBLE:VISIBLE);}',
         'controlScroll.setVisibility(show?VISIBLE:INVISIBLE);transport.setVisibility((watching?!show:false)?INVISIBLE:VISIBLE);pip.setVisibility(!watching&&pipAvailable&&actions.pipSupported()?VISIBLE:GONE);}')
    edit(u,'Hero.playback',2,
         'void playback(boolean playing,boolean isMuted,boolean captions,boolean available){unmute.setEnabled(available);',
         'void playback(boolean playing,boolean isMuted,boolean captions,boolean available){pipAvailable=available;pip.setEnabled(available);unmute.setEnabled(available);')
    edit(u,'Hero.playback',2,
         'if(sportsMode){player[6].setEnabled(sportsStats.isEnabled());player[7].setEnabled(sportsMulti.isEnabled());}}',
         'if(sportsMode){player[6].setEnabled(sportsStats.isEnabled());player[7].setEnabled(sportsMulti.isEnabled());}applyModeVisibility();requestLayout();}')
    edit(u,'Hero.onLayout',2,
         'place(controlScroll,controlPad,h-controlH-px(getContext(),13),w-2*controlPad,controlH);',
         'place(controlScroll,controlPad,h-controlH-px(getContext(),13),w-2*controlPad,controlH);layoutPip(w,h);')
    layout=(HERE/'HeroPip.fragment.java').read_text()
    edit(u,'Hero.layoutPip (new)',2,
         '    boolean insideControlStrip(float x,float y){',
         layout+'\n    boolean insideControlStrip(float x,float y){')
    # The Stats renderer is left byte-for-byte intact. Only a new PiP glyph is added.
    edit(u,'icon',2,
         '    else if("stats".equals(name)){',
         '    else if("pip".equals(name)){c.drawRoundRect(2,4,22,20,2,2,p);p.setStyle(Paint.Style.FILL);c.drawRoundRect(12,11,20,18,1,1,p);}\n    else if("stats".equals(name)){')
    for n,text in sources.items(): (root/RUNTIME/n).write_text(text)
    patch=''.join(''.join(difflib.unified_diff(original[n].splitlines(True),sources[n].splitlines(True),'a/'+RUNTIME+n,'b/'+RUNTIME+n)) for n in sorted(sources))
    (out/'changes.patch').write_text(patch)
    (out/'CHANGED-METHODS.json').write_text(json.dumps({'changes':inventory,'source_sha256':{n:{'before':digest(original[n]),'after':digest(sources[n])} for n in sources},'rejected_2103370_imported':False},indent=2)+'\n')
    print('Applied independently authored six-change overlay:',len(inventory),'mapped edits')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);a=p.parse_args();apply(a.source,a.out)
