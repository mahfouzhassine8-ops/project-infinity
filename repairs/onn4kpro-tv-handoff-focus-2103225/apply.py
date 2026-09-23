#!/usr/bin/env python3
"""2103225 onn. 4K Pro RC8 handoff/focus correction.

Parent: exact locked 2103224 TV Native Remote RC7 source.
Scope: four physical-TV regressions only:
- visible Multi-View list focus,
- unclipped player footer,
- preserved 2->1 Multi-View survivor session,
- first-render video surface handoffs instead of exposing black surfaces.

ARM64 phone/Fold and the ARMv7 native engine are untouched.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

VERSION=2103225
OLD_VERSION=2103224
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-Native-Remote-RC7'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Handoff-Focus-RC8'
SOURCE='tools/android/packaging/xbmc/'
ACT=SOURCE+'src/InfinityLiveActivity.java.in'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    req(text.count(old)==1,f'{label}: expected 1 anchor, got {text.count(old)}')
    return text.replace(old,new,1)

def span(text:str,name:str,kind='method'):
    if kind=='ctor':
        pat=re.compile(r'(?m)^\s*'+re.escape(name)+r'\s*\([^;\n]*\)\s*\{')
    else:
        pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w.<>,\[\]?]+\s+'+re.escape(name)+r'\s*\([^\n{;]*\)\s*\{')
    ms=list(pat.finditer(text)); req(len(ms)==1,f'{kind} cardinality {name}={len(ms)}')
    start=ms[0].start(); brace=text.find('{',ms[0].start()); depth=0; quote=None; esc=line=block=False; i=brace
    while i<len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False; i+=1
        elif quote:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: quote=None
        elif c=='/' and n=='/': line=True; i+=1
        elif c=='/' and n=='*': block=True; i+=1
        elif c in ('"',"'"): quote=c
        elif c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0: return start,i+1
        i+=1
    raise RuntimeError('unclosed '+name)

def member(text,name,kind='method'):
    a,b=span(text,name,kind); return text[a:b]
def replace_member(text,name,new,kind='method'):
    a,b=span(text,name,kind); return text[:a]+new.rstrip()+text[b:]

ROW_HELPER=r'''  private android.graphics.drawable.Drawable cobraTvMultiRowSurface(){
    android.graphics.drawable.StateListDrawable states=new android.graphics.drawable.StateListDrawable();
    states.addState(new int[]{android.R.attr.state_activated},surface(0xff18344a,10,0xff41c8ef,2));
    states.addState(new int[]{android.R.attr.state_selected},surface(0xff18344a,10,0xff41c8ef,2));
    states.addState(new int[]{android.R.attr.state_focused},surface(0xff18344a,10,0xff41c8ef,2));
    states.addState(new int[]{},surface(0xff0d141d,10,0xff263748,1));
    return states;
  }

  private void cobraTvPaintMultiRowSelection(android.widget.ListView list,int wanted){
    if(list==null)return;int first=list.getFirstVisiblePosition();
    for(int i=0;i<list.getChildCount();i++){
      View row=list.getChildAt(i);boolean active=first+i==wanted;
      if(row!=null){row.setActivated(active);row.setSelected(active);}
    }
  }

'''

def patch_activity(path:Path):
    before=path.read_bytes(); s=before.decode()
    marker='  private static final String COBRA_TV_NATIVE_REMOTE_BUILD="cobra_tv_native_remote_2103224";'
    req(s.count(marker)==1,'2103224 native remote marker missing')
    s=s.replace(marker,'  private static final String COBRA_TV_HANDOFF_FOCUS_BUILD="cobra_tv_handoff_focus_2103225";\n'+marker,1)

    # Surface handoffs finish on the first rendered video frame, not merely when TextureView exists.
    s=replace_member(s,'cobraTvAttachSurfaceWhenReady',r'''  private void cobraTvAttachSurfaceWhenReady(ExoPlayer player,TextureView texture,Runnable ready){
    if(player==null||texture==null)return;
    final int generation=++mCobraTvSurfaceHandoffGeneration;
    texture.animate().cancel();texture.setAlpha(0f);texture.setVisibility(View.VISIBLE);
    final boolean[] done={false};final Runnable[] fallback={null};
    final androidx.media3.common.Player.Listener[] listener=new androidx.media3.common.Player.Listener[1];
    final Runnable finish=()->{
      if(done[0])return;done[0]=true;
      if(listener[0]!=null)try{player.removeListener(listener[0]);}catch(Exception ignored){}
      if(fallback[0]!=null)texture.removeCallbacks(fallback[0]);
      if(generation!=mCobraTvSurfaceHandoffGeneration)return;
      texture.setAlpha(1f);
      if(ready!=null)ready.run();
    };
    listener[0]=new androidx.media3.common.Player.Listener(){
      @Override public void onRenderedFirstFrame(){texture.post(finish);}
      @Override public void onPlayerError(androidx.media3.common.PlaybackException error){texture.post(finish);}
    };
    player.addListener(listener[0]);
    final Runnable[] poll=new Runnable[1];final int[] tries={0};
    poll[0]=()->{
      if(generation!=mCobraTvSurfaceHandoffGeneration){
        if(listener[0]!=null)try{player.removeListener(listener[0]);}catch(Exception ignored){}
        return;
      }
      if(texture.isAvailable()||tries[0]++>=180){
        cobraAttachVideo(player,texture);
        fallback[0]=finish;
        texture.postDelayed(fallback[0],2400L);
        return;
      }
      texture.postDelayed(poll[0],16L);
    };
    texture.post(poll[0]);
  }''')

    # Multi-View rows own an explicit selected/activated drawable. RC7's opaque row surface
    # covered the ListView selector, so D-pad navigation moved but appeared invisible.
    focus_anchor='  private boolean cobraTvFocusMultiRow(int position){'
    req(s.count(focus_anchor)==1,'Multi-View row focus anchor missing')
    s=s.replace(focus_anchor,ROW_HELPER+focus_anchor,1)

    picker=member(s,'showCobraMultiPicker')
    picker=once(picker,
      'list.setSelector(surface(0xff15263a,12,0xff41c8ef,2));content.addView(list,new LinearLayout.LayoutParams(-1,0,1));',
      'list.setSelector(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));list.setDrawSelectorOnTop(false);content.addView(list,new LinearLayout.LayoutParams(-1,0,1));',
      'Multi-View selector ownership')
    s=replace_member(s,'showCobraMultiPicker',picker)

    render=member(s,'renderCobraMultiPicker')
    render=once(render,
      'row.setBackground(surface(0xff0d141d,10,0xff263748,1));row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(68)));',
      'row.setBackground(cobraTvMultiRowSurface());row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(68)));',
      'Multi-View visible row state')
    s=replace_member(s,'renderCobraMultiPicker',render)

    search=member(s,'renderCobraMultiPickerSearch')
    search=once(search,
      'row.setFocusable(false);row.setClickable(false);row.setBackground(surface(0xff0d141d,10,0xff263748,1));row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(68)));',
      'row.setFocusable(false);row.setClickable(false);row.setBackground(cobraTvMultiRowSurface());row.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1,dp(68)));',
      'Multi-View search visible row state')
    s=replace_member(s,'renderCobraMultiPickerSearch',search)

    s=replace_member(s,'cobraTvFocusMultiRow',r'''  private boolean cobraTvFocusMultiRow(int position){
    android.widget.ListView list=cobraTvMultiList();if(list==null||list.getAdapter()==null||list.getAdapter().getCount()==0)return false;
    mCobraTvMultiRow=Math.max(0,Math.min(list.getAdapter().getCount()-1,position));
    list.setSelection(mCobraTvMultiRow);list.setItemChecked(mCobraTvMultiRow,true);list.requestFocus();cobraTvPaintMultiRowSelection(list,mCobraTvMultiRow);
    final int wanted=mCobraTvMultiRow;list.post(()->{if(list!=cobraTvMultiList())return;list.setSelection(wanted);list.setItemChecked(wanted,true);cobraTvPaintMultiRowSelection(list,wanted);});
    return true;
  }''')

    # RC7's tool children are 58dp high but their parent row is only 52dp, physically clipping
    # Channels / Display / Multi-View / More. Keep button sizing and give the row safe breathing room.
    chrome=member(s,'cobraBuildPlayerChrome')
    chrome=once(chrome,
      'footer.setPadding(left+dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.22",4)),dp(shortScreen?8:24),right+dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.23",4)),bottom);',
      'footer.setPadding(left+dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.22",4)),dp(shortScreen?8:24),right+dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.23",4)),bottom+dp(8));',
      'TV player footer safe bottom')
    chrome=once(chrome,
      'footer.addView(tools,new LinearLayout.LayoutParams(-1,dp(vtheme().dimension("cobra.cobraBuildPlayerChrome.dimensions.35",52))));',
      'footer.addView(tools,new LinearLayout.LayoutParams(-1,dp(64)));',
      'TV player tool row unclipped')
    s=replace_member(s,'cobraBuildPlayerChrome',chrome)

    # Preserve the surviving ExoPlayer and the old Multi-View frame during the 2->1 transition.
    # The previous path removed Multi-View first and immediately attached the session to a new
    # black TextureView, which exposed a black/loading screen.
    s=replace_member(s,'multiToSingle',r'''  private void multiToSingle() {
    if(mMultiChannels==null||mMultiChannels.length==0)return;
    int owner=Math.max(0,Math.min(mAudioTile,mMultiChannels.length-1));CobraVideoTile tile=mCobraTiles.take(mMultiChannels[owner].id);if(tile==null)return;
    ExoPlayer session=tile.player;Channel channel=tile.channel;tile.player=null;
    cobraRememberChannelTransition(channel);closeCobraActionSheet();
    boolean restart=!mCobraPreparingMultiPip&&cobraShouldUseLocalTimeshift(channel,channel.primaryUrl);
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mCobraTvOpeningSurfaceHandoff=session!=null&&!restart;openPlayerOverlay(channel);
    if(restart){
      mReflowingMulti=true;releaseMulti();mReflowingMulti=false;
      cobraDisposePlayer(session);mPlayer=null;startSinglePlayer(channel.primaryUrl);return;
    }
    mPlayer=session;
    if(session!=null){
      cobraTvAttachSurfaceWhenReady(session,mPlayerTexture,()->{
        if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.BLACK);
        if(mPlayerTexture!=null)mPlayerTexture.setOpaque(true);
        session.setAudioAttributes(session.getAudioAttributes(),false);session.setVolume(1f);cobraClaimAudioFocus(session);
        mReflowingMulti=true;releaseMulti();mReflowingMulti=false;
        configureCobraPip(true);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();
      });
    }else{
      mReflowingMulti=true;releaseMulti();mReflowingMulti=false;startSinglePlayer(channel.primaryUrl);
      configureCobraPip(true);cobraUpdatePlaybackLabels();cobraStartPresentationTicker();
    }
  }''')

    # Even a cold direct tune keeps the guide underneath when a synchronous player is created.
    s=replace_member(s,'promoteCobraPreviewToFullscreen',r'''  private void promoteCobraPreviewToFullscreen(Channel channel) {
    if(channel==null)return;ExoPlayer session=cobraChannelKey(channel).equals(mCobraPreviewSessionKey)?mCobraPreviewPlayer:null;
    boolean local=session==mCobraTimeshiftPlayer&&mCobraTimeshiftSession!=null,proxy=session==mCobraTimeshiftProxyPlayer&&mCobraTimeshiftSession!=null;
    mCobraTvFullscreenReturnFocus=getCurrentFocus();cobraEndMiniBackgroundPlayback();
    mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";mCobraPreviewHandoffs++;
    mPlaying=channel;mPlayingIndex=mChannels.indexOf(channel);mTriedFallback=false;mCobraTvOpeningSurfaceHandoff=true;openPlayerOverlay(channel);mPlayer=session;
    if(local)mCobraTimeshiftPlayer=session;if(proxy)mCobraTimeshiftProxyPlayer=session;
    if(session!=null){
      cobraTvAttachSurfaceWhenReady(session,mPlayerTexture,()->{
        if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.BLACK);
        if(mPlayerTexture!=null)mPlayerTexture.setOpaque(true);
        session.setAudioAttributes(session.getAudioAttributes(),false);session.setVolume(1f);cobraClaimAudioFocus(session);
        showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();
      });
    }else{
      startSinglePlayer(channel.primaryUrl);ExoPlayer started=mPlayer;
      if(started!=null)cobraTvAttachSurfaceWhenReady(started,mPlayerTexture,()->{
        if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.BLACK);
        if(mPlayerTexture!=null)mPlayerTexture.setOpaque(true);
        showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();
      });
      else{
        if(mPlayerOverlay!=null)mPlayerOverlay.setBackgroundColor(Color.BLACK);
        if(mPlayerTexture!=null){mPlayerTexture.setAlpha(1f);mPlayerTexture.setOpaque(true);}
      }
    }
    cobraStartPresentationTicker();cobraUpdatePlaybackLabels();configureCobraPip(false);
    cobraSetTimeshiftUiState((local||proxy)&&mCobraTimeshiftSession.ready()?"READY":(local||proxy)?"RECORDING":cobraChannelRewindEnabled(channel)&&cobraLiveChannel(channel)?"UNSUPPORTED":"OFF",(local||proxy)?Math.round(mCobraTimeshiftSession.windowDurationMs()/1000f)+"s":"");
    if(mDeviceBridge!=null)mDeviceBridge.onPlaybackChanged(local?"preview-timeshift-fullscreen":"preview-fullscreen");
  }''')

    req('cobra_tv_handoff_focus_2103225' in s,'RC8 marker missing')
    req('onRenderedFirstFrame' in member(s,'cobraTvAttachSurfaceWhenReady'),'First-frame handoff missing')
    req('cobraTvMultiRowSurface()' in s,'Visible Multi-View row state missing')
    req('new LinearLayout.LayoutParams(-1,dp(64))' in member(s,'cobraBuildPlayerChrome'),'Unclipped TV tool row missing')
    req('mReflowingMulti=true;releaseMulti();mReflowingMulti=false;\n        configureCobraPip(true)' in member(s,'multiToSingle'),'Survivor release ordering missing')
    path.write_text(s)
    return sha_bytes(before),sha(path)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json'); receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,'Expected exact locked 2103224 RC7 parent')
    req(receipt.get('tv_variant') is True and receipt.get('tv_target_abi')=='armeabi-v7a','Expected ARMv7 TV parent')
    req(receipt.get('tv_native_remote_architecture') is True and receipt.get('tv_hardening') is True,'Expected RC7 TV architecture parent')
    req(receipt.get('multiview_fullscreen_reversible') is True and receipt.get('tv_multiview_picker_focus_owner') is True,'Expected RC7 Multi-View contracts')

    activity=shell/ACT; gradle=shell/(SOURCE+'build.gradle.in')
    for p in (activity,gradle): req(p.is_file(),'Missing '+str(p))
    activity_before,activity_after=patch_activity(activity)
    g=gradle.read_text(); g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName'); gradle.write_text(g)

    for rel in (ACT,SOURCE+'build.gradle.in'):
        req(rel in receipt['files'],'Receipt missing '+rel); receipt['files'][rel]['after']=sha(shell/rel)
    receipt.update(
      version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,candidate_locked=False,
      physical_device_verified=False,runtime_device_tested=False,tv_variant=True,tv_target_abi='armeabi-v7a',
      tv_handoff_first_render=True,tv_black_surface_exposure_fixed=True,
      tv_multiview_row_focus_visible=True,tv_player_footer_unclipped=True,
      multiview_two_to_one_session_preserved=True,multiview_survivor_player_recreated=False,
      mobile_parent_untouched=True,native_engine_rebuilt=False,playback_engine_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items(): req(sha(shell/name)==row['after'],'Final receipt drift '+name)

    Path('audit225').mkdir(exist_ok=True)
    Path('audit225/tv-handoff-focus-source.json').write_text(json.dumps({
      'build':VERSION,'version_name':NEW_NAME,'parent_build':OLD_VERSION,'target_abi':'armeabi-v7a',
      'activity_before_sha256':activity_before,'activity_after_sha256':activity_after,
      'marker':'cobra_tv_handoff_focus_2103225','mobile_fold_untouched':True,
      'multiview_row_focus_visible':True,'player_footer_unclipped':True,
      'surface_handoff_waits_first_rendered_frame':True,'surface_handoff_timeout_ms':2400,
      'multiview_two_to_one_session_preserved':True,'survivor_player_recreated':False,
      'native_engine_rebuilt':False,'playback_engine_unchanged':True,'physical_device_verified':False
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103225 RC8 handoff/focus correction applied over exact locked 2103224 RC7')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--shell',type=Path,required=True); a=p.parse_args(); apply(a.shell)
if __name__=='__main__': main()
