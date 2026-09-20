"""Scoped 2103199 repairs to existing timeshift controls and playback intent.

No transport, network, parser, storage-window or native-engine changes.
"""
import re


def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)


def span(text, name):
    matches = list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b' + re.escape(name) + r'\s*\(', text, re.M))
    if len(matches) != 1:
        raise RuntimeError(f'method cardinality {name}={len(matches)}')
    start = matches[0].start()
    i = text.index('{', matches[0].end())
    depth = 0
    quote = None
    escaped = line = block = False
    while i < len(text):
        c = text[i]
        n = text[i+1] if i+1 < len(text) else ''
        if line:
            if c == '\n': line = False
        elif block:
            if c == '*' and n == '/': block = False; i += 1
        elif quote:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == quote: quote = None
        elif c == '/' and n == '/': line = True; i += 1
        elif c == '/' and n == '*': block = True; i += 1
        elif c in ('"', "'"): quote = c
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return start, i+1
        i += 1
    raise RuntimeError('unclosed method ' + name)


def member(text, name):
    a, b = span(text, name)
    return text[a:b]


def edit_method(text, name, old, new):
    a, b = span(text, name)
    value = once(text[a:b], old, new, name)
    return text[:a] + value + text[b:]


def transform(text):
    text = once(text,
        '      cobraRefreshProgrammeLabels();\n      cobraInspectMultiHealth();',
        '      cobraRefreshProgrammeLabels();\n      cobraUpdateLiveRewindControls();\n      cobraUpdateTimeshiftSeek();\n      cobraInspectMultiHealth();',
        'presentation clock updates existing transport controls')
    # A new SeekBar cannot own the previous view's touch gesture. Reset even if
    # Android delivers CANCEL after the old controls have been detached.
    text = edit_method(text, 'cobraBuildPlayerChrome',
        '    mCobraTimeshiftSeek=new android.widget.SeekBar(this);',
        '    mCobraTimeshiftDragging=false;mCobraTimeshiftSeek=new android.widget.SeekBar(this);')
    text = edit_method(text, 'cobraUpdateTimeshiftSeek',
        '    if(mCobraPlayerProgramProgress!=null){mCobraPlayerProgramProgress.setVisibility(View.VISIBLE);mCobraPlayerProgramProgress.setProgress(value);}\n    if(!mCobraTimeshiftDragging)mCobraTimeshiftSeek.setProgress(value);',
        '    if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setVisibility(View.VISIBLE);\n    if(!mCobraTimeshiftDragging){\n      if(mCobraPlayerProgramProgress!=null)mCobraPlayerProgramProgress.setProgress(value);\n      mCobraTimeshiftSeek.setProgress(value);\n    }')
    text = edit_method(text, 'cobraActivateLocalTimeshift',
        '    try{mCobraTimeshiftProxyPlayer=null;',
        '    final boolean requested=player.getPlayWhenReady();\n    try{mCobraTimeshiftProxyPlayer=null;')
    text = edit_method(text, 'cobraActivateLocalTimeshift',
        'cobraPrepareObserved(player,"timeshift-enter-on-demand");startCobraPlayer(player);',
        'cobraPrepareObserved(player,"timeshift-enter-on-demand");if(requested)startCobraPlayer(player);else player.pause();')
    text = edit_method(text, 'cobraRecoverLocalTimeshiftSource',
        '            failed.setMediaItem(mediaItem(session.playlistUrl()+"?cobra_recovery="+generation));\n            cobraPrepareObserved(failed,"timeshift-source-recovery");startCobraPlayer(failed);',
        '            final boolean requested=failed.getPlayWhenReady();\n            failed.setMediaItem(mediaItem(session.playlistUrl()+"?cobra_recovery="+generation));\n            cobraPrepareObserved(failed,"timeshift-source-recovery");if(requested)startCobraPlayer(failed);else failed.pause();')
    # Preserve the caller's playback intent before creating a replacement player.
    # A background-paused player may retain a pending resume request.
    text = edit_method(text, 'cobraFallbackFromLocalTimeshift',
        '      cobraStopLocalTimeshift(reason);releaseSinglePlayer();',
        '      final boolean requested=failed.getPlayWhenReady()||mBackgroundResumePlayers.containsKey(failed);\n      cobraStopLocalTimeshift(reason);releaseSinglePlayer();')
    text = edit_method(text, 'cobraFallbackFromLocalTimeshift',
        '      mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";',
        '      final boolean requested=failed.getPlayWhenReady()||mBackgroundResumePlayers.containsKey(failed);\n      mCobraPreviewPlayer=null;mCobraPreviewSessionKey="";')
    text = edit_method(text, 'cobraStartDirectSinglePlayer',
        'Channel channel,String url,String reason)',
        'Channel channel,String url,String reason,boolean requested)')
    text = edit_method(text, 'cobraStartDirectSinglePlayer',
        'cobraPrepareObserved(mPlayer,"fullscreen-direct:"+reason);startCobraPlayer(mPlayer);',
        'cobraPrepareObserved(mPlayer,"fullscreen-direct:"+reason);if(requested)startCobraPlayer(mPlayer);else mPlayer.pause();')
    text = edit_method(text, 'cobraStartDirectPreview',
        'Channel channel,String reason)',
        'Channel channel,String reason,boolean requested)')
    text = edit_method(text, 'cobraStartDirectPreview',
        '      startCobraPlayer(mCobraPreviewPlayer);cobraStartPresentationTicker();',
        '      if(requested)startCobraPlayer(mCobraPreviewPlayer);else mCobraPreviewPlayer.pause();cobraStartPresentationTicker();')
    calls = [
        ('cobraStartDirectPreview(channel,"normal")','cobraStartDirectPreview(channel,"normal",true)'),
        ('cobraStartDirectSinglePlayer(target,url,"normal")','cobraStartDirectSinglePlayer(target,url,"normal",true)'),
        ('cobraStartDirectSinglePlayer(channel,sourceUrl,"timeshift-live-proxy-failed")','cobraStartDirectSinglePlayer(channel,sourceUrl,"timeshift-live-proxy-failed",true)'),
        ('cobraStartDirectPreview(channel,"timeshift-live-proxy-failed")','cobraStartDirectPreview(channel,"timeshift-live-proxy-failed",true)'),
        ('cobraStartDirectSinglePlayer(failedChannel,failedChannel.primaryUrl,"timeshift-transport-fallback")','cobraStartDirectSinglePlayer(failedChannel,failedChannel.primaryUrl,"timeshift-transport-fallback",requested)'),
        ('cobraStartDirectPreview(failedChannel,"timeshift-transport-fallback")','cobraStartDirectPreview(failedChannel,"timeshift-transport-fallback",requested)'),
    ]
    for old, new in calls: text = once(text, old, new, old)
    return text
