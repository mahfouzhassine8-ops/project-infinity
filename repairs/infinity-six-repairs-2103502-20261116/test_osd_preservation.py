"""Selected preservation checks for the owner's icon-only VideoOSD authorization."""
import argparse
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile

from build_osd_overlay import MEMBER, PREIMAGE, EXPECTED, enlarged


class Preservation(unittest.TestCase):
    def test_only_approved_image_bounds_differ(self):
        original, candidate = ET.fromstring(self.before), ET.fromstring(self.after)
        old_nodes, new_nodes = list(original.iter()), list(candidate.iter())
        self.assertEqual(len(old_nodes), len(new_nodes))
        changed = []
        for old, new in zip(old_nodes, new_nodes):
            self.assertEqual(old.tag, new.tag)
            self.assertEqual(old.attrib, new.attrib)
            self.assertEqual(old.tail, new.tail)
            if old.text != new.text:
                changed.append((old, new))
        self.assertEqual(len(changed), 56)
        expected = {'left': ('28', '16'), 'top': ('28', '16'), 'width': ('40', '64'), 'height': ('40', '64')}
        parent = {id(child): node for node in candidate.iter() for child in node}
        grandparent = parent
        slots = []
        for old, new in changed:
            self.assertIn(new.tag, expected)
            self.assertEqual((old.text.strip(), new.text.strip()), expected[new.tag])
            image = parent[id(new)]
            self.assertEqual(image.attrib, {'type': 'image'})
            group = grandparent[id(image)]
            button = group.find("control[@type='button']")
            self.assertIsNotNone(button)
            self.assertEqual((button.findtext('width'), button.findtext('height')), ('96', '96'))
            if new.tag == 'left':
                slots.append(int(button.get('id')))
        self.assertEqual(slots, EXPECTED)

    def test_every_interactive_control_is_identical(self):
        def controls(data):
            return [ET.tostring(c) for c in ET.fromstring(data).iter('control') if c.get('type') not in ('image', 'group', 'grouplist')]
        self.assertEqual(controls(self.before), controls(self.after))
        # Scrolling group geometry/actions are included by the full-tree comparison above.

    def test_icons_fit_original_hitboxes_and_centres(self):
        root = ET.fromstring(self.after)
        count = 0
        for group in root.iter('control'):
            button = group.find("control[@type='button']")
            if button is None or int(button.get('id', '-1')) not in EXPECTED:
                continue
            for image in group.findall("control[@type='image']"):
                x, y, w, h = (int(image.findtext(tag)) for tag in ('left', 'top', 'width', 'height'))
                self.assertEqual((x + w / 2, y + h / 2), (48, 48))
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, 96)
                self.assertLessEqual(y + h, 96)
                count += 1
        self.assertEqual(count, 14)

    def test_wrong_baseline_is_refused(self):
        with self.assertRaises(ValueError):
            enlarged(self.before.replace(b'<onclick>Seek(-30)</onclick>', b'<onclick>Seek(-10)</onclick>'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apk', required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--receipt', required=True)
    a = p.parse_args()
    with zipfile.ZipFile(a.apk) as z:
        before = z.read(MEMBER)
        legacy = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()
                  if n.startswith('assets/addons/skin.infinity.diggz/') and n.endswith('/VideoOSD.xml') and n != MEMBER}
        skin = ET.fromstring(z.read('assets/addons/skin.infinity.diggz/addon.xml'))
        resolutions = [dict(e.attrib) for e in skin.iter('res')]
    if hashlib.sha256(before).hexdigest() != PREIMAGE:
        raise SystemExit('Wrong baseline')
    after = Path(a.candidate).read_bytes()
    generated, _ = enlarged(before)
    if after != generated:
        raise SystemExit('Candidate has unapproved bytes')
    Preservation.before, Preservation.after = before, after
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Preservation))
    receipt = {'status': 'PASS_SOURCE_PRESERVATION_ONLY' if result.wasSuccessful() else 'FAIL',
               'checks': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'member': MEMBER, 'before_sha256': PREIMAGE, 'after_sha256': hashlib.sha256(after).hexdigest(),
               'permitted_edits': 'Only 56 coordinate values in fourteen noninteractive icons; no XML reserialization',
               'legacy_osd_members_unchanged': legacy, 'packaged_skin_resolution_declarations': resolutions,
               'not_verified': ['active owner profile skin root', 'Android render', 'physical Fold visual acceptance']}
    Path(a.receipt).write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
