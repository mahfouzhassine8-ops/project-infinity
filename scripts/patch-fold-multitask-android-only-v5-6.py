from pathlib import Path
import re, runpy

# Start with the known v5.5 Android-only PiP patch.
runpy.run_path('scripts/patch-pip-android-only-v5-5.py', run_name='__main__')

root = Path('/tmp/decoded')
manifest = root / 'AndroidManifest.xml'
s = manifest.read_text()

# Add foldable size-change capability metadata inside Infinity's Main activity.
pat = r'(<activity\b[^>]*android:name="com\.projectinfinity\.kodi\.Main"[^>]*>)'
m = re.search(pat, s)
if not m:
    raise SystemExit('Main activity not found')
meta = '<meta-data android:name="android.supports_size_changes" android:value="true" />'
if meta not in s:
    s = s[:m.end()] + '\n        ' + meta + s[m.end():]
manifest.write_text(s)

# Locate Main.smali.
main = None
for d in root.glob('smali*'):
    cand = d / 'com/projectinfinity/kodi/Main.smali'
    if cand.exists():
        main = cand
        break
if main is None:
    raise SystemExit('Main.smali not found')
t = main.read_text()

# Helper: unlock SurfaceHolder sizing and force Android layout to the current window.
helper = r'''.method private infinityRefreshSurfaceForWindow()V
    .locals 2

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;
    if-eqz v0, :done
    invoke-virtual {v0}, Lcom/projectinfinity/kodi/XBMCMainView;->getHolder()Landroid/view/SurfaceHolder;
    move-result-object v1
    if-eqz v1, :request
    invoke-interface {v1}, Landroid/view/SurfaceHolder;->setSizeFromLayout()V
    :request
    invoke-virtual {v0}, Landroid/view/View;->requestLayout()V
    invoke-virtual {v0}, Landroid/view/View;->invalidate()V
    :done
    return-void
.end method

'''
if 'infinityRefreshSurfaceForWindow()V' not in t:
    insert_at = t.rfind('.method')
    t = t[:insert_at] + helper + t[insert_at:]

# Fold/unfold, density, orientation and other configuration changes: keep the Activity,
# then rebind the SurfaceView to the CURRENT Android window dimensions.
conf_pat = r'(?ms)^\.method public onConfigurationChanged\(Landroid/content/res/Configuration;\)V\n.*?^\.end method\n?'
conf = r'''.method public onConfigurationChanged(Landroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1}, Landroid/app/NativeActivity;->onConfigurationChanged(Landroid/content/res/Configuration;)V
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshSurfaceForWindow()V
    return-void
.end method

'''
if re.search(conf_pat, t):
    t = re.sub(conf_pat, conf, t, count=1)
else:
    insert_at = t.rfind('.method')
    t = t[:insert_at] + conf + t[insert_at:]

# Split-screen / pop-up view transitions.
multi2_pat = r'(?ms)^\.method public onMultiWindowModeChanged\(ZLandroid/content/res/Configuration;\)V\n.*?^\.end method\n?'
multi2 = r'''.method public onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    .locals 0
    invoke-super {p0, p1, p2}, Landroid/app/NativeActivity;->onMultiWindowModeChanged(ZLandroid/content/res/Configuration;)V
    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshSurfaceForWindow()V
    return-void
.end method

'''
if re.search(multi2_pat, t):
    t = re.sub(multi2_pat, multi2, t, count=1)
else:
    insert_at = t.rfind('.method')
    t = t[:insert_at] + multi2 + t[insert_at:]

# Also refresh after PiP state changes; v5.5 already unlocks the buffer there,
# this keeps one common resize path for PiP/fold/split/freeform.
pip_pat = r'(?ms)^\.method public onPictureInPictureModeChanged\(ZLandroid/content/res/Configuration;\)V\n.*?^\.end method\n?'
m = re.search(pip_pat, t)
if m and 'infinityRefreshSurfaceForWindow()V' not in m.group(0):
    body = m.group(0)
    body = body.replace('    :done\n    return-void', '    :done\n    invoke-direct {p0}, Lcom/projectinfinity/kodi/Main;->infinityRefreshSurfaceForWindow()V\n    return-void')
    t = t[:m.start()] + body + t[m.end():]

main.write_text(t)
print('Applied v5.6 Android-only Fold/Multitask layer on top of v5.5; libkodi untouched')
