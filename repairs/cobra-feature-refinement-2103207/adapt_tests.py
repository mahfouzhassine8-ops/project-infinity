"""Explicit, guarded supersession of expectations changed by the user's request.

The original 665 cases run on the locked parent first. Only disposable generated
fixtures are adapted for 207; historical repository tests are never overwritten.
All original test identities remain in the new run. This is not an unchanged-test claim.
"""
from pathlib import Path
import hashlib, json

def adapt(folder, out):
    log=[]
    def edit(name, changes, reason):
        path=folder/name
        original=path.read_text(); text=original
        for old,new,count in changes:
            if text.count(old)!=count:
                raise RuntimeError(f'Fixture anchor drift: {name}: {old}: {text.count(old)} != {count}')
            text=text.replace(old,new)
        path.write_text(text)
        log.append(dict(file=name,reason=reason,before=hashlib.sha256(original.encode()).hexdigest(),after=hashlib.sha256(text.encode()).hexdigest()))
    edit('Cobra2103201SubtitleTest.java',[
        ('assertEquals("Turn subtitles off",rebuiltButton.getContentDescription());','assertEquals("Subtitles on · turn off",rebuiltButton.getContentDescription());',1),
        ('assertEquals("Turn subtitles on when available",rebuiltButton.getContentDescription());','assertEquals("No subtitle track available",rebuiltButton.getContentDescription());',1),
    ],'Actual subtitle availability/selection is now named explicitly; state assertions preserved')
    edit('Cobra2103205PresentationEffectsTest.java',[
        ('assertEquals(0f,text.getTranslationX(),0f);','assertTrue(text.getTranslationX()<0f);',1),
        ('Duration.ofMillis(1900)','Duration.ofMillis(CobraPresentationEffects.WELCOME_MS)',1),
    ],'Requested slide-out animation and 2.4-second hold replace alpha-only 2.2-second toast')
    # Keep the original 28 call scenarios, but move the explicit call-audio action
    # from transport Play to speaker Unmute. Setup playing() still starts video.
    p=folder/'Cobra2103206MediaCallsTest.java'
    old=p.read_text(); t=old
    t=t.replace('call("cobraUserPlay",s.player);','call("cobraUserUnmute",s.player);')
    t=t.replace('f.single();call("cobraUserUnmute",s.player);return s;', 'f.single();call("cobraUserPlay",s.player);return s;')
    t=t.replace('Object r=request();interrupt();call("cobraUserUnmute",s.player);', 'Object r=request();interrupt();call("cobraUserPlay",s.player);',1)
    # First explicit UI command changes, but Pause after the command stays Pause.
    marker='@Test public void optInOneTapPlayRetriesAndKeepsPlayerSurfaceChannelTimeshift()'
    start=t.index(marker); end=t.index('\n  @Test',start+1)
    t=t[:start]+t[start:end].replace('call("toggleCobraPlayerPlayPause")','call("cobraUserUnmute",s.player)')+t[end:]
    t=t.replace('Allow When Manually Resumed','Allow When Unmuted')
    t=t.replace('assertEquals("Play",row("cobra_player_play_pause").getContentDescription());','assertEquals("Pause",row("cobra_player_play_pause").getContentDescription());')
    t=t.replace('assertEquals(false,call("cobraCallResumeAvailable",s.player));','assertEquals(false,get(a,"mCobraManualCallResume"));')
    t=t.replace('call("cobraUserPlay",first.player);','call("cobraUserUnmute",first.player);')
    t=t.replace('interrupt();call("toggleCobraPreviewPlayPause");','interrupt();call("toggleCobraPreviewMute");')
    t=t.replace('call("cobraUserPlay",f.states.get(0).player);','call("cobraUserUnmute",f.states.get(0).player);')
    t=t.replace('call("cobraUserPlay",f.states.get(1).player);','call("cobraUserUnmute",f.states.get(1).player);')
    t=t.replace('PlaybackState.STATE_PAUSED,((PlaybackState)call("cobraPipPlaybackState",s.player)).getState()', 'PlaybackState.STATE_PLAYING,((PlaybackState)call("cobraPipPlaybackState",s.player)).getState()')
    t=t.replace('callback.onPlay();assertEquals(1f,s.volume,0f);','callback.onPlay();assertEquals(0f,s.volume,0f);')
    t=t.replace('assertEquals(PlaybackState.STATE_PAUSED,owner.state())','assertEquals(PlaybackState.STATE_PLAYING,owner.state())')
    t=t.replace('assertEquals(1f,s.volume,0f);assertSame(owner,get(a,"mCobraMiniOwner"));','assertEquals(0f,s.volume,0f);assertSame(owner,get(a,"mCobraMiniOwner"));')
    t=t.replace('interrupt();call("toggleCobraPlayerPlayPause");call("toggleCobraPlayerPlayPause");', 'interrupt();call("cobraUserUnmute",s.player);call("toggleCobraPlayerPlayPause");')
    if t==old or 'cobraCallResumeAvailable' in t: raise RuntimeError('Call fixture adaptation failed')
    p.write_text(t)
    log.append(dict(file=p.name,reason='Speaker replaces Play for explicit call-audio retry; actual video remains PLAYING in PiP/background; all 28 identities retained with new requested expectations',before=hashlib.sha256(old.encode()).hexdigest(),after=hashlib.sha256(t.encode()).hexdigest()))
    out.write_text(json.dumps(log,indent=2)+'\n')
