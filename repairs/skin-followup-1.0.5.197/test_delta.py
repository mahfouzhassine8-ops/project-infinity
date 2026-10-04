#!/usr/bin/env python3
import unittest
import xml.etree.ElementTree as ET
from delta import HERE, TARGET, PREIMAGE, repair, sha

ORIGINAL={TARGET:(HERE/'fixtures/AddonBrowser-196.xml').read_bytes()}
CANDIDATE=repair(ORIGINAL)


class BrowserContracts(unittest.TestCase):
    def setUp(self):
        self.old=ET.fromstring(ORIGINAL[TARGET])
        self.new=ET.fromstring(CANDIDATE[TARGET])
        self.panel=self.new.find('.//control[@id="50"]')

    def test_exact_preimage(self):
        self.assertEqual(sha(ORIGINAL[TARGET]),PREIMAGE)
        with self.assertRaises(ValueError):repair({TARGET:ORIGINAL[TARGET]+b' '})

    def test_no_font_growth_or_label_bounds_jump(self):
        rest=self.panel.find('itemlayout/control[@type="textbox"]')
        focused=self.panel.find('focusedlayout/control[@type="textbox"]')
        for field in ('font','label','left','right','top','bottom','autoscroll','textcolor'):
            self.assertEqual(rest.findtext(field),focused.findtext(field),field)
        self.assertEqual(rest.findtext('font'),'InfinitySmall')
        self.assertEqual(self.panel.find('itemlayout').attrib,self.panel.find('focusedlayout').attrib)

    def test_theme_following_surface_and_text(self):
        focus=self.panel.find('focusedlayout')
        surface=focus.find('control/texture')
        self.assertEqual(surface.get('colordiffuse'),'$VAR[InfinityPaletteSurfaceElevated]')
        self.assertEqual(focus.find('control[@type="textbox"]/textcolor').text,'$VAR[InfinityDiggzPrimaryText]')
        rim=focus.findall('control/texture')[-1]
        self.assertEqual(rim.text,'infinity_polish/focus_rim.png')
        self.assertEqual(self.new.find('.//control[@id="9096"]/focusedcolor').text,
                         '$VAR[InfinityDiggzPrimaryText]')

    def test_routes_ids_and_control_bounds_preserved(self):
        self.assertEqual(self.old.findtext('defaultcontrol'),self.new.findtext('defaultcontrol'))
        for control in self.old.findall('.//control[@id]'):
            candidate=self.new.find('.//control[@id="'+control.get('id')+'"]')
            self.assertEqual(control.attrib,candidate.attrib)
            for child in control:
                if child.tag in ('onclick','onup','ondown','onleft','onright','left','top','width','height','bottom','right'):
                    self.assertEqual(child.text,candidate.findtext(child.tag),child.tag)
        self.assertEqual(self.old.findtext('views'),self.new.findtext('views'))

    def test_no_extra_primary_or_context_actions(self):
        for tag in ('onclick','onfocus','onunfocus','onload','onunload'):
            self.assertEqual([n.text for n in self.old.iter(tag)],[n.text for n in self.new.iter(tag)])
        self.assertFalse(list(self.new.iter('onlongclick')))


if __name__=='__main__':unittest.main(verbosity=2)
