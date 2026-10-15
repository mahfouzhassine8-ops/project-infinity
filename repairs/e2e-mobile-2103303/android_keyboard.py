"""Java half of the Android IME bridge, paired with native_keyboard.py."""
from pathlib import Path
import shutil
from native_controls import once
HERE=Path(__file__).resolve().parent

def apply(root):
    java=root/'tools/android/packaging/xbmc/src'
    shutil.copy2(HERE/'InfinityAndroidKeyboard.java.in',java/'InfinityAndroidKeyboard.java.in')
    p=root/'cmake/scripts/android/Install.cmake';s=p.read_text()
    s=once(s,'                  src/InfinityHealthExport.java',
             '                  src/InfinityHealthExport.java\n                  src/InfinityAndroidKeyboard.java')
    p.write_text(s)
    p=java/'Main.java.in';s=p.read_text()
    for method in ['onPause','onDestroy']:
        old='  public void '+method+'()\n  {'
        s=once(s,old,old+'\n    InfinityAndroidKeyboard.cancelOwner(this);')
    s=once(s,'    mInfinityWindowMode = mode | (managed ? 4 : 0);',
             '    mInfinityWindowMode = mode | (managed ? 4 : 0);\n    InfinityAndroidKeyboard.resized(this);')
    p.write_text(s)
