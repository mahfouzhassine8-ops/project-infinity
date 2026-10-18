"""Exact, single-method Android 11 compatibility delta; native engine unchanged.

AndroidX documents API 30 clearing controller behavior on Window.setAttributes.
Use its legacy IMMERSIVE_STICKY compatibility mechanism only on API 30. The
bundled older AndroidX Impl30 itself still calls the affected framework API.
"""
import hashlib

MAIN = 'com/projectinfinity/kodi/Main.smali'
PREIMAGE = 'd6e3d950614bc151ccb17f5a204c30a51a0cf0102a473c0449ef3b1d29820e56'
METHOD_PREIMAGE = 'a17014b486e5f8444902ef6a6fcda8e5116ee1543b0fcea75bded479252b182f'
SIGNATURE = '.method public onResume()V'
ANCHOR = '''    invoke-static {v2, v3}, Lcom/projectinfinity/kodi/Main$$ExternalSyntheticApiModelOutline0;->m(Landroid/view/WindowInsetsController;I)V

    goto :goto_0'''
INSERT = '''    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v4, 0x1e

    if-ne v2, v4, :cond_5

    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mDecorView:Landroid/view/View;

    invoke-virtual {v2}, Landroid/view/View;->getSystemUiVisibility()I

    move-result v4

    and-int/lit16 v4, v4, -0x801

    or-int/lit16 v4, v4, 0x1000

    invoke-virtual {v2, v4}, Landroid/view/View;->setSystemUiVisibility(I)V

'''

# Equivalent Java addition immediately after the existing controller behavior
# call, inside its non-null guard. Existing APK source owners stay protected;
# the package builder applies only these instructions to the verified preimage.
JAVA_ADDITION = '''        if (Build.VERSION.SDK_INT == 30)
        {
          int flags = mDecorView.getSystemUiVisibility();
          mDecorView.setSystemUiVisibility(
              (flags & ~View.SYSTEM_UI_FLAG_IMMERSIVE) | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }
'''

def apply(text):
    assert hashlib.sha256(text.encode()).hexdigest() == PREIMAGE, 'Main bytecode preimage differs'
    start = text.index(SIGNATURE)
    end = text.index('.end method', start) + len('.end method')
    method = text[start:end]
    assert hashlib.sha256(method.encode()).hexdigest() == METHOD_PREIMAGE
    assert method.count(ANCHOR) == 1 and '.registers 9' in method
    # v2 and v4 are dead here; v2 is overwritten by mDelayedIntents after the
    # existing merge label. No register, label, exception or lifecycle changes.
    assert ':goto_0\n    iget-object v2, p0, Lcom/projectinfinity/kodi/Main;->mDelayedIntents:' in method
    changed = method.replace(ANCHOR, ANCHOR.replace('    goto :goto_0', INSERT + '    goto :goto_0'))
    assert changed.replace(INSERT, '', 1) == method
    return text[:start] + changed + text[end:]
