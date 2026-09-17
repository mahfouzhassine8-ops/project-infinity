#!/usr/bin/env python3
"""Prepare a source-only drawer delta over the exact passing 2103157 Activity.

Never mutates the input, historical recipes, source receipts, APKs, or versions.
Apply AFTER reconstructing 2103157, BEFORE future candidate promotion/compilation.
A future integration must record the resulting hash in its source receipt.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

BASE_COMMIT = '7d95f8dd1696e340bde82cb73ce4e04a0bc2ac98'
BASE_SHA256 = 'b5d25a639b0c2eb09cf2503b5af40f4d9c5ed4545db9406e8bc7413ef0aa2943'
OLD = '''    TextView layout=cobraText("VIEW MODES",cobraModeColor("muted"),10);layout.setLetterSpacing(.13f);layout.setPadding(dp(12),0,0,0);items.addView(layout,new LinearLayout.LayoutParams(-1,dp(38)));
    for(String mode:CobraModeLayout.MODES){final String key=mode;Button b=cobraTextButton(cobraModeName(mode),dark,()->{closeCobraExperienceDrawer();cobraSwitchMode(key);});b.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);b.setPadding(dp(18),0,dp(12),0);b.setSelected(mode.equals(mCobraGuideStyle));items.addView(b,new LinearLayout.LayoutParams(-1,dp(48)));}
'''
NEW = '''    // Drawer navigation stays compact; reveal the existing five-mode chooser on demand.
    LinearLayout view=cobraSheetRow("multi","View","Current: "+cobraModeName(mCobraGuideStyle),false,dark,()->{
      closeCobraExperienceDrawer();
      showCobraViewModeMenu();
    });
    view.setTag("cobra_drawer_view");
    TextView chevron=cobraText("\\u203a",cobraModeColor("muted"),22);
    chevron.setGravity(Gravity.CENTER);
    chevron.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
    view.addView(chevron,new LinearLayout.LayoutParams(dp(24),-1));
    items.addView(view,new LinearLayout.LayoutParams(-1,-2));
'''

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch(before: bytes) -> bytes:
    if sha256(before) != BASE_SHA256:
        raise ValueError('Expected exact passing 2103157 Activity; refusing unknown or already patched source')
    old, new = OLD.encode(), NEW.encode()
    if before.count(old) != 1:
        raise ValueError('Expected one direct-mode drawer section')
    start = before.index(old)
    after = before[:start] + new + before[start + len(old):]
    if after[:start] != before[:start] or after[start + len(new):] != before[start + len(old):]:
        raise ValueError('Unexpected change outside drawer section')
    return after


def prepare(source: Path, output: Path, rollback: Path) -> dict:
    source, output, rollback = source.resolve(), output.resolve(), rollback.resolve()
    if source == output or output.exists() or rollback.exists():
        raise ValueError('Output and rollback must be new paths; input is never overwritten')
    if output.is_relative_to(rollback) or rollback.is_relative_to(output):
        raise ValueError('Output and rollback paths must be separate')
    before = source.read_bytes()
    after = patch(before)  # Fail closed BEFORE writing anything.
    rollback.mkdir(parents=True, exist_ok=False)
    (rollback / 'InfinityLiveActivity-2103157.java.in').write_bytes(before)
    (rollback / 'SHA256SUMS').write_text(BASE_SHA256 + '  InfinityLiveActivity-2103157.java.in\n')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(after)
    report = {
        'base_commit': BASE_COMMIT, 'base_version_code': 2103157,
        'before_sha256': BASE_SHA256, 'after_sha256': sha256(after),
        'changed_method': 'toggleCobraDrawer', 'untargeted_bytes_preserved': True,
        'input_modified': False, 'native_modified': False, 'apk_built': False,
        'android_view_tests_run': False, 'device_verified': False, 'official': False,
        'integration': 'Apply after exact 2103157 reconstruction, then update the future candidate source receipt and run existing release gates.',
    }
    output.with_name(output.name + '.receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    output.with_name(output.name + '.diff').write_text(''.join(difflib.unified_diff(
        before.decode().splitlines(True), after.decode().splitlines(True),
        fromfile='2103157/InfinityLiveActivity.java.in', tofile='drawer-view/InfinityLiveActivity.java.in')))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rollback', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = prepare(args.input, args.output, args.rollback)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
