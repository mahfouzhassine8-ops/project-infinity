"""Change only the two deliberately clarified subtitle strings, retaining all cases."""
from pathlib import Path
import argparse
import hashlib
import json
import re


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def adapt(name, text):
    if name != 'Cobra2103201SubtitleTest.java':
        raise RuntimeError('Unreviewed inherited fixture: ' + name)
    replacements = [
        ('"No subtitle tracks available in this stream."',
         '"No subtitle tracks detected in this playback session."', 3),
        ('"English • when available"', '"Saved preference: English • when available"', 1),
    ]
    for old, new, count in replacements:
        if text.count(old) != count:
            raise RuntimeError('Expected ' + str(count) + ' subtitle-copy occurrences: ' + old)
        text = text.replace(old, new)
    return text


def main(root, out):
    # This historical build-directory name is required by the immutable 2103202
    # adapter immediately before this one. It does not set the candidate version.
    path = root / 'repair202-build/xbmc/src/test/java/com/projectinfinity/kodi/Cobra2103201SubtitleTest.java'
    before = path.read_text()
    after = adapt(path.name, before)
    names = lambda text: re.findall(r'@Test(?:\([^\n]*?\))?(?:\s*@[^\n]+)?\s+public void (\w+)\s*\(', text)
    if names(before) != names(after):
        raise RuntimeError('Inherited testcase identity changed')
    assertions = lambda text: re.findall(r'\b(assert\w+)\s*\(', text)
    if assertions(before) != assertions(after):
        raise RuntimeError('Inherited assertions changed')
    path.write_text(after)
    result = {
        'scope': 'Two explicit subtitle-copy clarifications only',
        'case_names_unchanged': True,
        'assertion_calls_unchanged': True,
        'changes': {str(path): {'before': digest(before), 'after': digest(after)}},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parsed = parser.parse_args()
    main(parsed.root, parsed.out)
