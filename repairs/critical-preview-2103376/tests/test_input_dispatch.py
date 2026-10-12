#!/usr/bin/env python3
"""Compile production input, selection and preview methods with narrow host adapters.

The old candidate must reproduce three dispatch failures. No rendering, Android
event injection, installed keymap identity or physical-device success is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
RECIPE = HERE.parent
PREVIOUS = RECIPE.parent / 'zip-preview-2103375'


def method(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == '{': depth += 1
        if source[index] == '}': depth -= 1
        if not depth: return source[start:index + 1]
    raise AssertionError(signature)


def run(kodi, report):
    current = (RECIPE / 'native/xbmc/dialogs/GUIDialogFileBrowser.cpp').read_text()
    old = (PREVIOUS / 'native/xbmc/dialogs/GUIDialogFileBrowser.cpp').read_text()
    inputs = (RECIPE / 'native/xbmc/input/InputManager.cpp').read_text()
    original_inputs = inputs.replace('#include "dialogs/GUIDialogFileBrowser.h"\n', '')
    start = original_inputs.index('      // INFINITY_ZIP_HOLD_V2:')
    end = original_inputs.index('      if (newEvent.touch.action == ACTION_TOUCH_TAP)', start)
    original_inputs = original_inputs[:start] + original_inputs[end:]
    expected = next(x['before'] for x in json.loads((RECIPE / 'native-delta.json').read_text())['files']
                    if x['file'] == 'xbmc/input/InputManager.cpp')
    assert hashlib.sha256(original_inputs.encode()).hexdigest() == expected
    window = (kodi / 'xbmc/guilib/GUIWindowManager.cpp').read_text()
    active = method(window, 'int CGUIWindowManager::GetActiveWindowOrDialog() const').replace('CGUIWindowManager::', 'WindowManager::')
    container = (kodi / 'xbmc/guilib/GUIBaseContainer.cpp').read_text()
    select = method(container, 'EVENT_RESULT CGUIBaseContainer::OnMouseEvent')
    # Execute the complete unchanged click branch, excluding unrelated scroll/gesture branches.
    select = select[:select.index('  else if')] + '  return EVENT_RESULT_UNHANDLED;\n}'
    fixture = (HERE / 'dispatch_fixture.cpp.in').read_text()
    tests = ['builtin_hold', 'scroll_selection', 'instance_optin', 'repeat_and_confirm',
             'preserve_other_input', 'source_editing', 'no_skin_contract']
    results = []
    with tempfile.TemporaryDirectory(prefix='infinity-376-dispatch-') as directory:
        directory = Path(directory)
        for label, browser, event_source in [('failed375', old, original_inputs), ('candidate376', current, inputs)]:
            bodies = []
            for signature in ['bool CGUIDialogFileBrowser::OnAction', 'void CGUIDialogFileBrowser::OnWindowLoaded',
                              'bool CGUIDialogFileBrowser::OpenInfinityFilePreview',
                              'bool CGUIDialogFileBrowser::ConfirmInfinityFilePreview',
                              'void CGUIDialogFileBrowser::ClearInfinityFilePreview']:
                bodies.append(method(browser, signature))
            if label == 'candidate376': bodies.append(method(browser, 'bool CGUIDialogFileBrowser::OnInfinityZipLongPress'))
            touch = event_source.split('    case XBMC_TOUCH:', 1)[1].split('    case XBMC_BUTTON:', 1)[0]
            bodies += [active, select, 'bool InputManager::OnEvent(const XBMC_Event& newEvent) { switch(newEvent.type) { case XBMC_TOUCH:' + touch + '} return true; }']
            source = directory / (label + '.cpp')
            source.write_text(fixture.replace('// @PRODUCTION_METHODS@', '\n\n'.join(bodies)))
            binary = directory / label
            subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pedantic',
                            '-DTEST_PARENT=' + ('1' if label == 'failed375' else '0'),
                            '-I', str(RECIPE / 'native'), '-I', str(kodi), str(source), '-o', str(binary)], check=True)
            for case in tests:
                subprocess.run([str(binary), case], check=True)
                results.append({'candidate': label, 'case': case, 'passed': True})
                print(label + ': ' + case + ' PASS')
    result = {'cases': results, 'executions': len(results), 'negative_controls_reproduced': 3,
              'physical_device_verified': False,
              'limitations': ['Host adapters replace rendering, coordinate transforms and the OS message queue.',
                             'The installed device keymap and live instance ID have not been observed.'],
              'production_inputs': {str(p.relative_to(kodi)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in [kodi / 'xbmc/guilib/GUIWindowManager.cpp', kodi / 'xbmc/guilib/GUIBaseContainer.cpp']}}
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kodi', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    run(args.kodi, args.report)
