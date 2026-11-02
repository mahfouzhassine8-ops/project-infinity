package com.projectinfinity.kodi;

import android.content.Intent;
import android.net.Uri;
import java.util.UUID;
import java.util.WeakHashMap;

/** Retire superseded local-video requests before JNI; never owns Kodi UI/readiness. */
public final class InfinityExternalVideoIntents {
  private InfinityExternalVideoIntents() {}
  private static final String KEY="com.projectinfinity.kodi.external_video_ticket";
  private static final WeakHashMap<Main,State> OWNERS=new WeakHashMap<>();
  private static final class State {
    State() {}
    final String nonce=UUID.randomUUID().toString();
    long generation;
    boolean delivered;
    String ticket(){return nonce+":"+generation;}
  }
  private static boolean localVideo(Intent i) {
    if(i==null || !Intent.ACTION_VIEW.equals(i.getAction()))return false;
    Uri uri=i.getData();String type=i.getType();
    return uri!=null && ("content".equals(uri.getScheme()) || "file".equals(uri.getScheme()))
        && type!=null && type.startsWith("video/");
  }
  /** Called once at acceptance, before existing copy/queue/immediate branching. */
  public static Intent accept(Main owner,Intent input) {
    if(!localVideo(input))return input;
    State state=OWNERS.get(owner);
    if(state==null){state=new State();OWNERS.put(owner,state);}
    state.generation++;state.delivered=false;
    Intent copy=new Intent(input);copy.putExtra(KEY,state.ticket());return copy;
  }
  /** Existing caller retains pause/destruction/exit checks and native exception policy. */
  public static void dispatch(Main owner,Intent input) {
    if(!localVideo(input)){owner._onNewIntent(input);return;}
    State state=OWNERS.get(owner);String ticket=input.getStringExtra(KEY);
    // An unstamped legacy route retains its original semantics.
    if(ticket==null){owner._onNewIntent(input);return;}
    if(state==null || !state.ticket().equals(ticket) || state.delivered)return;
    state.delivered=true;
    Intent clean=new Intent(input);clean.removeExtra(KEY);owner._onNewIntent(clean);
  }
}
