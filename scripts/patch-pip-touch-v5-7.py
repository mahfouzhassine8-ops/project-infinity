from pathlib import Path
import re, runpy

# Start from v5.6 Android-only PiP + Fold + multitasking layer.
runpy.run_path('scripts/patch-fold-multitask-android-only-v5-6.py', run_name='__main__')

root = Path('/tmp/decoded')
main = None
for d in root.glob('smali*'):
    cand = d / 'com/projectinfinity/kodi/Main.smali'
    if cand.exists():
        main = cand
        break
if main is None:
    raise SystemExit('Main.smali not found')

t = main.read_text()

# v5.5/v5.6 playback gate is blocking PiP on the real device.
# For v5.7, restore reliable manual PiP entry first so we can finally test
# the SurfaceHolder resize fix. Keep 16:9 and keep auto-PiP disabled.
leave_pat = r'(?ms)^\.method public onUserLeaveHint\(\)V\n.*?^\.end method\n?'
leave = r'''.method public onUserLeaveHint()V
    .locals 4

    invoke-super {p0}, Landroid/app/NativeActivity;->onUserLeaveHint()V

    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x1a
    if-lt v0, v1, :done

    invoke-virtual {p0}, Landroid/app/Activity;->isInPictureInPictureMode()Z
    move-result v0
    if-nez v0, :done

    new-instance v0, Landroid/app/PictureInPictureParams$Builder;
    invoke-direct {v0}, Landroid/app/PictureInPictureParams$Builder;-><init>()V
    new-instance v1, Landroid/util/Rational;
    const/16 v2, 0x10
    const/16 v3, 0x9
    invoke-direct {v1, v2, v3}, Landroid/util/Rational;-><init>(II)V
    invoke-virtual {v0, v1}, Landroid/app/PictureInPictureParams$Builder;->setAspectRatio(Landroid/util/Rational;)Landroid/app/PictureInPictureParams$Builder;
    move-result-object v0
    invoke-virtual {v0}, Landroid/app/PictureInPictureParams$Builder;->build()Landroid/app/PictureInPictureParams;
    move-result-object v1
    invoke-virtual {p0, v1}, Landroid/app/Activity;->enterPictureInPictureMode(Landroid/app/PictureInPictureParams;)Z

    :done
    return-void
.end method

'''
if re.search(leave_pat, t):
    t = re.sub(leave_pat, leave, t, count=1)
else:
    insert_at = t.rfind('.method')
    t = t[:insert_at] + leave + t[insert_at:]

# Replace the common window refresh helper with a stronger Android-side resize:
# 1) release fixed SurfaceHolder sizing
# 2) force XBMCMainView bounds to the CURRENT decor/window size
# 3) request layout + invalidate so Android's touch coordinate space follows visuals.
helper_pat = r'(?ms)^\.method private infinityRefreshSurfaceForWindow\(\)V\n.*?^\.end method\n?'
helper = r'''.method private infinityRefreshSurfaceForWindow()V
    .locals 7

    iget-object v0, p0, Lcom/projectinfinity/kodi/Main;->mMainView:Lcom/projectinfinity/kodi/XBMCMainView;
    if-eqz v0, :done

    invoke-virtual {v0}, Lcom/projectinfinity/kodi/XBMCMainView;->getHolder()Landroid/view/SurfaceHolder;
    move-result-object v1
    if-eqz v1, :bounds
    invoke-interface {v1}, Landroid/view/SurfaceHolder;->setSizeFromLayout()V

    :bounds
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v2
    if-eqz v2, :refresh
    invoke-virtual {v2}, Landroid/view/Window;->getDecorView()Landroid/view/View;
    move-result-object v3
    if-eqz v3, :refresh
    invoke-virtual {v3}, Landroid/view/View;->getWidth()I
    move-result v4
    invoke-virtual {v3}, Landroid/view/View;->getHeight()I
    move-result v5
    if-lez v4, :refresh
    if-lez v5, :refresh

    new-instance v6, Landroid/view/ViewGroup$LayoutParams;
    invoke-direct {v6, v4, v5}, Landroid/view/ViewGroup$LayoutParams;-><init>(II)V
    invoke-virtual {v0, v6}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V
    const/4 v6, 0x0
    invoke-virtual {v0, v6, v6, v4, v5}, Landroid/view/View;->layout(IIII)V

    :refresh
    invoke-virtual {v0}, Landroid/view/View;->requestLayout()V
    invoke-virtual {v0}, Landroid/view/View;->invalidate()V

    :done
    return-void
.end method

'''
if not re.search(helper_pat, t):
    raise SystemExit('v5.6 refresh helper not found')
t = re.sub(helper_pat, helper, t, count=1)

main.write_text(t)
print('Applied v5.7: restored manual PiP entry + current-window XBMCMainView touch bounds; libkodi untouched')
