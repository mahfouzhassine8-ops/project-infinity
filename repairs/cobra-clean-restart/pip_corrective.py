#!/usr/bin/env python3
"""Authorized continuation of aca973f; no rejected menu or tuning policy is imported."""
import difflib
import hashlib
import json
from pathlib import Path

RUNTIME = 'tools/android/packaging/xbmc/src/'
PREIMAGES = {
    'InfinityLiveActivity.java.in': '0abbb320d58c9eb37a024c1da48be4301cf2cd22b51a789e6a9e4279c7d8545c',
    'CobraProUi.java.in': '9efbd2802cc28d09162b0166399b4e3ed10ba94e909e54f4dbc5ade8b935aad1',
}

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def apply(source, out):
    texts = {name: (source / RUNTIME / name).read_text() for name in PREIMAGES}
    for name, expected in PREIMAGES.items():
        if sha(texts[name]) != expected:
            raise RuntimeError('Not the exact saved implementation: ' + name)
    before = dict(texts)
    changes = []
    def replace(name, method, old, new, origin):
        if texts[name].count(old) != 1:
            raise RuntimeError('Corrective preimage mismatch: ' + method)
        texts[name] = texts[name].replace(old, new, 1)
        changes.append({'file': RUNTIME + name, 'method': method, 'requirement': 2,
                        'origin': origin, 'before_sha256': sha(old), 'after_sha256': sha(new)})

    replace('CobraProUi.java.in', 'Hero constructor',
        'for(int index:new int[]{0,1,2,3,4,8,6,7,5})if(index!=8||actions.pipSupported())controlStrip.addView',
        'player[8].setLayoutParams(new LinearLayout.LayoutParams(px(c,62),-1));\n      for(int index:new int[]{0,1,2,3,4,8,6,7,5})if(index!=8||actions.pipSupported())controlStrip.addView',
        'New control initialization only; original layout loop, strip membership and eight original actions unchanged')

    replace('InfinityLiveActivity.java.in', 'CobraSix.miniPip',
        '      ExoPlayer session = mCobraPreviewPlayer;\n      if (!cobraPlaybackRequested(session)',
        '      // Selectively retained from 2103370: never promote a locked, stale, or mismatched session.\n      if (mCobraPlayerLocked || isCobraInPictureInPicture()\n          || !cobraChannelKey(mGuidePreviewChannel).equals(mCobraPreviewSessionKey)) return;\n      ExoPlayer session = mCobraPreviewPlayer;\n      if (!cobraPlaybackRequested(session)',
        '2103370 cobraRequestPictureInPicture lock/current-session identity guards; no broad audio carry or explicit paused/multi policy imported')

    for name, text in texts.items():
        (source / RUNTIME / name).write_text(text)
    receipt = {'checkpoint': 'aca973f21642c30148367baaf7ed0e0f83f079f8',
               'selective_reference': '47d9e563a6052e6ac5d90f784ad526346d93d9cf',
               'changes': changes,
               'source_sha256': {name: {'before': sha(before[name]), 'after': sha(texts[name])} for name in texts},
               'groups_runtime_modified': False, 'rejected_menu_imported': False}
    (out / 'PIP-CORRECTIVE-DELTA.json').write_text(json.dumps(receipt, indent=2) + '\n')
    patch = ''.join(''.join(difflib.unified_diff(before[n].splitlines(True), texts[n].splitlines(True),
                    'a/' + RUNTIME + n, 'b/' + RUNTIME + n)) for n in sorted(texts))
    (out / 'pip-corrective.patch').write_text(patch)
    original = out / 'extracted/shell-kodi'
    complete = ''.join(''.join(difflib.unified_diff((original/RUNTIME/n).read_text().splitlines(True),
                      texts[n].splitlines(True), 'a/' + RUNTIME + n, 'b/' + RUNTIME + n)) for n in sorted(texts))
    (out / 'changes.patch').write_text(complete)
    path = out / 'CHANGED-METHODS.json'
    inventory = json.loads(path.read_text())
    inventory['changes'].extend(changes)
    for name in texts:
        inventory['source_sha256'][name]['after'] = sha(texts[name])
    inventory['selective_pip_reference'] = receipt['selective_reference']
    path.write_text(json.dumps(inventory, indent=2) + '\n')

def prepare_tests(tests):
    path = tests / 'CobraCleanRuntimeTest.java'
    text = path.read_text()
    edits = [
        ('    assertTrue(context+" list="+get(a,"mCobraDrawerFilter")',
         '    if(list.getChildCount()==0)CobraGroupsTrace.record(context,list);\n    assertTrue(context+" list="+get(a,"mCobraDrawerFilter")'),
        ('void measure()throws Exception{f.measure(a,width,height);',
         'void measure()throws Exception{f.frames(12);'),
        ('open(mode,muted);PipPlatform.requests=0;Object origin=get(a,"mCobraGuideStyle");click(miniPip());',
         '''open(mode,muted);PipPlatform.requests=0;Object origin=get(a,"mCobraGuideStyle");
      String currentKey=(String)get(a,"mCobraPreviewSessionKey");
      put(a,"mCobraPreviewSessionKey","stale-session");call(get(a,"mCobraSix"),"miniPip");
      assertSame(state.proxy,get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayerOverlay"));assertEquals(0,PipPlatform.requests);
      put(a,"mCobraPreviewSessionKey",currentKey);put(a,"mCobraPlayerLocked",true);call(get(a,"mCobraSix"),"miniPip");
      assertSame(state.proxy,get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayerOverlay"));assertEquals(0,PipPlatform.requests);
      put(a,"mCobraPlayerLocked",false);click(miniPip());'''),
    ]
    for old, new in edits:
        if text.count(old) != 1:
            raise RuntimeError('Corrective test preimage mismatch: ' + old[:100])
        text = text.replace(old, new, 1)
    path.write_text(text)
