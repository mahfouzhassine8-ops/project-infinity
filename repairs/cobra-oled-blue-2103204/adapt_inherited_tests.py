"""Explicitly adapt one obsolete entry-motion fixture precondition for 2103204.

The user-approved presentation now fades rows in place instead of translating
their touch targets. Historical tests remain immutable. Only the generated build
copy is adapted; the original testcase identity and every post-focus assertion
remain byte-identical, including stale-transform and inherited-delay cleanup.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

SOURCE_SHA256 = '6505f7ecd469ed37467668efbd0b2c621b48780267a4516f33ae9bd9218432a9'
BUILD_COPY = Path('repair202-build/xbmc/src/test/java/com/projectinfinity/kodi/Cobra2103199UiRepairTest.java')
CASE = 'focusInterruptingStaggeredEntryRestoresPositionWithoutInheritedDelay'
OLD = '''    // Restart the existing entry callback, then inject a framework focus event
    // before this late-staggered row reaches its final translation/alpha.
    call(a,"cobraAnimateChildrenIn",list);ui.frames(1);
    assertTrue("Fixture must interrupt an unfinished translation",target.getTranslationY()>0f);
'''
NEW = '''    // 2103204 keeps real entry touch rectangles stationary; interrupt its fade.
    // Then inject stale transforms explicitly so the inherited focus cleanup
    // assertions below retain their adversarial coverage rather than becoming vacuous.
    call(a,"cobraAnimateChildrenIn",list);ui.frames(1);
    assertTrue("Fixture must interrupt an unfinished entry fade",target.getAlpha()<1f);
    assertTrue("Late row still carries stagger before focus",target.animate().getStartDelay()>0L);
    assertEquals(0f,target.getTranslationY(),.01f);assertEquals(0f,target.getTranslationX(),.01f);
    assertEquals(1f,target.getScaleX(),.001f);assertEquals(1f,target.getScaleY(),.001f);
    target.setTranslationY(8f);target.setTranslationX(5f);
'''


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def case_names(text):
    return re.findall(r'@Test(?:\([^\n]*?\))?(?:\s*@[^\n]+)?\s+public void (\w+)\s*\(', text)


def adapt_text(text):
    """Accept only the exact frozen preimage or this adapter's exact postimage."""
    if digest(text) == SOURCE_SHA256:
        original = text
        state = 'adapted'
    elif text.count(NEW) == 1:
        original = text.replace(NEW, OLD, 1)
        if digest(original) != SOURCE_SHA256:
            raise RuntimeError('Adapted inherited fixture drift; historical source is not the pinned preimage')
        state = 'already_adapted'
    else:
        raise RuntimeError('Pinned inherited fixture preimage drift')
    if original.count(OLD) != 1:
        raise RuntimeError('Entry-motion precondition anchor drift')
    adapted = original.replace(OLD, NEW, 1)
    if case_names(original) != case_names(adapted) or CASE not in case_names(original):
        raise RuntimeError('Inherited testcase identity drift')
    before_prefix, before_suffix = original.split(OLD)
    after_prefix, after_suffix = adapted.split(NEW)
    if before_prefix != after_prefix or before_suffix != after_suffix:
        raise RuntimeError('Unreviewed change outside the entry-motion precondition')
    return adapted, state


def main(root, out):
    path = root / BUILD_COPY
    before = path.read_text()
    after, state = adapt_text(before)
    # Do not rewrite an already-adapted file. Repeating the preparation is safe,
    # while even whitespace drift in any unreviewed assertion is rejected.
    if after != before:
        path.write_text(after)
    result = {
        'scope': 'One entry-motion fixture precondition superseded by stationary 2103204 row fade',
        'rationale': 'Fading in place preserves touch geometry; unfinished fade and stagger remain real, '
                     'then explicit stale X/Y exercise the original focus-reset assertions',
        'status': state,
        'historical_repository_tests_modified': False,
        'case_names_unchanged': True,
        'post_focus_assertions_byte_identical': True,
        'all_bytes_outside_reviewed_precondition_unchanged': True,
        'frozen_source_sha256': SOURCE_SHA256,
        'adapted_source_sha256': digest(after),
        'input_sha256': digest(before),
        'output_sha256': digest(after),
        'case_names': case_names(after),
        'changed_testcase': CASE,
        'changes': {str(BUILD_COPY): {'before': digest(before), 'after': digest(after)}},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(main(args.root, args.out), indent=2))
