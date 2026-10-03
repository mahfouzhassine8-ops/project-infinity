#!/usr/bin/env python3
"""Native window-to-SurfaceView input translation; no Java/skin/player changes."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CPP = 'xbmc/platform/android/activity/AndroidTouch.cpp'
HEADER = 'xbmc/platform/android/activity/AndroidTouch.h'
JNI = 'xbmc/platform/android/activity/JNIMainActivity.cpp'
CHANGED = {CPP, HEADER, JNI}
H = lambda b: hashlib.sha256(b).hexdigest()
UPSTREAM_TOUCH = 'e8935d916dfa428c18757ee7fc3ce602ea33cab9' # Git blob, pinned Kodi 21.3
UPSTREAM_HEADER = '60c66280e707acc1b28af2c3b5b13de029e3f650'

def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def transform(name, source):
    if 'INFINITY_WINDOW_INPUT_V1' in source:
        return source
    if name == CPP:
        assert blob_sha(source.encode()) == UPSTREAM_TOUCH, 'Unreviewed touch parent'
        return (ROOT / 'AndroidTouch.cpp').read_text()
    if name == HEADER:
        assert blob_sha(source.encode()) == UPSTREAM_HEADER, 'Unreviewed touch header parent'
        source = source.replace('#include <math.h>', '#include <math.h>\n#include <cstdint>\n#include <jni.h>', 1)
        source = source.replace('  bool onTouchEvent(AInputEvent* event);',
            '  bool onTouchEvent(AInputEvent* event);\n'
            '  // INFINITY_WINDOW_INPUT_V1: publish UI-thread surface coordinates only.\n'
            '  static void RefreshInputViewport(JNIEnv* env, jobject activity);', 1)
        return source.replace('  uint32_t m_dpi = 160;',
            '  uint32_t m_dpi = 160;\n  uint64_t m_gestureViewportSerial{0};\n'
            '  bool m_gestureActive{false};\n  bool m_streamRejected{false};\n'
            '  unsigned int m_downTraceCount{0};', 1)
    assert name == JNI
    old = '''void CJNIMainActivity::_doFrame(JNIEnv *env, jobject context, jlong frameTimeNanos)
{
  (void)env;
  (void)context;
  if(m_appInstance)
    m_appInstance->doFrame(frameTimeNanos);
}'''
    new = '''void CJNIMainActivity::_doFrame(JNIEnv *env, jobject context, jlong frameTimeNanos)
{
  // INFINITY_WINDOW_INPUT_V1: this callback already runs on Android's UI thread.
  CAndroidTouch::RefreshInputViewport(env, context);
  if(m_appInstance)
    m_appInstance->doFrame(frameTimeNanos);
}'''
    assert source.count(old) == 1, 'Pinned UI frame hook differs'
    assert source.count('#include "JNIMainActivity.h"') == 1
    return source.replace('#include "JNIMainActivity.h"',
        '#include "JNIMainActivity.h"\n#include "AndroidTouch.h"', 1).replace(old, new, 1)

def snapshot(root):
    return {p.relative_to(root).as_posix(): H(p.read_bytes()) for p in root.rglob('*')
            if p.is_file() and '.git' not in p.relative_to(root).parts}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=('apply', 'verify'))
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    if args.command == 'apply':
        # This candidate layers over the reviewed text/cache repair, not a new resolver.
        assert 'INFINITY_TEXT_REFLOW_V1' in (args.source / 'xbmc/guilib/GUIListLabel.cpp').read_text()
        before = snapshot(args.source)
        entries = []
        for name in sorted(CHANGED):
            file = args.source / name
            data = file.read_bytes()
            result = transform(name, data.decode()).encode()
            assert result != data, 'Fresh application required: ' + name
            file.write_bytes(result)
            entries.append(dict(path=name, before=H(data), after=H(result)))
        after = snapshot(args.source)
        changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
        assert changed == CHANGED, sorted(changed)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        manifest = dict(schema=1, before=before, after=after,
                        changed_files=sorted(changed), unexpected_changes=[])
        args.receipt.with_name('WINDOW-INPUT-BYTE-MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        protected = {name: sha for name, sha in before.items()
                     if name not in CHANGED and (name.startswith('xbmc/') or
                         name.startswith('tools/android/packaging/xbmc/src/'))}
        receipt = dict(schema=1, candidate=2103295, source_parent=2103294,
                       recovery_parent=2103293, changed_files=entries,
                       unexpected_native_source_changes=0, protected_parent_sources=protected,
                       coordinate_owner='Android window -> actual XBMCMainView origin in window',
                       screen_global_origin_subtracted=False, runtime_resize_engine_added=False,
                       android_view_read_thread='UI Choreographer only',
                       window_reload=False, skin_changed=False, java_changed=False,
                       providers_changed=False, playback_changed=False, cobra_changed=False,
                       physical_verified=False, locked=False)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    else:
        receipt = json.loads(args.receipt.read_text())
        assert receipt['candidate'] == 2103295
        assert {entry['path'] for entry in receipt['changed_files']} == CHANGED
        for entry in receipt['changed_files']:
            data = (args.source / entry['path']).read_bytes()
            assert H(data) == entry['after'], entry['path']
            assert b'INFINITY_WINDOW_INPUT_V1' in data
        for name, sha in receipt['protected_parent_sources'].items():
            assert H((args.source / name).read_bytes()) == sha, name
    print('PASS 2103295 window-input', args.command)

if __name__ == '__main__':
    main()
