#!/usr/bin/env python3
"""Execute the production preview admission/confirmation contract on a host compiler."""
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native'


class NativePreviewTests(unittest.TestCase):
    def test_production_bridge_methods_and_property_lifecycle(self):
        source = (NATIVE / 'xbmc/dialogs/GUIDialogFileBrowser.cpp').read_text()
        methods = source.split('bool CGUIDialogFileBrowser::OpenInfinityFilePreview', 1)[1]
        methods = 'bool CGUIDialogFileBrowser::OpenInfinityFilePreview' + methods.split('void CGUIDialogFileBrowser::ClearFileItems()', 1)[0]
        prefix = r'''
#include <cmath>
#include <cassert>
#include <map>
#include <memory>
#include <string>
#include <vector>
#include "xbmc/dialogs/InfinityFilePreviewContracts.h"
struct Variant { std::string value; std::string asString() const { return value; } };
struct CFileItem {
  std::string path, label; bool m_bIsFolder{false}; long long m_dwSize{123};
  const std::string& GetPath() const { return path; }
  const std::string& GetLabel() const { return label; }
};
using CFileItemPtr = std::shared_ptr<CFileItem>;
struct CFileItemList {
  std::vector<CFileItemPtr> items;
  int Size() const { return static_cast<int>(items.size()); }
  CFileItemPtr operator[](int index) const { return items.at(index); }
};
struct View { int selected{0}; int GetSelectedItem() const { return selected; } };
struct CFile { static inline bool exists{true}; static bool Exists(const char*) { return exists; } };
struct CBuiltins {
  static inline std::vector<std::string> commands;
  static CBuiltins& GetInstance() { static CBuiltins value; return value; }
  int Execute(const std::string& command) { commands.push_back(command); return 0; }
};
class CGUIDialogFileBrowser {
public:
  bool m_infinityZipInstallContext{true};
  uint64_t m_infinityPreviewSequence{0};
  KODI::FILEPREVIEW::Request m_infinityPreviewRequest;
  CFileItemList list; CFileItemList* m_vecItems{&list}; View m_viewControl;
  std::map<std::string, std::string> properties; int clicks{0};
  // This deliberately exposes Kodi's actual property API, without a ClearProperty method.
  void SetProperty(const std::string& key, const std::string& value) { properties[key] = value; }
  Variant GetProperty(const std::string& key) const {
    auto value = properties.find(key); return {value == properties.end() ? "" : value->second};
  }
  int GetID() const { return 10126 + (1 << 16); }
  void OnClick(int index) { assert(index == m_viewControl.selected); ++clicks; }
  bool OpenInfinityFilePreview(int);
  bool ConfirmInfinityFilePreview();
  void ClearInfinityFilePreview();
};
'''
        suffix = r'''
int main() {
  CGUIDialogFileBrowser browser;
  auto first = std::make_shared<CFileItem>(); first->path = "/Download/one),RunScript(evil).ZIP"; first->label = "one";
  auto second = std::make_shared<CFileItem>(); second->path = "/Download/second.zip"; second->label = "two";
  browser.list.items = {first, second};
  assert(!browser.OpenInfinityFilePreview(0));
  assert(CBuiltins::commands.empty());
  browser.SetProperty("Infinity.FilePreview.OptIn", "v1");
  assert(browser.OpenInfinityFilePreview(0));
  assert(CBuiltins::commands.size() == 1);
  assert(CBuiltins::commands.back() == "RunScript(special://skin/resources/lib/infinity_file_preview.py,75662)");
  assert(browser.GetProperty("Infinity.FilePreview.Path").asString() == first->path);
  auto ticket = browser.GetProperty("Infinity.FilePreview.Nonce").asString();
  assert(browser.OpenInfinityFilePreview(0));
  assert(CBuiltins::commands.size() == 1);
  assert(!browser.ConfirmInfinityFilePreview());
  assert(browser.clicks == 0);
  assert(browser.GetProperty("Infinity.FilePreview.Active").asString().empty());
  assert(browser.OpenInfinityFilePreview(0));
  ticket = browser.GetProperty("Infinity.FilePreview.Nonce").asString();
  browser.SetProperty("Infinity.FilePreview.AcceptNonce", ticket);
  browser.m_viewControl.selected = 1;
  assert(!browser.ConfirmInfinityFilePreview());
  assert(browser.clicks == 0);
  browser.m_viewControl.selected = 0;
  assert(browser.OpenInfinityFilePreview(0));
  ticket = browser.GetProperty("Infinity.FilePreview.Nonce").asString();
  browser.SetProperty("Infinity.FilePreview.AcceptNonce", ticket);
  assert(browser.ConfirmInfinityFilePreview());
  assert(browser.clicks == 1);
  browser.SetProperty("Infinity.FilePreview.AcceptNonce", ticket);
  assert(!browser.ConfirmInfinityFilePreview());
  assert(browser.clicks == 1);
  assert(!browser.OpenInfinityFilePreview(-1));
  assert(!browser.OpenInfinityFilePreview(2));
  CFile::exists = false;
  assert(!browser.OpenInfinityFilePreview(0));
}
'''
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / 'bridge.cpp'
            source.write_text(prefix + methods + suffix)
            binary = directory / 'bridge'
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pedantic',
                            '-I', str(NATIVE), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_production_admission_and_confirmation(self):
        program = r'''
#include <cmath>
#include "xbmc/dialogs/InfinityFilePreviewContracts.h"
#include <cassert>
using namespace KODI::FILEPREVIEW;
int main() {
  assert(std::isinf(INFINITY));
  assert(IsZipInstallContext("*.zip", "Install from zip file", "Install from zip file"));
  assert(!IsZipInstallContext("*", "Install from zip file", "Install from zip file"));
  assert(!IsZipInstallContext("*.zip", "Choose image", "Install from zip file"));
  assert(!IsZipInstallContext("*.zip", "", ""));
  assert(CanOpen(true, true, true, "/storage/Download/example.zip"));
  assert(!CanOpen(false, true, true, "/storage/Download/example.zip"));
  assert(!CanOpen(true, false, true, "/storage/Download/example.zip"));
  assert(!CanOpen(true, true, false, "/storage/Download/example.zip"));
  assert(!CanOpen(true, true, true, ""));
  assert(!CanOpen(true, true, true, std::string(8193, 'x')));
  for (uint64_t generation = 1; generation <= 50000; ++generation) {
    Request request{generation, "/storage/Download/real.ZIP", false};
    assert(CanConfirm(request, std::to_string(generation), true, true, true, request.path, false));
    assert(!CanConfirm(request, "", true, true, true, request.path, false));
    assert(!CanConfirm(request, std::to_string(generation + 1), true, true, true, request.path, false));
    assert(!CanConfirm(request, std::to_string(generation), true, true, true, "/other.zip", false));
    assert(!CanConfirm(request, std::to_string(generation), true, true, false, request.path, false));
    assert(!CanConfirm(request, std::to_string(generation), true, true, true, request.path, true));
    request.folder = true;
    assert(!CanConfirm(request, std::to_string(generation), true, true, true, request.path, false));
    request = {};
    assert(!CanConfirm(request, "0", true, true, true, "/storage/Download/real.ZIP", false));
  }
  Request incompatible{4, "/storage/not-an-addon.apk", false};
  assert(!CanConfirm(incompatible, "4", true, true, true, incompatible.path, false));
  assert(ShouldPrimePointer(true, true, true, false));
  assert(!ShouldPrimePointer(false, true, true, false));
  assert(!ShouldPrimePointer(true, false, true, false));
  assert(!ShouldPrimePointer(true, true, false, false));
  assert(!ShouldPrimePointer(true, true, true, true));
  assert(PREVIEW_CONTROL == 9410 && CONFIRM_CONTROL == 9411);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / 'contract.cpp'
            source.write_text(program)
            binary = directory / 'contract'
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pedantic',
                            '-I', str(NATIVE), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_native_routing_keeps_source_actions_and_standard_install(self):
        source = (NATIVE / 'xbmc/dialogs/GUIDialogFileBrowser.cpp').read_text()
        action = source.split('bool CGUIDialogFileBrowser::OnAction', 1)[1].split('bool CGUIDialogFileBrowser::OnBack', 1)[0]
        self.assertLess(action.index('return OnPopupMenu(iItem);'), action.index('OpenInfinityFilePreview'))
        self.assertIn('m_viewControl.HasControl(GetFocusedControlID())', action)
        self.assertLess(action.index('ACTION_MOUSE_MOVE'), action.index('return OnPopupMenu(iItem);'))
        self.assertIn('action.GetAmount(0)', action)
        self.assertIn('action.GetAmount(1)', action)
        self.assertIn('iAction == ACTION_MOUSE_RIGHT_CLICK', source)
        self.assertIn('else if (message.GetSenderId() == CONTROL_OK)', source)
        self.assertIn('OnClick(selected);', source)
        self.assertIn('GetProperty("Infinity.FilePreview.Nonce").asString()', source)
        self.assertIn('GetProperty("Infinity.FilePreview.AcceptNonce").asString()', source)
        self.assertIn('ClearInfinityFilePreview();\n      SetProperty("Infinity.FilePreview.NativeVersion", "")', source)
        self.assertEqual(source.count('Execute("RunScript(special://skin/resources/lib/infinity_file_preview.py,"'), 1)
        self.assertIn('std::to_string(GetID())', source)
        self.assertNotIn('Extract', source.split('// INFINITY_FILE_PREVIEW_V1:', 1)[1].split('void CGUIDialogFileBrowser::ClearFileItems', 1)[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
