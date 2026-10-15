#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Apply a narrowly checked lifecycle delta to a COPY of verified source.

The caller must supply the complete exact input hash manifest. This is source
staging, not an APK/signing gate. The matching native wrapper is mandatory.
"""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
JAVA = Path('tools/android/packaging/xbmc/src')
MANIFEST = Path('tools/android/packaging/xbmc/AndroidManifest.xml.in')
INSTALL = Path('cmake/scripts/android/Install.cmake')
NATIVE_MAIN = Path('xbmc/platform/android/activity/android_main.cpp')
NATIVE_HEADER = NATIVE_MAIN.parent / 'InfinityNativeActivityEntry.h'
GUARD_SHA = '790209e1d00f106e8f054fcdaf3dc92f28acc59199ffa42eb6bb6aaca28b79a0'
NATIVE_MAIN_SHA = '41c8c0fc88ab335229f330d95e58ba0daf7fe05c4a0beb6d9190ffcfc8c6dd8a'
HELPERS = ('InfinityTaskLifecycleGate', 'InfinityNativeTaskEntry')
ANDROID_MANIFEST_SHA = '0e93016a3c41ce38c3f62a7aaca1e10c0ad639e03794bbbf33ac6503864210c5'
NATIVE_MANIFEST_SHA = 'df5b66fbad0bb5c9b693a72904bcd7b4a683aa64375e44900bf45870c4b85081'


def require_manifest(manifest, count, expected_digest):
    # A caller-provided subset or self-generated snapshot is not proof of the
    # complete approved baseline. Pin the historical complete file map too.
    encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    if len(manifest) != count or hashlib.sha256(encoded).hexdigest() != expected_digest:
        raise ValueError('Incomplete or unapproved source manifest')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Reviewed source anchor missing or ambiguous: ' + repr(before[:100]))
    return text.replace(before, after, 1)


def apply_android(root, expected):
    root = Path(root)
    require_manifest(expected, 264, ANDROID_MANIFEST_SHA)
    before = snapshot(root)
    if before != expected:
        raise ValueError('Not the complete exact verified Android source checkpoint')
    guard = root / JAVA / 'InfinityCloseGuardService.java.in'
    if digest(guard) != GUARD_SHA:
        raise ValueError('Not the green 5997 guard implementation')
    s = guard.read_text()
    start = s.index('  private String retireConfirmedClosedKodiTask(')
    end = s.index('  static Intent homeIntent()', start)
    original = s[start:end]
    body = once(original, '    try {\n',
        '    try (InfinityTaskLifecycleGate.Removal retirement =\n'
        '        InfinityTaskLifecycleGate.beginRemoval(getFilesDir())) {\n'
        '      if (retirement == null) return "replacement_engine_entry_or_removal_in_progress";\n')
    body = once(body, '// This is a second observation, NOT an atomic OS compare-and-remove.',
        '// The entry/removal lease remains held through task-manager removal.')
    guard.write_text(s[:start] + body + s[end:])

    main = root / JAVA / 'Main.java.in'
    s = main.read_text()
    s = once(s, '  private boolean mInfinityLaunchReady;\n',
        '  private boolean mInfinityLaunchReady;\n'
        '  private boolean mInfinityNativeEntryAttempted;\n'
        '  private boolean mInfinityNativeEntryAdmitted;\n'
        '  private boolean mInfinityNativeEntryDenied;\n'
        '  private boolean mInfinityNativeEntryRecovery;\n')
    # A rejected cold/duplicate Activity must never steal an accepted Main's
    # static ownership slot. Publish the slot only from admitted native entry.
    s = once(s, '    MainActivity = this;\n', '')
    start = s.index('    InfinityKodiShutdown.boot(this,getIntent().getStringExtra(InfinityKodiShutdown.TOKEN));')
    end = s.index('    InfinityStartupTrace.mainEvent("main.nativeLoaded");', start)
    original_initialization = s[start:end]
    initialization = once(original_initialization, '    System.loadLibrary("@APP_NAME_LC@");\n', '')
    s = s[:start] + '    System.loadLibrary("@APP_NAME_LC@");\n' + s[end:]
    method = '''  // Invoked by the matching native entry wrapper BEFORE native_app_glue.
  // Declined entry still permits NativeActivity.super.onCreate to finish but
  // starts no Kodi engine, writer, player or successful-close receipt.
  public boolean infinityPrepareNativeTask() {
    if (mInfinityNativeEntryAttempted) return false;
    mInfinityNativeEntryAttempted = true;
    mInfinityNativeEntryRecovery = InfinityNativeTaskEntry.hasFreshIntent(getIntent());
    if (!InfinityNativeTaskEntry.admit(this)) {
      mInfinityNativeEntryDenied = true;
      return false;
    }
    MainActivity = this;
''' + initialization + '''    mInfinityNativeEntryAdmitted = true;
    return true;
  }

'''
    s = once(s, '  @Override\n  public void onCreate(Bundle savedInstanceState)',
        method + '  @Override\n  public void onCreate(Bundle savedInstanceState)')
    s = once(s, '    super.onCreate(savedInstanceState);\n',
        '    super.onCreate(savedInstanceState);\n'
        '    if (!mInfinityNativeEntryAdmitted) {\n'
        '      mInfinityNativeEntryDenied = true;\n'
        '      mInfinityDestroyed = true;\n'
        '      if (MainActivity == this) MainActivity = null;\n'
        '      InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.nativeEntry.deferred");\n'
        '      InfinityNativeTaskEntry.returnToChooser(this, mInfinityNativeEntryRecovery);\n'
        '      return;\n'
        '    }\n')
    s = once(s, '    super.onNewIntent(intent);\n',
        '    super.onNewIntent(intent);\n'
        '    if (mInfinityNativeEntryDenied) {\n'
        '      setIntent(intent);\n'
        '      InfinityNativeTaskEntry.returnToChooser(this, mInfinityNativeEntryRecovery);\n'
        '      return;\n'
        '    }\n')
    for call in ('onStart()', 'onResume()', 'onConfigurationChanged(configuration)',
                 'onPictureInPictureModeChanged(active, configuration)',
                 'onMultiWindowModeChanged(active, configuration)',
                 'onWindowFocusChanged(hasFocus)',
                 'onPictureInPictureModeChanged(inPictureInPictureMode)',
                 'onMultiWindowModeChanged(inMultiWindowMode)'):
        line = '    super.' + call + ';\n'
        s = once(s, line, line + '    if (mInfinityNativeEntryDenied) return;\n')
    # No owner publication, native JNI calls, ambient mutation, TV worker
    # cancellation or Plan.completed() from a denied-creation lifecycle.
    for callback in ('onPause', 'onStop'):
        line = '  public void ' + callback + '()\n  {\n'
        s = once(s, line, line + '    if (mInfinityNativeEntryDenied) { super.' + callback + '(); return; }\n')
    s = once(s, '  public void onDestroy()\n  {\n',
        '  public void onDestroy()\n  {\n'
        '    if (mInfinityNativeEntryDenied) {\n'
        '      try { super.onDestroy(); }\n'
        '      finally { if (MainActivity == this) MainActivity = null; }\n'
        '      return;\n'
        '    }\n')
    main.write_text(s)

    entry = root / JAVA / 'InfinityKodiEntryActivity.java.in'
    s = entry.read_text()
    s = once(s, '    dispatched=true;startActivity(target);finish();',
        '    if(Main.infinityLiveActivity()==null)InfinityNativeTaskEntry.prepareFreshIntent(target);\n'
        '    dispatched=true;startActivity(target);finish();')
    s = once(s, '    super.onCreate(state);setContentView(R.layout.activity_splash);',
        '    super.onCreate(state);\n'
        '    if(!InfinityTaskLifecycleGate.retainEntry(getFilesDir())){\n'
        '      InfinityNativeTaskEntry.returnToChooser(this,true);return;\n'
        '    }\n'
        '    setContentView(R.layout.activity_splash);')
    entry.write_text(s)

    manifest = root / MANIFEST
    s = manifest.read_text()
    s = once(s, '                android:value="@APP_NAME_LC@" />',
        '                android:value="@APP_NAME_LC@" />\n'
        '            <meta-data android:name="android.app.func_name"\n'
        '                android:value="InfinityNativeActivity_onCreate" />')
    manifest.write_text(s)
    install = root / INSTALL
    s = install.read_text()
    for name in HELPERS:
        target = root / JAVA / (name + '.java.in')
        if target.exists():
            raise ValueError('New helper unexpectedly exists')
        shutil.copyfile(HERE / (name + '.java.in'), target)
        s += ('\nconfigure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/' + name + '.java.in\n'
              '               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/' + name + '.java @ONLY)\n')
    install.write_text(s)
    after = snapshot(root)
    changed = sorted(name for name in before if before[name] != after.get(name))
    added = sorted(set(after) - set(before))
    allowed = sorted([str(JAVA / (n + '.java.in')) for n in
                      ('Main', 'InfinityKodiEntryActivity', 'InfinityCloseGuardService')] +
                     [str(MANIFEST), str(INSTALL)])
    if changed != allowed or added != sorted(str(JAVA / (n + '.java.in')) for n in HELPERS):
        raise ValueError('Unexpected lifecycle transformation delta')
    return {'before': before, 'after': after, 'changed': changed, 'added': added,
            'unchanged_runtime_files': len(before) - len(changed),
            'matched_native_wrapper_required': True, 'apk_authorized': False,
            'physical_device_verified': False}


def apply_native(root, expected):
    root = Path(root)
    require_manifest(expected, 9391, NATIVE_MANIFEST_SHA)
    before = snapshot(root)
    if before != expected or digest(root / NATIVE_MAIN) != NATIVE_MAIN_SHA:
        raise ValueError('Not the complete exact 2103376 native source checkpoint')
    header = root / NATIVE_HEADER
    if header.exists():
        raise ValueError('Native entry header unexpectedly exists')
    shutil.copyfile(HERE / NATIVE_HEADER.name, header)
    main = root / NATIVE_MAIN
    main.write_text(once(main.read_text(), '#include "InfinityShutdownTrace.h"\n',
                        '#include "InfinityShutdownTrace.h"\n#include "InfinityNativeActivityEntry.h"\n'))
    after = snapshot(root)
    changed = sorted(name for name in before if before[name] != after.get(name))
    added = sorted(set(after) - set(before))
    if changed != [str(NATIVE_MAIN)] or added != [str(NATIVE_HEADER)]:
        raise ValueError('Unexpected native transformation delta')
    return {'before': before, 'after': after, 'changed': changed, 'added': added,
            'full_engine_compiled': False, 'apk_authorized': False}
