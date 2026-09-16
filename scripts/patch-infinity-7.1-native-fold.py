from pathlib import Path
import re

root = Path('kodi')
app = root / 'xbmc/platform/android/activity/XBMCApp.cpp'
if not app.exists():
    raise SystemExit('Kodi 21.3 XBMCApp.cpp not found')

text = app.read_text()

sync_body = r'''void CXBMCApp::InfinitySyncDisplayState()
{
  // Infinity 7.1: one geometry event, one Kodi state transition.
  // Reuse Kodi's own display-mode refresh path so native window, GUI mode
  // bookkeeping and input DPI are refreshed together.
  CWinSystemAndroid* winSystemAndroid = dynamic_cast<CWinSystemAndroid*>(CServiceBroker::GetWinSystem());
  if (winSystemAndroid)
    winSystemAndroid->UpdateDisplayModes();

  m_displayChangeEvent.Set();
  m_inputHandler.setDPI(GetDPI());
}

'''

# Add the helper once, immediately before onConfigurationChanged.
marker = 'void CXBMCApp::onConfigurationChanged()\n'
if 'void CXBMCApp::InfinitySyncDisplayState()' not in text:
    if marker not in text:
        raise SystemExit('onConfigurationChanged marker not found')
    text = text.replace(marker, sync_body + marker, 1)

# Replace the two upstream no-op/fixed-window callbacks with the unified path.
text, n1 = re.subn(
    r'void CXBMCApp::onConfigurationChanged\(\)\n\{.*?\n\}',
    '''void CXBMCApp::onConfigurationChanged()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  InfinitySyncDisplayState();\n}''',
    text,
    count=1,
    flags=re.S,
)
if n1 != 1:
    raise SystemExit('Failed to patch onConfigurationChanged')

text, n2 = re.subn(
    r'void CXBMCApp::onResizeWindow\(\)\n\{.*?\n\}',
    '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  m_window.reset();\n  InfinitySyncDisplayState();\n}''',
    text,
    count=1,
    flags=re.S,
)
if n2 != 1:
    raise SystemExit('Failed to patch onResizeWindow')

app.write_text(text)

hdr = root / 'xbmc/platform/android/activity/XBMCApp.h'
h = hdr.read_text()
if 'InfinitySyncDisplayState();' not in h:
    # Keep the bridge private to CXBMCApp; upper layers trigger the existing callbacks.
    anchor = '  bool XBMC_DestroyDisplay();\n'
    if anchor not in h:
        raise SystemExit('XBMCApp.h insertion anchor not found')
    h = h.replace(anchor, '  void InfinitySyncDisplayState();\n\n' + anchor, 1)
    hdr.write_text(h)

# Static assertions against accidental drift.
check = app.read_text()
for token in (
    'void CXBMCApp::InfinitySyncDisplayState()',
    'winSystemAndroid->UpdateDisplayModes();',
    'm_displayChangeEvent.Set();',
    'm_inputHandler.setDPI(GetDPI());',
    'void CXBMCApp::onResizeWindow()',
    'void CXBMCApp::onConfigurationChanged()',
):
    if token not in check:
        raise SystemExit(f'missing expected token: {token}')

print('Infinity 7.1 native Fold synchronization patch applied to Kodi 21.3')
