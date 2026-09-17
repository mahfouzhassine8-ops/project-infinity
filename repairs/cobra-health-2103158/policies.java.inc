  /** Observed liveness only. No network, player or surface objects belong to this policy. */
  private static final class CobraRecoveryPolicy {
    static final long STALL_MS=12000L, GRACE_MS=20000L, COOLDOWN_MS=60000L;
    static final int MAX_REATTACHES=2;
    long previousAt=-1,position=-1,video=-1,audio=-1,surface=-1;
    long videoAt=-1,audioAt=-1,positionAt=-1,surfaceAt=-1,eligibleAt=-1,lastAttempt=-1;
    int attempts; boolean surfaceObserved; String state="not_observed";
    void suspend(){previousAt=-1;eligibleAt=-1;surfaceObserved=false;state="suspended";}
    void initialize(long now,long pos,long frames,long samples,long stamp){
      previousAt=now;eligibleAt=now;position=pos;video=frames;audio=samples;surface=stamp;
      videoAt=now;audioAt=now;positionAt=now;surfaceAt=now;surfaceObserved=false;
    }
    boolean observe(long now,boolean eligible,long pos,long frames,long samples,long stamp){
      if(!eligible||pos<0||frames<0||samples<0){suspend();return false;}
      if(previousAt<0||now<previousAt||now-previousAt>5000L||frames<video||samples<audio||pos<position||pos-position>5000L){
        initialize(now,pos,frames,samples,stamp);state="grace_period";return false;
      }
      previousAt=now;
      if(pos>position)positionAt=now;
      if(frames>video)videoAt=now;
      if(samples>audio)audioAt=now;
      if(stamp>0&&stamp!=surface){surfaceAt=now;if(surface>0)surfaceObserved=true;}
      position=pos;video=frames;audio=samples;surface=stamp;
      if(now-eligibleAt<GRACE_MS){state="grace_period";return false;}
      if(now-audioAt>2500L||now-positionAt>2500L){state="no_audio_progress_evidence";return false;}
      boolean decoderStall=now-videoAt>=STALL_MS;
      boolean surfaceStall=surfaceObserved&&stamp>0&&now-surfaceAt>=STALL_MS;
      if(!decoderStall&&!surfaceStall){state="video_progress_observed";return false;}
      if(attempts>=MAX_REATTACHES){state="automatic_limit_reached";return false;}
      if(lastAttempt>=0&&now-lastAttempt<COOLDOWN_MS){state="recovery_cooldown";return false;}
      attempts++;lastAttempt=now;
      state=surfaceStall?"surface_timestamp_stalled":"video_output_stalled";
      // Consume the attempt BEFORE external work. A throwing adapter cannot create a retry loop.
      eligibleAt=now;videoAt=now;surfaceAt=now;surfaceObserved=false;
      return true;
    }
  }

  private static final class CobraPreferencePolicy {
    static final int MAX_SAVED=12000;
    static String language(String value){
      if(value==null)return "";String v=value.trim().toLowerCase(Locale.ROOT);
      if(v.length()>35||!v.matches("[a-z]{2,3}(?:-[a-z0-9]{2,8})*")||"und".equals(v))return "";
      return v;
    }
    static int aspect(int value){return value>=-1&&value<=11?value:-1;}
    static float scale(float value){return Float.isNaN(value)||Float.isInfinite(value)?1f:Math.max(.55f,Math.min(1.8f,value));}
    static String choice(String value,String first,String second){return first.equals(value)||second.equals(value)?value:"inherit";}
    static String key(String profile,String source,String channel){
      String[] values={profile==null?"":profile,source==null?"":source,channel==null?"":channel};
      StringBuilder input=new StringBuilder("cobra-channel-v1|");for(String v:values)input.append(v.length()).append(':').append(v);
      try {byte[] hash=java.security.MessageDigest.getInstance("SHA-256").digest(input.toString().getBytes(StandardCharsets.UTF_8));
        StringBuilder out=new StringBuilder("cobra.channel.v1.");for(byte b:hash)out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();
      }catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
    }
  }
