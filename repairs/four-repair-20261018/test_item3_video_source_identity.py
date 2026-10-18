#!/usr/bin/env python3
"""#3: real production C++ input method, fails closed on mismatched add-on IDs.

The existing Video Sources normal two-tap and hold matrix is left unchanged.
This host guard compiles the exact production method, reproduces the original
bad second-click on Work's prior source, and requires the correction.
It does not compile or modify Cobra, the full APK, playback or shutdown.
"""
import ast
import importlib.util
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'native_patch.py'
PREIMAGE_BLOB = 'cb5f70079e3bc38d9ef9722b158e12ad2dddd417'
GUARD = """  // INFINITY_VIDEO_SOURCES_IDENTITY_V1: Video Sources projection only.
  // Kodi's selected item and its separately supplied Addon.ID must agree.
  // Otherwise the ordinary Kodi fallback could launch a different add-on on
  // the second tap. Consume the malformed opt-in touch without launching;
  // do not change unmarked tiles, other windows, or Cobra input handling.
  if (browse && item->GetProperty("Infinity.UI.Version").asString() == "1" &&
      kind == "addon" &&
      (!safe || token != item->GetProperty("Addon.ID").asString()))
  {
    SelectItem(previous);
    m_infinityUiTapKey.clear();
    return true;
  }
"""


def literal(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(x, ast.Name) and x.id == name for x in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError('Missing pinned native source: ' + name)


def compile_run(source, test):
    with tempfile.TemporaryDirectory() as tmp:
        cpp = Path(tmp) / 'test.cpp'
        exe = Path(tmp) / 'test'
        cpp.write_text(source + test)
        subprocess.run(['g++','-std=c++17','-O0','-Wall','-Wextra',
                        '-Werror', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


OLD_CASE = r"""
int main()
{
  CGUIBaseContainer c;
  c.m_items = {make("addon", "plugin.video.left"),
               make("addon", "plugin.video.right")};
  c.m_items[1]->p["Addon.ID"] = {"plugin.video.unrelated"};
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.selected == 1 && c.clicks == 0);
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 1); // confirmed original wrong-add-on activation path
}
"""

NEW_CASE = r"""
int main()
{
  CGUIBaseContainer c;
  c.m_items = {make("addon", "plugin.video.left"),
               make("addon", "plugin.video.right")};
  auto original = c.m_items[1];
  original->p["Addon.ID"] = {"plugin.video.unrelated"};
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.selected == 0 && c.clicks == 0);
  assert(c.m_infinityUiTapKey.empty());
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 0 && c.selected == 0);
  assert(c.OnInfinityUiTouch(160,50,true));
  assert(c.clicks == 0);
  assert(CServiceBroker::GetAppMessenger()->calls.empty());
  original->p["Addon.ID"] = {"plugin.video.right"};
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.selected == 1 && c.clicks == 0);
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 1 && c.last == 1);

  // If the identity changed AFTER arming, second tap cannot open a wrong ID.
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 1);
  original->p["Addon.ID"] = {"plugin.video.changed"};
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 1 && c.m_infinityUiTapKey.empty());
  original->p["Addon.ID"] = {"plugin.video.right"};
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 1);
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.clicks == 2 && c.last == 1);

  // An unsafe opt-in token must not fall through into Kodi's one-tap launch.
  auto bad = make("addon", "plugin.video.ok");
  bad->p["Infinity.UI.Token"] = {"bad),Quit("};
  c.m_items[1] = bad; c.selected = 0;
  assert(c.OnInfinityUiTouch(160,50,false));
  assert(c.selected == 0 && c.clicks == 2);

  // Original nonopt-in tiles retain original Kodi routing (no swallowing).
  bad->p["Infinity.UI.Version"] = {""};
  assert(!c.OnInfinityUiTouch(160,50,false));

  // Unrelated windows and Cobra-specific surfaces remain outside the path.
  c.parentID = 19999; c.id = 50;
  assert(!c.OnInfinityUiTouch(60,50,false));

  // Original opt-in Continue Playing and popup paths remain unchanged.
  c.parentID = WINDOW_HOME; c.id = 8830; c.selected = 0;
  c.m_items = {make("resume", std::string(64,'a'))};
  assert(!c.OnInfinityUiTouch(60,50,false));
  assert(c.OnInfinityUiTouch(60,50,true));
  assert(CServiceBroker::GetAppMessenger()->calls.back() ==
         "RunScript(script.infinity.uirepair,resume,"+std::string(64,'a')+")");
}
"""


def main():
    original = subprocess.check_output([
        'git','cat-file','blob',PREIMAGE_BLOB], cwd=HERE.parents[1]).decode()
    current = SOURCE.read_text()
    assert '  if (item->GetProperty("Infinity.UI.Version")' in literal(original, 'METHOD')
    assert current.count(GUARD) == 1
    assert current.replace(GUARD, '', 1) == original, (
        'Out-of-scope shared input modification or protected preimage mismatch')
    assert literal(current, 'DISPATCH') == literal(original, 'DISPATCH')
    assert literal(current, 'INFO') == literal(original, 'INFO')
    assert literal(current, 'FILES') == literal(original, 'FILES')
    assert 'const bool browse = GetParentID() == WINDOW_HOME + 1193 && GetID() == 50;' in literal(current, 'METHOD')
    ordinary = __import__('test_native')
    compile_run(ordinary.HARNESS + literal(original,'METHOD'), OLD_CASE)
    compile_run(ordinary.HARNESS + literal(current,'METHOD'), NEW_CASE)
    print('ITEM 3 PASS: prior wrong-ID click reproduced; corrected ID-check'
          ' blocks wrong launch/hold; original Video Sources/Continue'
          ' scope and Kodi/Cobra fallthrough unchanged')


if __name__ == '__main__':
    main()
