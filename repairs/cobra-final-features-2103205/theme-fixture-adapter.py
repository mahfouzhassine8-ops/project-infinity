"""Add the explicitly requested 205 Keep Theme action to one generated UI test.

The historical test stays immutable. Its original restoration assertions stay
byte-identical. Before performing Keep, additional assertions verify that the
exact prior theme is visible only as a preview and is not committed early.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

SOURCE_SHA256 = '0a17437b2064e81df1e721ab0ef439a2d2a0aa76c26ae01dfbd4e9b708651ddb'
BUILD_COPY = Path('repair202-build/xbmc/src/test/java/com/projectinfinity/kodi/Cobra2103162ThemeRotationTest.java')
CASE = 'oneThemeSheetSwitchesToBuiltInThenBackToSameInstalledTheme'
ORIGINAL_ASSERTIONS = '''      assertTrue("The exact installed theme must be restored",await(()->CobraVisualRenderer.active.id.equals("hm-test")));
      assertFalse(CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
'''
BEFORE = '''      try {
      // 2103205 requires explicit Keep for a previously installed theme too.
      // Preview the exact generation without replacing committed global state.
      assertTrue("Installed selection must open a guarded preview",await(()->CobraPresentationSafety.isPreviewing(a)));
      CobraVisualRenderer previewRenderer=(CobraVisualRenderer)call(a,"vtheme");
      assertEquals("hm-test",previewRenderer.effective().id);
      assertEquals(installed.directory,previewRenderer.effective().directory);
      assertEquals("builtin",CobraVisualRenderer.active.id);
      assertTrue("Preview cannot commit before Keep",CobraVisualTheme.readPointer(a).optString("active","").isEmpty());
      assertEquals(installed.directory.getName(),CobraVisualTheme.readPointer(a).optString("previous",""));
      assertEquals("builtin",CobraVisualTheme.load(a).id);
      android.app.AlertDialog confirmation=org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();
      assertNotNull(confirmation);assertTrue(confirmation.isShowing());
      android.widget.Button keep=confirmation.getButton(android.app.AlertDialog.BUTTON_POSITIVE);
      assertNotNull(keep);assertEquals("Keep Theme",keep.getText().toString());assertTrue(keep.isEnabled());
      assertTrue("Choose the real native Keep action",keep.performClick());
'''
AFTER = '''      assertFalse("Keep must end the temporary preview",CobraPresentationSafety.isPreviewing(a));
      assertEquals(installed.directory.getName(),CobraVisualTheme.readPointer(a).optString("active",""));
      CobraVisualTheme coldRestored=CobraVisualTheme.load(a);
      assertEquals("hm-test",coldRestored.id);assertEquals(installed.directory,coldRestored.directory);
      assertEquals(installed.data.toString(),coldRestored.data.toString());
      }finally{CobraPresentationSafety.cancel(a,false);}
'''


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def case_names(text):
    return re.findall(r'@Test(?:\([^\n]*?\))?(?:\s*@[^\n]+)?\s+public void (\w+)\s*\(', text)


def adapt_text(text):
    inserted = BEFORE + ORIGINAL_ASSERTIONS + AFTER
    if digest(text) == SOURCE_SHA256:
        original, status = text, 'adapted'
    elif text.count(inserted) == 1:
        original, status = text.replace(inserted, ORIGINAL_ASSERTIONS, 1), 'already_adapted'
        if digest(original) != SOURCE_SHA256:
            raise RuntimeError('Adapted theme fixture drift outside approved Keep action')
    else:
        raise RuntimeError('Pinned historical theme fixture preimage drift')
    if original.count(ORIGINAL_ASSERTIONS) != 1:
        raise RuntimeError('Exact restoration assertion anchor drift')
    adapted = original.replace(ORIGINAL_ASSERTIONS, inserted, 1)
    if adapted.replace(inserted, ORIGINAL_ASSERTIONS, 1) != original:
        raise RuntimeError('Unexpected inherited fixture rewrite')
    if case_names(original) != case_names(adapted) or CASE not in case_names(original):
        raise RuntimeError('Inherited testcase identity drift')
    return adapted, status


def main(root, out):
    path = root / BUILD_COPY
    before = path.read_text()
    after, status = adapt_text(before)
    if after != before:
        path.write_text(after)
    receipt = {
        'scope': 'One generated historical UI fixture completes the explicitly required 205 theme preview/Keep workflow',
        'rationale': 'A preview must not publish committed global state; Keep is the user confirmation required before original exact-theme restoration assertions',
        'status': status,
        'historical_repository_tests_modified': False,
        'case_names_unchanged': True,
        'original_assertions_byte_identical': True,
        'changes_outside_reviewed_insertion': False,
        'frozen_source_sha256': SOURCE_SHA256,
        'input_sha256': digest(before),
        'output_sha256': digest(after),
        'case_names': case_names(after),
        'changed_testcase': CASE,
        'changes': {str(BUILD_COPY): {'before': digest(before), 'after': digest(after)}},
        'physical_device_verified': False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(main(args.root, args.out), indent=2))
