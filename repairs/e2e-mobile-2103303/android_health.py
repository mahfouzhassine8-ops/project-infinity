"""Wire the bounded observer to the native activity only; chooser delay is not a freeze."""
from pathlib import Path
import shutil
from native_controls import once
HERE=Path(__file__).resolve().parent

def apply(root):
    java=root/'tools/android/packaging/xbmc/src'
    shutil.copy2(HERE/'InfinityResponsiveness.java.in',java/'InfinityResponsiveness.java.in')
    p=root/'cmake/scripts/android/Install.cmake';s=p.read_text()
    p.write_text(once(s,'                  src/InfinityAndroidKeyboard.java',
                         '                  src/InfinityAndroidKeyboard.java\n                  src/InfinityResponsiveness.java'))
    p=java/'Main.java.in';s=p.read_text()
    s=once(s,'  native void _doFrame(long frameTimeNanos);',
        '  native void _doFrame(long frameTimeNanos);\n  static native long[] _infinityHeartbeat();\n  private InfinityResponsiveness mInfinityResponsiveness;')
    s=once(s,'    InfinityStartupTrace.mainEvent("main.afterSuper");',
        '    InfinityStartupTrace.mainEvent("main.afterSuper");\n    mInfinityResponsiveness = new InfinityResponsiveness(this, Main::_infinityHeartbeat);')
    s=once(s,'    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onResume");',
        '    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onResume");\n    if (mInfinityResponsiveness != null) mInfinityResponsiveness.resume();')
    s=once(s,'    infinityTraceWindow("main.pause");',
        '    infinityTraceWindow("main.pause");\n    if (mInfinityResponsiveness != null) mInfinityResponsiveness.pause();')
    s=once(s,'    InfinityStartupTrace.mainEvent("main.destroy");',
        '    InfinityStartupTrace.mainEvent("main.destroy");\n    if (mInfinityResponsiveness != null) mInfinityResponsiveness.close();\n    mInfinityResponsiveness = null;')
    # Completion is only recorded when Android's native destruction returned successfully.
    s=once(s,'    try { super.onDestroy(); }','''    try {
      super.onDestroy();
      mInfinityExitPlan.completed();
      InfinityExitCompletion.record(this, "exit.afterNativeDestroy.returned");
    }''')
    s=once(s,'      mInfinityExitPlan.completed();\n      InfinityExitCompletion.record(this, "exit.afterNativeDestroy");','')
    p.write_text(s)
    p=java/'Splash.java.in';s=p.read_text()
    s=once(s,'InfinityExitCompletion.report(this)+"\\n"+trace',
        'InfinityExitCompletion.report(this)+"\\n"+InfinityResponsiveness.report(this)+"\\n"+trace')
    p.write_text(s)
