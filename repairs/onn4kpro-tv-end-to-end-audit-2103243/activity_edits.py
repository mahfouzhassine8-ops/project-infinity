"""Explicit Android Activity corrections. apply.py supplies hash-pinned s and member parser lib."""
def get(n):return lib['member'](s,n)
def replace(n,t):
 global s
 s=lib['repl'](s,n,t)
def once(a,b):
 global s
 assert s.count(a)==1,(a[:120],s.count(a));s=s.replace(a,b,1)
def edit(n,a,b):
 t=get(n);assert t.count(a)==1,(n,a[:80],t.count(a));replace(n,t.replace(a,b,1))

helpers=r'''  // RC23: input ownership and cancellation are presentation-only; no decoder ownership changes.
  private final android.util.SparseLongArray mCobraTvConsumedDownTimes=new android.util.SparseLongArray();
  private final android.util.SparseIntArray mCobraTvConsumedDevices=new android.util.SparseIntArray();
  private int mCobraTvFocusInputGeneration=0,mCobraTvPowerFocusGeneration=0;
  private volatile int mCobraVodDetailsGeneration=0;
  private int mCobraTvRemoteEdgeDevice=-1;
  private View mCobraTvPowerPreviousFocus;
  private boolean mCobraTvMultiActivationPending=false;

  private boolean cobraTvDiscreteKey(int code){
    return code==KeyEvent.KEYCODE_BACK||code==KeyEvent.KEYCODE_MENU||code==KeyEvent.KEYCODE_DPAD_CENTER||
        code==KeyEvent.KEYCODE_ENTER||code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE||code==KeyEvent.KEYCODE_LAST_CHANNEL||
        code==KeyEvent.KEYCODE_CHANNEL_UP||code==KeyEvent.KEYCODE_CHANNEL_DOWN;
  }

  private boolean cobraTvRecordConsumedKey(KeyEvent event){
    if(event.getAction()==KeyEvent.ACTION_DOWN&&cobraTvDiscreteKey(event.getKeyCode())){
      mCobraTvConsumedDownTimes.put(event.getKeyCode(),event.getDownTime());
      mCobraTvConsumedDevices.put(event.getKeyCode(),event.getDeviceId());
    }
    return true;
  }

  private boolean cobraTvFocusTargetCurrent(View target){
    if(target==null||!isCobraAsyncAlive()||!target.isAttachedToWindow()||target.getWindowToken()==null||
        !target.isShown()||!target.isEnabled()||!target.isFocusable())return false;
    View modal=cobraTvTransientRoot();
    if(modal!=null)return target==modal||cobraTvViewInside(modal,target);
    if(mCobraTvDrawerPanel!=null&&mCobraTvDrawerPanel.isAttachedToWindow())
      return target==mCobraTvDrawerPanel||cobraTvViewInside(mCobraTvDrawerPanel,target);
    if(mPlayerOverlay!=null&&mPlayerOverlay.isAttachedToWindow())return cobraTvViewInside(mPlayerOverlay,target)||target==mPlayerOverlay;
    if(mMultiOverlay!=null&&mMultiOverlay.isAttachedToWindow())return cobraTvViewInside(mMultiOverlay,target)||target==mMultiOverlay;
    return true;
  }

  private void cobraReleaseVodTrimTree(View view){
    if(view==null)return;
    mCobraVodTrimRoles.remove(view);
    if(view instanceof android.view.ViewGroup){android.view.ViewGroup group=(android.view.ViewGroup)view;
      for(int i=0;i<group.getChildCount();i++)cobraReleaseVodTrimTree(group.getChildAt(i));}
  }

  private String cobraTvActualPlaybackState(ExoPlayer player){
    if(player==null)return "";
    if(player.getPlayerError()!=null)return "UNAVAILABLE";
    if(player.isPlaying())return "PLAYING";
    if(!player.getPlayWhenReady())return "PAUSED";
    if(player.getPlaybackState()==Player.STATE_BUFFERING)return "BUFFERING";
    if(player.getPlaybackState()==Player.STATE_ENDED)return "ENDED";
    return "WAITING";
  }

'''
once('  @Override\n  protected void onCreate(Bundle state) {',helpers+'  @Override\n  protected void onCreate(Bundle state) {')
replace('dispatchKeyEvent',r'''  @Override public boolean dispatchKeyEvent(KeyEvent event) {
    int code=event.getKeyCode();
    if(event.getAction()==KeyEvent.ACTION_UP){
      int at=mCobraTvConsumedDownTimes.indexOfKey(code);
      if(at>=0){boolean same=mCobraTvConsumedDownTimes.valueAt(at)==event.getDownTime()&&mCobraTvConsumedDevices.get(code)==event.getDeviceId();
        mCobraTvConsumedDownTimes.delete(code);mCobraTvConsumedDevices.delete(code);if(same)return true;}
    }
    if(event.getAction()==KeyEvent.ACTION_DOWN){
      mCobraTvFocusInputGeneration++;
      if(event.getRepeatCount()>0&&cobraTvDiscreteKey(code)&&mCobraTvConsumedDownTimes.get(code,-1L)==event.getDownTime()&&mCobraTvConsumedDevices.get(code,-1)==event.getDeviceId())return true;
      if(code!=KeyEvent.KEYCODE_BACK&&mPlayerOverlay!=null&&mPlayerChrome!=null&&mPlayerChrome.getVisibility()==View.VISIBLE&&
          (code==KeyEvent.KEYCODE_DPAD_UP||code==KeyEvent.KEYCODE_DPAD_DOWN||code==KeyEvent.KEYCODE_DPAD_LEFT||code==KeyEvent.KEYCODE_DPAD_RIGHT||cobraTvDiscreteKey(code)))scheduleChromeHide();
    }
    // A modal key may never be interpreted again by the drawer, guide or player underneath it.
    if(cobraTvTransientRoot()!=null){
      if(cobraTvHandleTransientKey(event))return cobraTvRecordConsumedKey(event);
      return super.dispatchKeyEvent(event);
    }
    if(cobraTvHandleDrawerKey(event)||cobraTvHandleDirectoryKey(event)||cobraTvHandleGuideKey(event)||cobraTvHandlePlayerKey(event))
      return cobraTvRecordConsumedKey(event);
    if(event.getAction()==KeyEvent.ACTION_DOWN&&code==KeyEvent.KEYCODE_LAST_CHANNEL&&mPlayerOverlay!=null&&!mCobraPlayerLocked){
      if(!cobraOnDemandPlayer())cobraTuneLastChannel();return cobraTvRecordConsumedKey(event);
    }
    if(mCobraPlayerLocked&&mPlayerOverlay!=null&&!mInPictureInPicture){
      boolean system=code==KeyEvent.KEYCODE_VOLUME_UP||code==KeyEvent.KEYCODE_VOLUME_DOWN||code==KeyEvent.KEYCODE_VOLUME_MUTE||code==KeyEvent.KEYCODE_POWER;
      boolean unlock=getCurrentFocus()==mCobraPlayerUnlockButton&&mCobraPlayerUnlockButton!=null&&mCobraPlayerUnlockButton.getVisibility()==View.VISIBLE&&(code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER);
      if(!system&&!unlock){if(event.getAction()==KeyEvent.ACTION_DOWN)showCobraPlayerUnlockAffordance();return cobraTvRecordConsumedKey(event);}
    }
    return super.dispatchKeyEvent(event);
  }''')
replace('cobraTvHandleTransientKey',r'''  private boolean cobraTvHandleTransientKey(KeyEvent event){
    android.view.ViewGroup root=cobraTvTransientRoot();if(root==null)return false;
    if(root==mCobraMultiPicker)return cobraTvHandleMultiPickerKey(event);
    if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
    int key=event.getKeyCode();
    if(key==KeyEvent.KEYCODE_BACK)return cobraTvCloseTransient();
    if(root==mCobraActionSheet&&"tv-directory".equals(mCobraSheetKind)&&key==KeyEvent.KEYCODE_DPAD_LEFT)return closeCobraActionSheet();
    if(key==KeyEvent.KEYCODE_DPAD_UP||key==KeyEvent.KEYCODE_DPAD_DOWN||key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT)
      return cobraTvMoveTransientFocus(key);
    if((key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER)&&!cobraTvViewInside(root,getCurrentFocus())){
      cobraTvFocusFirst(root);return true;
    }
    return false;
  }''')
# Preserve normal View long-press handling; deduplicate only actions owned by the TV router.
replace('cobraTvBeginRemoteEdgeAction',r'''  private boolean cobraTvBeginRemoteEdgeAction(KeyEvent event){
    if(event==null||event.getAction()!=KeyEvent.ACTION_DOWN||event.getRepeatCount()>0)return false;
    int key=event.getKeyCode();long down=event.getDownTime();int device=event.getDeviceId();
    if(mCobraTvRemoteEdgeKey==key&&mCobraTvRemoteEdgeAt==down&&mCobraTvRemoteEdgeDevice==device)return false;
    mCobraTvRemoteEdgeAt=down;mCobraTvRemoteEdgeKey=key;mCobraTvRemoteEdgeDevice=device;mCobraTvDirectoryFocusEpoch++;
    return true;
  }''')
edit('cobraTvMoveTransientFocus','    View current=getCurrentFocus();',r'''    View current=getCurrentFocus();
    if(current!=null&&cobraTvViewInside(root,current)){
      int id=key==KeyEvent.KEYCODE_DPAD_UP?current.getNextFocusUpId():key==KeyEvent.KEYCODE_DPAD_DOWN?current.getNextFocusDownId():key==KeyEvent.KEYCODE_DPAD_LEFT?current.getNextFocusLeftId():key==KeyEvent.KEYCODE_DPAD_RIGHT?current.getNextFocusRightId():View.NO_ID;
      View linked=id==View.NO_ID?null:root.findViewById(id);
      if(linked!=current&&cobraTvFocusTargetCurrent(linked)&&linked.requestFocus()){cobraTvReveal(linked);return true;}
    }''')
edit('cobraTvMoveTransientFocus','if(next!=pos){list.setSelection(next);final int wanted=next;list.post(()->{',
     'if(next!=pos){list.setSelection(next);final int wanted=next;final android.widget.ListAdapter adapter=list.getAdapter();final int inputEpoch=mCobraTvFocusInputGeneration;list.post(()->{\n            if(root!=cobraTvTransientRoot()||!list.isAttachedToWindow()||adapter!=list.getAdapter()||inputEpoch!=mCobraTvFocusInputGeneration)return;')
edit('cobraTvPostDirectoryFocus','if(epoch!=mCobraTvDirectoryFocusEpoch||list==null||!list.isAttachedToWindow()||!list.isShown())return;',
     'if(epoch!=mCobraTvDirectoryFocusEpoch||!cobraTvFocusTargetCurrent(list))return;')
edit('cobraTvPostDirectoryFocus','if(epoch!=mCobraTvDirectoryFocusEpoch||!list.isAttachedToWindow()||!list.isShown())return;',
     'if(epoch!=mCobraTvDirectoryFocusEpoch||!cobraTvFocusTargetCurrent(list)||adapter!=list.getAdapter())return;')
edit('cobraTvCloseDrawerRestoreFocus','if(epoch!=mCobraTvDirectoryFocusEpoch)return;',
     'if(epoch!=mCobraTvDirectoryFocusEpoch||!isCobraAsyncAlive()||cobraTvTransientRoot()!=null)return;')
edit('cobraTvFocusDrawer','if(panel==null||!panel.isAttachedToWindow())return;',
     'if(panel==null||panel!=mCobraTvDrawerPanel||!panel.isAttachedToWindow()||cobraTvTransientRoot()!=null)return;')
edit('showCobraPowerMenu','    closeCobraPowerMenu();',
     '    closeCobraPowerMenu();mCobraTvPowerFocusGeneration++;mCobraTvPowerPreviousFocus=getCurrentFocus();')
replace('cobraTvClosePowerMenuRestoreFocus',r'''  private boolean cobraTvClosePowerMenuRestoreFocus(){
    final View restore=mCobraTvPowerPreviousFocus;final long ticket=mCobraNavigation.current();
    boolean closed=closeCobraPowerMenu();if(!closed)return false;
    mCobraTvPowerPreviousFocus=null;final int epoch=++mCobraTvPowerFocusGeneration;
    mMain.post(()->{
      if(!isCobraAsyncAlive()||epoch!=mCobraTvPowerFocusGeneration||!mCobraNavigation.accepts(ticket)||cobraTvTransientRoot()!=null)return;
      if(cobraTvFocusTargetCurrent(restore)&&restore.requestFocus())return;
      if(mPlayerOverlay!=null){showPlayerChromeTemporarily();cobraTvFocusPlayerPrimary();return;}
      if(mMultiOverlay!=null){cobraTvFocusCurrentMultiTile();return;}
      if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()){cobraTvRestoreGuideFocus();return;}
      if(mStage!=null&&mStage.isAttachedToWindow())cobraTvFocusFirst(mStage);
    });
    return true;
  }''')
edit('onBackPressed','    if(closeCobraActionSheet())return;',
     '    mCobraVodDetailsGeneration++;\n    if(cobraTvTransientRoot()!=null){cobraTvCloseTransient();return;}')
edit('onBackPressed','    if(mCobraMultiFullscreenActive&&mPlayerOverlay!=null){cobraReturnToMultiFromFullscreen();return;}\n', '')
edit('cobraTvFocusMultiRow','final int wanted=mCobraTvMultiRow;list.post(()->{if(list!=cobraTvMultiList())return;',
     'final int wanted=mCobraTvMultiRow;final android.widget.ListAdapter adapter=list.getAdapter();list.post(()->{if(list!=cobraTvMultiList()||adapter!=list.getAdapter()||wanted!=mCobraTvMultiRow||!list.isAttachedToWindow())return;')
replace('cobraTvActivateMultiRow',r'''  private boolean cobraTvActivateMultiRow(){
    android.widget.ListView list=cobraTvMultiList();if(list==null||list.getAdapter()==null||list.getAdapter().getCount()==0||mCobraTvMultiActivationPending)return true;
    final android.widget.ListAdapter adapter=list.getAdapter();
    final int wanted=Math.max(0,Math.min(adapter.getCount()-1,mCobraTvMultiRow));mCobraTvMultiRow=wanted;
    final long itemId=adapter.getItemId(wanted);mCobraTvMultiActivationPending=true;list.setSelection(wanted);
    list.post(()->{
      try{
        if(list!=cobraTvMultiList()||!list.isAttachedToWindow()||adapter!=list.getAdapter()||wanted>=adapter.getCount()||itemId!=adapter.getItemId(wanted))return;
        int child=wanted-list.getFirstVisiblePosition();View row=child>=0&&child<list.getChildCount()?list.getChildAt(child):null;
        list.performItemClick(row,wanted,itemId);
      }finally{mCobraTvMultiActivationPending=false;}
    });
    return true;
  }''')
edit('cobraTvChannelPlaybackState','mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED"','cobraTvActualPlaybackState(mPlayer)')
edit('cobraTvChannelPlaybackState','mCobraPreviewPlayer.getPlayWhenReady()?"PLAYING":"PAUSED"','cobraTvActualPlaybackState(mCobraPreviewPlayer)')
edit('cobraTvPlayingIndicatorKey','(mPlayer.getPlayWhenReady()?"PLAYING":"PAUSED")','cobraTvActualPlaybackState(mPlayer)')
edit('cobraTvPlayingIndicatorKey','(mCobraPreviewPlayer.getPlayWhenReady()?"PLAYING":"PAUSED")','cobraTvActualPlaybackState(mCobraPreviewPlayer)')
replace('cobraTvRecoverUnexpectedPause',r'''  private void cobraTvRecoverUnexpectedPause(ExoPlayer proof,int reason){
    if(proof==null||proof!=mPlayer||!isCobraAsyncAlive()||reason==Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST)return;
    InfinityCobraDiagnostics.record(this,"tv-player","non-user-pause-observed",
        "reason="+reason+"; state="+proof.getPlaybackState()+"; suppression="+proof.getPlaybackSuppressionReason()+"; no_auto_resume=true; no_restart=true");
    // Existing audio-focus/lifecycle policy owns legitimate recovery. Never turn a system pause
    // into a user Play request merely because a delayed timer expires.
  }''')
edit('clearStage','    mHeader.setCompoundDrawablesRelative(', '    mCobraVodDetailsGeneration++;\n    mHeader.setCompoundDrawablesRelative(')
edit('toggleCobraDrawer','  private void toggleCobraDrawer(){','  private void toggleCobraDrawer(){\n    mCobraVodDetailsGeneration++;')
replace('cobraShowVodDetails',r'''  private void cobraShowVodDetails(VodItem item){
    if(!isCobraAsyncAlive()||item==null)return;LiveSource source=sourceById(item.sourceId);if(source==null)return;
    status("Loading details…");final long ticket=mCobraNavigation.current();final int request=++mCobraVodDetailsGeneration;
    final String profile=mFeatures.activeProfileId();
    submitCobraIo(()->{
      if(request!=mCobraVodDetailsGeneration||!isCobraAsyncAlive())return;
      JSONObject info;try{info=cobraVodInfo(item);}catch(Exception ignored){info=new JSONObject();}
      final JSONObject ready=info;
      cobraPublishNavigation(ticket,()->{
        if(request!=mCobraVodDetailsGeneration||!profile.equals(mFeatures.activeProfileId())||sourceById(item.sourceId)!=source)return;
        status("Ready");cobraRenderVodDetails(item,ready);
      });
    });
  }''')
for name in ['cobraBrowseVodPerson','cobraBrowseVodCollectionMetadata']:
 t=get(name)
 assert t.count('    submitCobraIo(()->{')==1
 assert t.count('      runOnUiThread(()->{status("Ready");')==1
 t=t.replace('    submitCobraIo(()->{','    final long ticket=mCobraNavigation.current();final int request=++mCobraVodDetailsGeneration;\n    submitCobraIo(()->{',1)
 t=t.replace('      runOnUiThread(()->{status("Ready");','      cobraPublishNavigation(ticket,()->{if(request!=mCobraVodDetailsGeneration)return;status("Ready");',1)
 replace(name,t)
edit('renderVodBrowse','    final Runnable[] pending=new Runnable[1];final int[] generation={0};',r'''    final Runnable[] pending=new Runnable[1];final int[] generation={0};
    final Runnable refresh=()->{
      if(!input.isAttachedToWindow()||!content.isAttachedToWindow())return;
      String q=input.getText()==null?"":input.getText().toString().trim();
      if(q.isEmpty())cobraPopulateVodLandingDefault(content,items,series,failures);
      else cobraPopulateVodLandingSearchResults(content,input,series);
    };
    input.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){
      public void onViewAttachedToWindow(View view){}
      public void onViewDetachedFromWindow(View view){generation[0]++;if(pending[0]!=null)mMain.removeCallbacks(pending[0]);pending[0]=null;}
    });''')
edit('renderVodBrowse',r'''          String q=input.getText()==null?"":input.getText().toString().trim();
          if(q.isEmpty())cobraPopulateVodLandingDefault(content,items,series,failures);
          else cobraPopulateVodLandingSearchResults(content,input,series);''', '          pending[0]=null;refresh.run();')
edit('renderVodBrowse','      if(!submit)return false;','      if(!submit)return false;\n      if(event!=null&&(event.getAction()!=KeyEvent.ACTION_DOWN||event.getRepeatCount()>0))return true;\n      generation[0]++;if(pending[0]!=null)mMain.removeCallbacks(pending[0]);pending[0]=null;refresh.run();')
edit('renderVodBrowse',r'''      View first=content.findViewWithTag("cobra_vod_landing_search_result_0");
      if(first!=null&&first.isAttachedToWindow()&&first.isShown()&&first.isFocusable())first.requestFocus();''', r'''      final int token=generation[0];
      content.postOnAnimation(()->{
        if(token!=generation[0]||!input.isAttachedToWindow()||!content.isAttachedToWindow()||cobraTvTransientRoot()!=null)return;
        View first=content.findViewWithTag("cobra_vod_landing_search_result_0");
        if(cobraTvFocusTargetCurrent(first))first.requestFocus();
      });''')
edit('cobraPopulateVodLandingDefault','    content.removeAllViews();','    cobraReleaseVodTrimTree(content);content.removeAllViews();')
edit('cobraPopulateVodLandingSearchResults','CobraTvVodSearchResult result=cobraTvVodSearchMatches(series,query,"",35);content.removeAllViews();',
     'CobraTvVodSearchResult result=cobraTvVodSearchMatches(series,query,"",35);cobraReleaseVodTrimTree(content);content.removeAllViews();')
edit('cobraPopulateVodLandingSearchResults','lp.height=dp(isCompact()?258:288);','lp.height=android.view.ViewGroup.LayoutParams.WRAP_CONTENT;')
edit('cobraTvRenderVodSearchResults','lp.height=dp(isCompact()?258:288);','lp.height=android.view.ViewGroup.LayoutParams.WRAP_CONTENT;')
edit('cobraRenderVodCollection','dp(isCompact()?258:292)','dp(isCompact()?286:314)')
once('private final HashMap<View,String> mCobraVodTrimRoles=new HashMap<>();',
     'private final java.util.WeakHashMap<View,String> mCobraVodTrimRoles=new java.util.WeakHashMap<>();')
replace('cobraLoadVodArtwork',r'''  private void cobraLoadVodArtwork(android.widget.ImageView view,String rawUrl) {
    final String url=rawUrl==null?"":rawUrl.trim();if(url.isEmpty()||!(url.startsWith("http://")||url.startsWith("https://")))return;
    final String tag="cobra-vod-art:"+url;view.setTag(tag);android.graphics.Bitmap cached;
    synchronized(mCobraVodArtwork){cached=mCobraVodArtwork.get(url);}
    if(cached!=null&&!cached.isRecycled()){view.setImageBitmap(cached);return;}
    final java.lang.ref.WeakReference<android.widget.ImageView> destination=new java.lang.ref.WeakReference<>(view);
    submitCobraIo(()->{
      if(destination.get()==null)return;
      okhttp3.OkHttpClient client=null;okhttp3.Response response=null;
      try{
        int mode=cobraNetworkFamilyMode();CobraNetworkFamilyPolicy.NetworkTelemetry telemetry=new CobraNetworkFamilyPolicy.NetworkTelemetry(url);
        CobraNetworkFamilyPolicy.FamilyDns dns=CobraNetworkFamilyPolicy.dns(url,mode,telemetry);
        client=CobraNetworkFamilyPolicy.client(dns,telemetry,5000,8000);
        okhttp3.Request request=new okhttp3.Request.Builder().url(url).get().build();response=client.newCall(request).execute();
        if(!response.isSuccessful()||response.body()==null||response.body().contentLength()>4L*1024L*1024L)return;
        java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();byte[] buffer=new byte[8192];int size;
        try(java.io.InputStream in=response.body().byteStream()){
          while((size=in.read(buffer))!=-1){if(!isCobraAsyncAlive()||Thread.currentThread().isInterrupted()||bytes.size()+size>4*1024*1024)return;bytes.write(buffer,0,size);}
        }
        byte[] encoded=bytes.toByteArray();android.graphics.BitmapFactory.Options options=new android.graphics.BitmapFactory.Options();
        options.inJustDecodeBounds=true;android.graphics.BitmapFactory.decodeByteArray(encoded,0,encoded.length,options);
        if(options.outWidth<=0||options.outHeight<=0)return;
        options.inSampleSize=1;while(options.outWidth/options.inSampleSize>1024||options.outHeight/options.inSampleSize>1024)options.inSampleSize*=2;
        options.inJustDecodeBounds=false;final android.graphics.Bitmap ready=android.graphics.BitmapFactory.decodeByteArray(encoded,0,encoded.length,options);
        if(ready==null)return;
        synchronized(mCobraVodArtwork){
          mCobraVodArtwork.put(url,ready);long total=0L;for(android.graphics.Bitmap bitmap:mCobraVodArtwork.values())if(!bitmap.isRecycled())total+=bitmap.getAllocationByteCount();
          java.util.Iterator<Map.Entry<String,android.graphics.Bitmap>> entries=mCobraVodArtwork.entrySet().iterator();
          while(total>16L*1024L*1024L&&entries.hasNext()){android.graphics.Bitmap oldest=entries.next().getValue();if(!oldest.isRecycled())total-=oldest.getAllocationByteCount();entries.remove();}
        }
        publishCobraUi(()->{android.widget.ImageView target=destination.get();if(target!=null&&tag.equals(target.getTag())&&!ready.isRecycled())target.setImageBitmap(ready);});
      }catch(Exception ignored){}finally{
        if(response!=null)response.close();if(client!=null){client.dispatcher().cancelAll();client.connectionPool().evictAll();}
      }
    });
  }''')
once('(("PLAYING".equals(playback)?"▶ PLAYING":"Ⅱ PAUSED")+"  /  ")',
     '(("PLAYING".equals(playback)?"▶ PLAYING":"PAUSED".equals(playback)?"Ⅱ PAUSED":playback)+"  /  ")')
edit('showVodLibrary','    final long ticket=mCobraNavigation.current();',
     '    final long ticket=mCobraNavigation.current();final ArrayList<LiveSource> sources=new ArrayList<>(mSources);')
edit('showVodLibrary','for(LiveSource source:mSources){','for(LiveSource source:sources){')
for name in ['cobraBrowseVodPerson','cobraBrowseVodCollectionMetadata']:
 edit(name,'      for(VodItem candidate:candidates){',
      '      for(VodItem candidate:candidates){\n        if(!isCobraAsyncAlive()||request!=mCobraVodDetailsGeneration)return;')
edit('cobraRenderVodCollection','ScrollView scroll=new ScrollView(this);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);',
     'ScrollView scroll=new ScrollView(this);LinearLayout page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setClipChildren(false);page.setClipToPadding(false);')
edit('cobraRenderVodCollection','row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);',
     'row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setClipChildren(false);')
