"""Generate an inert review diff. Never patch the production overlay/native tree."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
NATIVE = Path('/tmp/kodi451-restored-native')
NATIVE_MAP = Path('/tmp/kodi451-restored-proof/retained-module-source/NATIVE-SOURCE-MAP.json')
NAV = 'xbmc/video/windows/GUIWindowVideoNav.cpp'
HELPER = 'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/library_navigation.py'
DRAWER = 'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml'
TARGETS = {'library-movies': 'videodb://movies/titles/', 'library-tv': 'videodb://tvshows/titles/'}

# This branch executes before the existing base-class WINDOW_INIT path. The
# request remains native: no second directory load, retry, history clearing,
# worker, persisted property or alternate playback route.
HOOK = '''#if defined(TARGET_ANDROID)
      // An explicit Infinity drawer entry opens its title root, even when
      // "return" would otherwise restore a previously retained child.
      // Other callers keep Kodi's existing return/history semantics.
      if (g_SkinInfo && g_SkinInfo->ID() == "skin.infinity.diggz" &&
          message.GetNumStringParams() == 3 &&
          message.GetStringParam(1) == "return" &&
          message.GetStringParam(2) == "infinity-library-direct" &&
          (message.GetStringParam(0) == "videodb://movies/titles/" ||
           message.GetStringParam(0) == "videodb://tvshows/titles/"))
      {
        m_vecItems->SetPath(message.GetStringParam(0));
      }
#endif

'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def candidate():
    native_map = json.loads(NATIVE_MAP.read_text())
    native = (NATIVE / NAV).read_bytes()
    assert sha(native) == native_map[NAV] == '57818436a65fe03333835d27e6ba98a82fbf00b961290997767f2103bc125eb3'
    helper = (ROOT / HELPER).read_bytes()
    drawer = (ROOT / DRAWER).read_bytes()
    assert sha(drawer) == '8a49a29ba7e3accf0c7f1bfffd55cd920752c9b11aa8a9a1c04c78572cc55300'
    n = once(native.decode(), '#include "ServiceBroker.h"\n', '#include "ServiceBroker.h"\n#include "addons/Skin.h"\n')
    n = once(n, '      if (!CGUIWindowVideoBase::OnMessage(message))\n', HOOK + '      if (!CGUIWindowVideoBase::OnMessage(message))\n')
    h = once(helper.decode(), 'def activate(xbmc, gui, path):', 'def activate(xbmc, gui, path, direct_library=False):')
    h = once(h, "    result = rpc(xbmc, 'GUI.ActivateWindow',\n                 {'window': 'videos', 'parameters': [path, 'return']})", "    parameters = [path, 'return']\n    if direct_library:\n        if path not in ('videodb://movies/titles/', 'videodb://tvshows/titles/'):\n            return False\n        parameters.append('infinity-library-direct')\n    result = rpc(xbmc, 'GUI.ActivateWindow',\n                 {'window': 'videos', 'parameters': parameters})")
    h = once(h, 'def run(action, xbmc, gui, environ=None):\n', "def run(action, xbmc, gui, environ=None):\n    if action in ('library-movies', 'library-tv'):\n        path = ('videodb://movies/titles/' if action == 'library-movies'\n                else 'videodb://tvshows/titles/')\n        return activate(xbmc, gui, path, direct_library=True)\n")
    d = drawer.decode()
    for action, target in TARGETS.items():
        d = once(d, 'ActivateWindow(Videos,%s,return)' % target,
                 'RunScript(script.infinity.commandcenter,library-navigation,%s)' % action)
    return {NAV: (native, n.encode()), HELPER: (helper, h.encode()), DRAWER: (drawer, d.encode())}


def main():
    sources = candidate()
    diff = ''.join(''.join(difflib.unified_diff(a.decode().splitlines(True), b.decode().splitlines(True),
                                             fromfile='a/' + path, tofile='b/' + path))
                   for path, (a, b) in sources.items())
    (HERE / 'UNAPPLIED-NAVIGATION.patch').write_text(diff)
    manifest = {'status': 'UNAPPLIED; no production files changed',
                'source_checkpoint': '6a26f34d',
                'files': {p: {'before_sha256': sha(a), 'proposed_sha256': sha(b)} for p, (a, b) in sources.items()},
                'patch_sha256': sha(diff.encode())}
    (HERE / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
