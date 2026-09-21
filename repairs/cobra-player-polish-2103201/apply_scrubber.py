"""Repair timeline gesture ownership and on-demand entry; preserve timeshift transport."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "cobra201_timeshift_source_tools",
    Path(__file__).resolve().parents[1] / "cobra-power-audit-2103199/apply_timeshift.py")
_tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools)
once, member, edit_method, span = _tools.once, _tools.member, _tools.edit_method, _tools.span

HELPERS = r'''
  private boolean mCobraTimelineCancelled=false;
  private ExoPlayer mCobraTimelineDragPlayer;
  private CobraLocalTimeshiftSession mCobraTimelineDragSession;
  private int mCobraPendingTimelineValue=-1;
  private ExoPlayer mCobraPendingTimelinePlayer;
  private CobraLocalTimeshiftSession mCobraPendingTimelineSession;

  private void cobraHoldTimelineChrome(){
    mMain.removeCallbacks(mHideChrome);
    if(mPlayerChrome!=null){mPlayerChrome.animate().cancel();mPlayerChrome.setAlpha(1f);mPlayerChrome.setTranslationY(0f);}
  }

  private void cobraResetTimelineGesture(){
    mCobraTimeshiftDragging=false;mCobraTimelineCancelled=true;
    mCobraTimelineDragPlayer=null;mCobraTimelineDragSession=null;
  }

  private void cobraClearPendingTimelineSeek(){
    mCobraPendingTimelineValue=-1;mCobraPendingTimelinePlayer=null;mCobraPendingTimelineSession=null;
  }

  private void cobraBindTimelineTouch(FrameLayout timeline,android.widget.SeekBar seek){
    // Even when rewind is off or still warming, this visible control owns its
    // gesture. A hold on program progress must not reach the video drawer.
    timeline.setClickable(true);timeline.setFocusable(false);
    timeline.setOnTouchListener((v,event)->{
      int action=event.getActionMasked();
      if(action==android.view.MotionEvent.ACTION_DOWN)cobraHoldTimelineChrome();
      else if(action==android.view.MotionEvent.ACTION_UP||action==android.view.MotionEvent.ACTION_CANCEL)showPlayerChromeTemporarily();
      return false;
    });
    seek.setOnTouchListener((v,event)->{
      if(v!=mCobraTimeshiftSeek)return true;
      int action=event.getActionMasked();
      if(action==android.view.MotionEvent.ACTION_DOWN){
        mCobraTimelineCancelled=false;cobraHoldTimelineChrome();
        if(v.getParent()!=null)v.getParent().requestDisallowInterceptTouchEvent(true);
      }else if(action==android.view.MotionEvent.ACTION_CANCEL)mCobraTimelineCancelled=true;
      if(action==android.view.MotionEvent.ACTION_UP||action==android.view.MotionEvent.ACTION_CANCEL)
        if(v.getParent()!=null)v.getParent().requestDisallowInterceptTouchEvent(false);
      return false;
    });
    seek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
      public void onStartTrackingTouch(android.widget.SeekBar bar){
        if(bar!=mCobraTimeshiftSeek)return;
        mCobraTimeshiftDragging=true;mCobraTimelineCancelled=false;
        mCobraTimelineDragPlayer=mPlayer;mCobraTimelineDragSession=mCobraTimeshiftSession;
        cobraHoldTimelineChrome();
      }
      public void onProgressChanged(android.widget.SeekBar bar,int value,boolean user){
        if(bar!=mCobraTimeshiftSeek||!user)return;
        if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setProgress(value);
        // Touch previews the position; keyboard/accessibility changes commit directly.
        if(!mCobraTimeshiftDragging){cobraCommitTimelineSeek(value);showPlayerChromeTemporarily();}
      }
      public void onStopTrackingTouch(android.widget.SeekBar bar){
        if(bar!=mCobraTimeshiftSeek)return;
        boolean commit=!mCobraTimelineCancelled&&mCobraTimeshiftDragging
            &&mPlayer==mCobraTimelineDragPlayer&&mCobraTimeshiftSession==mCobraTimelineDragSession;
        int value=bar.getProgress();cobraResetTimelineGesture();
        if(commit)cobraCommitTimelineSeek(value);
        cobraUpdateTimeshiftSeek();showPlayerChromeTemporarily();
      }
    });
  }

  private boolean cobraReadyTimelineProxy(){
    return cobraLiveRewindEnabled()&&mPlayer!=null&&cobraLiveChannel(mPlaying)&&mPlayingVodKey.isEmpty()
        &&mPlayer==mCobraTimeshiftProxyPlayer&&mCobraTimeshiftSession!=null
        &&mCobraTimeshiftSession.ready()&&mCobraTimeshiftSession.windowDurationMs()>0L;
  }

  private void cobraCommitTimelineSeek(int value){
    if(!cobraTimeshiftTimelineAvailable())return;
    value=Math.max(0,Math.min(1000,value));
    ExoPlayer player=mPlayer;CobraLocalTimeshiftSession session=mCobraTimeshiftSession;
    try{
      if(cobraReadyTimelineProxy()){
        // Releasing at the live edge does not unnecessarily switch the live proxy.
        if(value==1000)return;
        mCobraPendingTimelineValue=value;mCobraPendingTimelinePlayer=player;mCobraPendingTimelineSession=session;
        if(!cobraActivateLocalTimeshift(player,mPlaying,0L))cobraClearPendingTimelineSeek();
      }else{
        cobraClearPendingTimelineSeek();long duration=player.getDuration();
        if(duration>0L&&duration!=C.TIME_UNSET&&player.isCurrentMediaItemSeekable())
          player.seekTo(Math.max(0L,Math.min(duration,(duration*value)/1000L)));
      }
    }catch(RuntimeException failure){cobraClearPendingTimelineSeek();InfinityCobraDiagnostics.failure(this,"timeline-seek",failure);}
    cobraUpdateLiveRewindControls();
  }

  private void cobraApplyPendingTimelineSeek(ExoPlayer player){
    if(mCobraPendingTimelineValue<0||player!=mCobraPendingTimelinePlayer)return;
    if(player!=mCobraTimeshiftPlayer||mCobraTimeshiftSession!=mCobraPendingTimelineSession
        ||(player!=mPlayer&&player!=mCobraPreviewPlayer)){cobraClearPendingTimelineSeek();return;}
    try{
      long duration=player.getDuration();
      if(duration<=0L||duration==C.TIME_UNSET||!player.isCurrentMediaItemSeekable())return;
      int value=mCobraPendingTimelineValue;cobraClearPendingTimelineSeek();
      player.seekTo(Math.max(0L,Math.min(duration,(duration*value)/1000L)));
    }catch(RuntimeException failure){cobraClearPendingTimelineSeek();InfinityCobraDiagnostics.failure(this,"timeline-ready-seek",failure);}
  }
'''

AVAILABLE = r'''  private boolean cobraTimeshiftTimelineAvailable(){
    if(!cobraLiveRewindEnabled()||mPlayer==null||!cobraLiveChannel(mPlaying)||!mPlayingVodKey.isEmpty())return false;
    if(cobraReadyTimelineProxy())return true;
    try{return mPlayer.isCurrentMediaItemSeekable()&&mPlayer.getDuration()>0L&&mPlayer.getDuration()!=C.TIME_UNSET;}
    catch(RuntimeException unavailable){return false;}
  }'''

UPDATE = r'''  private void cobraUpdateTimeshiftSeek(){
    if(mCobraTimeshiftSeek==null)return;
    boolean available=cobraTimeshiftTimelineAvailable();long duration=0,position=0;
    if(available)try{
      if(cobraReadyTimelineProxy()){duration=mCobraTimeshiftSession.windowDurationMs();position=duration;}
      else{duration=mPlayer.getDuration();position=mPlayer.getCurrentPosition();}
    }catch(RuntimeException unavailable){available=false;}
    if(!available){mCobraTimeshiftSeek.setVisibility(View.GONE);return;}
    int value=(int)Math.max(0,Math.min(1000,(position*1000L)/Math.max(1,duration)));
    mCobraTimeshiftSeek.setVisibility(View.VISIBLE);
    if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setVisibility(View.VISIBLE);
    if(!mCobraTimeshiftDragging){
      if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setProgress(value);
      mCobraTimeshiftSeek.setProgress(value);
    }
  }'''

def transform(text):
    text = once(text, '  private boolean cobraTimeshiftTimelineAvailable(){', HELPERS + '\n  private boolean cobraTimeshiftTimelineAvailable(){', 'timeline helpers')
    old = member(text, 'cobraTimeshiftTimelineAvailable')
    text = once(text, old, AVAILABLE, 'timeline availability')
    text = once(text, member(text, 'cobraUpdateTimeshiftSeek'), UPDATE, 'timeline update')
    text = edit_method(text, 'cobraBuildPlayerChrome',
                       'mCobraTimeshiftDragging=false;mCobraTimeshiftSeek=new android.widget.SeekBar(this);',
                       'cobraResetTimelineGesture();mCobraTimeshiftSeek=new android.widget.SeekBar(this);')
    old = '    mCobraTimeshiftSeek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){public void onStartTrackingTouch(android.widget.SeekBar b){mCobraTimeshiftDragging=true;mMain.removeCallbacks(mHideChrome);}public void onProgressChanged(android.widget.SeekBar b,int value,boolean user){if(!user||mPlayer==null)return;long duration=mPlayer.getDuration();if(duration>0&&duration!=C.TIME_UNSET&&mPlayer.isCurrentMediaItemSeekable()){if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setProgress(value);mPlayer.seekTo((duration*value)/1000L);}}public void onStopTrackingTouch(android.widget.SeekBar b){mCobraTimeshiftDragging=false;showPlayerChromeTemporarily();}});'
    text = once(text, old, '    cobraBindTimelineTouch(timeline,mCobraTimeshiftSeek);', 'actual timeline listeners')
    text = once(text, '        if(player==mCobraTimeshiftPlayer)cobraCancelTimeshiftStallCheck();',
                '        if(player==mCobraTimeshiftPlayer)cobraCancelTimeshiftStallCheck();\n        cobraApplyPendingTimelineSeek(player);', 'ready position callback')
    text = edit_method(text, 'cobraStopLocalTimeshift',
                       '    CobraLocalTimeshiftSession session=mCobraTimeshiftSession;',
                       '    cobraResetTimelineGesture();cobraClearPendingTimelineSeek();\n    CobraLocalTimeshiftSession session=mCobraTimeshiftSession;')
    text = edit_method(text, 'cobraRewindLive', '    if(!cobraLiveRewindEnabled())',
                       '    cobraClearPendingTimelineSeek();\n    if(!cobraLiveRewindEnabled())')
    text = edit_method(text, 'cobraGoLive', '    if(mPlayer==null',
                       '    cobraClearPendingTimelineSeek();\n    if(mPlayer==null')
    return text
