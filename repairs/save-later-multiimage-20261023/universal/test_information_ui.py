"""Selected host checks for handoff Option B/synopsis/ZIP artifact only.

No application execution, Android emulation, native crash or shutdown claims.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
CC = HERE / 'overlay/script.infinity.commandcenter'
sys.path.insert(0, str(CC))
import information

XML = CC / 'resources/skins/Default/1080i/InfinityInformation.xml'
ARC = (b'<control type="image"><right>0</right><top>0</top><width>62%</width><height>160</height>'
       b'<texture colordiffuse="$VAR[InfinityPaletteAccent]">infinity_browser/header_arc.png</texture></control>')


class InformationTests(unittest.TestCase):
    def test_original_complete_plot_runtime_and_cast(self):
        plot = '  First sentence.\n\n' + 'Original description paragraph. ' * 8000 + '\nLast original sentence.  '
        entry = dict(title='Selected title', poster='https://image.test/poster.jpg',
                     information=dict(plot=plot, duration=3635, year=2026, cast='Original Name as Original Role'))
        shown = information.presentation(entry)
        self.assertEqual(shown['synopsis'], plot)
        self.assertIn('1:00:35', shown['metadata'])
        self.assertIn('Original Name as Original Role', shown['details'])
        self.assertEqual(information.duration_text(95), '1:35')
        self.assertEqual(information.duration_text(0), '')

    def test_geometry_order_bounds_and_poster_aspect_across_fold_sizes(self):
        for pw, ph in ((1080, 2520), (2184, 1968), (2520, 1080), (1200, 1637),
                       (1226, 938), (616, 1497), (721, 1088), (1076, 444)):
            for logical in ((1920, 1080), (1080, 2400)):
                for details in (True, False):
                    with self.subTest(physical=(pw, ph), logical=logical, details=details):
                        result = information.geometry(*logical, pw, ph, details)
                        self.assertGreaterEqual(result['x'], 0)
                        self.assertGreaterEqual(result['y'], 0)
                        self.assertLessEqual(result['x'] + result['width'], logical[0] + 1)
                        self.assertLessEqual(result['y'] + result['height'], logical[1] + 1)
                        controls = result['controls']
                        for ident, (x, y, w, h) in controls.items():
                            self.assertGreaterEqual(x, 0, ident)
                            self.assertGreaterEqual(y, 0, ident)
                            self.assertGreaterEqual(w, 0, ident)
                            self.assertGreaterEqual(h, 0, ident)
                            self.assertLessEqual(x + w, result['width'] + 1, ident)
                            self.assertLessEqual(y + h, result['height'] + 1, ident)
                        self.assertLessEqual(controls[121][1] + controls[121][3], controls[126][1])
                        self.assertLessEqual(controls[126][1] + controls[126][3], controls[101][1])
                        self.assertLessEqual(controls[101][1] + controls[101][3], controls[130][1])
                        # Preserve physical poster ratio when native XML axes differ.
                        ratio = logical[1] * pw / (logical[0] * ph)
                        self.assertAlmostEqual(controls[112][3] / ratio / controls[112][2], 1.5, delta=.02)

    def test_native_scrollbars_original_poster_and_simple_buttons(self):
        xml = ET.parse(XML).getroot()
        self.assertEqual(xml.find('.//control[@id="112"]/aspectratio').text, 'keep')
        self.assertEqual(xml.find('.//control[@id="126"]/pagecontrol').text, '128')
        self.assertIsNotNone(xml.find('.//control[@id="128"]'))
        self.assertEqual(xml.find('.//control[@id="131"]/pagecontrol').text, '133')
        self.assertEqual([c.findtext('label') for c in xml.findall('.//control[@type="button"]')
                          if c.get('id') in ('101', '102')], ['Play', 'Trailer'])
        self.assertFalse(xml.findall('.//onclick'))  # Only explicit Python return actions.
        self.assertFalse(xml.findall('.//maxlines'))
        self.assertFalse(xml.findall('.//wrapmultiline'))

    def _run_dialog(self, choose, skin='skin.infinity.diggz', enabled=True):
        instances = []
        dimensions = {'System.ScreenWidth': '1080', 'System.ScreenHeight': '2520'}
        plot = 'FIRST\n' + 'Unabridged text ' * 6000 + '\nFINAL'
        entry = dict(title='Exact selected title', poster='https://example.test/poster',
                     information=dict(plot=plot, duration=5999, trailer='plugin://plugin.video.test/?id=exact'))
        xml = ET.parse(XML).getroot()
        control_types = {int(c.get('id')): c.get('type') for c in xml.findall('.//control') if c.get('id')}

        class Control:
            def __init__(self, ident): self.ident = ident; self.text = ''; self.enabled = True; self.visible = True
            def getWidth(self): return 1920
            def getHeight(self): return 1080
            def setPosition(self, x, y): self.position = (x, y)
            def setWidth(self, value): self.width = value
            def setHeight(self, value): self.height = value
            def setAnimations(self, value): self.animations = value
            def setLabel(self, value): self.text = value
            def setText(self, value): self.text = value; self.text_writes = getattr(self, 'text_writes', 0) + 1
            def setImage(self, value): self.image = value
            def setVisible(self, value): self.visible = value
            def setEnabled(self, value): self.enabled = value

        class Window:
            def __init__(self, *args): self.controls = {}; self.properties = {}; self.closed = False; instances.append(self)
            def getControl(self, ident):
                # Actual Kodi API has no Python scrollbar wrapper; regression guard.
                if control_types[ident] == 'scrollbar': raise RuntimeError('Unknown control type')
                return self.controls.setdefault(ident, Control(ident))
            def setProperty(self, name, value): self.properties[name] = value
            def setFocusId(self, ident): self.focus = ident
            def doModal(self):
                self.onInit()
                self.controls[126].scroll = 7
                self.setFocusId(128)
                old_position = self.controls[126].position
                dimensions.update({'System.ScreenWidth': '2520', 'System.ScreenHeight': '1080'})
                self.onInit()  # Existing callback delivered by exact native resize guard.
                assert self.controls[126].scroll == 7 and self.focus == 128
                assert self.controls[126].text_writes == 1
                assert self.controls[126].position != old_position
                self.onFocus(101)
                self.onAction(types.SimpleNamespace(getId=lambda: 7))
                assert self.choice == ''  # focus/ordinary input never dispatches
                self.onClick(choose)
            def close(self): self.closed = True

        modules = {
            'xbmc': types.SimpleNamespace(getSkinDir=lambda: skin,
                getInfoLabel=lambda name: dimensions[name],
                getCondVisibility=lambda value: enabled),
            'xbmcgui': types.SimpleNamespace(WindowXMLDialog=Window),
            'xbmcaddon': types.SimpleNamespace(Addon=lambda _: types.SimpleNamespace(getAddonInfo=lambda _: str(CC))),
            'xbmcvfs': types.SimpleNamespace(translatePath=lambda value: value),
        }
        with patch.dict(sys.modules, modules):
            result = information.show_information(object(), entry, resume=True)
        if instances:
            self.assertEqual(instances[0].controls[126].text, plot)
            self.assertEqual(instances[0].controls[101].text, 'Resume')
            self.assertTrue(instances[0].closed)
        return result, instances

    def test_modeled_python_control_contract_and_explicit_actions(self):
        self.assertEqual(self._run_dialog(101)[0], 'play')
        self.assertEqual(self._run_dialog(102)[0], 'trailer')
        self.assertEqual(self._run_dialog(9)[0], '')
        self.assertEqual(self._run_dialog(102, enabled=False)[0], '')
        result, windows = self._run_dialog(101, skin='skin.estuary')
        self.assertEqual((result, windows), ('', []))

    def test_no_fabricated_missing_metadata(self):
        result = information.presentation(dict(title='Verified title'))
        self.assertEqual(result['synopsis'], '')
        self.assertEqual(result['trailer'], '')
        self.assertEqual(result['details'], '')


class ZipHeaderTests(unittest.TestCase):
    def test_exact_fourteen_header_only_byte_deltas(self):
        source = os.environ.get('INFINITY_REFERENCE_SKIN')
        self.assertTrue(source, 'INFINITY_REFERENCE_SKIN must name the exact signed-reference skin ZIP')
        pins = json.loads((HERE / 'UI-PREIMAGES.json').read_text())
        self.assertEqual(len(pins), 14)
        with ZipFile(source) as archive:
            for name, expected in pins.items():
                old = archive.read(name)
                new = (HERE / 'overlay' / name).read_bytes()
                self.assertEqual(hashlib.sha256(old).hexdigest(), expected)
                self.assertEqual(old.count(ARC), 1)
                self.assertEqual(new, old.replace(ARC, b'', 1))
                tree = ET.fromstring(new)
                for ident in ('450', '451', '413', '414', '415', '9410'):
                    self.assertIsNotNone(tree.find('.//control[@id="%s"]' % ident))
                self.assertNotIn(b'header_arc.png', new)


if __name__ == '__main__':
    unittest.main(verbosity=2)
