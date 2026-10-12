#!/usr/bin/env python3
"""Execute the production preview admission/confirmation contract on a host compiler."""
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native'


class NativePreviewTests(unittest.TestCase):
    def test_production_admission_and_confirmation(self):
        program = r'''
#include "xbmc/dialogs/InfinityFilePreviewContracts.h"
#include <cassert>
using namespace INFINITY::FILEPREVIEW;
int main() {
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
        self.assertIn('iAction == ACTION_MOUSE_RIGHT_CLICK', source)
        self.assertIn('else if (message.GetSenderId() == CONTROL_OK)', source)
        self.assertIn('OnClick(selected);', source)
        self.assertIn('GetProperty("Infinity.FilePreview.Nonce").asString()', source)
        self.assertIn('GetProperty("Infinity.FilePreview.AcceptNonce").asString()', source)
        self.assertIn('ClearInfinityFilePreview();\n      ClearProperty("Infinity.FilePreview.NativeVersion")', source)
        self.assertEqual(source.count('Execute("RunScript(special://skin/resources/lib/infinity_file_preview.py,"'), 1)
        self.assertIn('std::to_string(GetID())', source)
        self.assertNotIn('Extract', source.split('// INFINITY_FILE_PREVIEW_V1:', 1)[1].split('void CGUIDialogFileBrowser::ClearFileItems', 1)[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
