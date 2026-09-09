#!/usr/bin/env python3
"""Structural/logic regression tests, NOT an Android/Kodi screenshot renderer."""
from __future__ import annotations
import io
import itertools
import json
import os
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile
from PIL import ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import infinity_theme_contract as patch

APK = Path(os.environ.get('INFINITY_TEST_APK', '/mnt/data/infinity-audit-work/base-1.0.5.apk'))


def args_split(text):
    depth = 0
    for i, char in enumerate(text):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            return text[:i], text[i+1:]
    return (text,)


class Condition:
    """Evaluate only the Kodi condition subset in the audited branding variants.

    NOT a general-purpose replacement for Kodi's actual runtime evaluator.
    Unsupported expressions fail rather than silently evaluate as false.
    """
    def __init__(self, text, facts, expressions):
        self.text, self.facts, self.expressions, self.pos = text, facts, expressions, 0

    def skip(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def take(self, char):
        self.skip()
        if self.text.startswith(char, self.pos):
            self.pos += len(char)
            return True
        return False

    def run(self):
        result = self.or_expr()
        self.skip()
        if self.pos != len(self.text):
            raise ValueError('Unparsed condition: ' + self.text[self.pos:])
        return result

    def or_expr(self):
        value = self.and_expr()
        while self.take('|'):
            rhs = self.and_expr()
            value = value or rhs
        return value

    def and_expr(self):
        value = self.atom()
        while self.take('+'):
            rhs = self.atom()
            value = value and rhs
        return value

    def atom(self):
        self.skip()
        if self.take('!'):
            return not self.atom()
        if self.take('['):
            value = self.or_expr()
            if not self.take(']'):
                raise ValueError('Unclosed boolean group')
            return value
        if self.take('$EXP['):
            end = self.text.index(']', self.pos)
            name = self.text[self.pos:end]
            self.pos = end + 1
            return Condition(self.expressions[name], self.facts, self.expressions).run()
        start = self.pos
        depth = 0
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif depth == 0 and char in '+|]':
                break
            self.pos += 1
        atom = self.text[start:self.pos].strip()
        if atom.lower() in ('true', 'false'):
            return atom.lower() == 'true'
        match = re.fullmatch(r'([A-Za-z.]+)\((.*)\)', atom)
        if not match:
            raise ValueError('Unsupported atom: ' + atom)
        func, payload = match.groups()
        values = [self.facts.get(v, v) for v in args_split(payload)]
        if func == 'String.IsEmpty':
            return values[0] == ''
        if func == 'String.IsEqual':
            return str(values[0]).lower() == str(values[1]).lower()
        if func == 'Integer.IsLess':
            return int(values[0]) < int(values[1])
        if func == 'Integer.IsGreater':
            return int(values[0]) > int(values[1])
        raise ValueError('Unsupported atom: ' + atom)


def facts(policy='', theme='unknown', mode='mobile', width=658, height=1536):
    return {'Skin.String(Infinity.ThemePolicy)': policy,
            'Window(Home).Property(Infinity.SystemTheme)': theme,
            'Window(Home).Property(Infinity.DeviceMode)': mode,
            'System.ScreenWidth': width, 'System.ScreenHeight': height}


def visible(control, state, expr):
    return all(Condition(v.text or 'true', state, expr).run()
               for v in control.findall('visible'))


def contrast(a, b):
    def luminance(argb):
        rgb = [int(argb[i:i+2], 16) / 255 for i in (2,4,6)]
        linear = [x / 12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in rgb]
        return sum(x*w for x,w in zip(linear, (.2126,.7152,.0722)))
    low, high = sorted((luminance(a), luminance(b)))
    return (high+.05)/(low+.05)


class ThemeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(APK) as z:
            cls.source = {n: z.read(n) for n in patch.XML_FILES}
            cls.font_data = z.read(patch.SKIN + 'fonts/NotoSans-Regular.ttf')
            cls.font_xml = z.read(patch.SKIN + 'xml/Font.xml')
        cls.result = patch.transform(cls.source)
        cls.old = {n: ET.fromstring(b) for n,b in cls.source.items()}
        cls.new = {n: ET.fromstring(b) for n,b in cls.result.items()}
        cls.expr = {n.get('name'): n.text for n in
                    cls.new[patch.SKIN+'xml/Includes.xml'].findall('expression')}

    def branding(self, roots):
        home = roots[patch.SKIN+'xml/Home.xml']
        sidebar = [c for c in home.iter('control')
                   if (c.findtext('texture') or '').startswith('infinity/sidebar-')]
        widget = roots[patch.SKIN+'xml/Includes_Home.xml'].find("include[@name='ImageWidget']")
        hero = [c for c in widget.iter('control')
                if (c.findtext('texture') or '').startswith('infinity/hero-')]
        body = [c for c in widget.iter('control') if c.get('type') == 'textbox']
        return sidebar, hero, body

    def test_regression_manual_light_was_not_mutually_exclusive(self):
        sidebar, hero, _ = self.branding(self.old)
        state = facts(policy='light')
        self.assertEqual(sum(visible(c,state,{}) for c in sidebar), 3)
        self.assertEqual(sum(visible(c,state,{}) for c in hero), 2)

    def test_regression_square_mobile_had_no_body(self):
        _, _, body = self.branding(self.old)
        self.assertEqual(sum(visible(c,facts(width=1000,height=1000),{}) for c in body), 0)

    def test_theme_layout_matrix_270_cases(self):
        sidebar, hero, body = self.branding(self.new)
        for policy, theme, mode, size in itertools.product(
                ('','system','light','dark','oled','invalid'),
                ('unknown','light','dark'), ('','mobile','tv'),
                ((658,1536),(1536,658),(1182,1312),(1920,1080),(1000,1000))):
            state = facts(policy,theme,mode,*size)
            with self.subTest(policy=policy,theme=theme,mode=mode,size=size):
                expected = policy == 'light' or (policy in ('','system') and theme == 'light')
                self.assertEqual(Condition(patch.EXP('ThemeLight'),state,self.expr).run(),expected)
                for group in (sidebar,hero,body):
                    self.assertEqual(sum(visible(c,state,self.expr) for c in group),1)
                for group in (sidebar,hero):
                    selected = next(c for c in group if visible(c,state,self.expr))
                    self.assertTrue(selected.findtext('texture').endswith('light.png' if expected else 'dark.png'))

    def test_focus_palette_is_paired_and_has_no_dynamic_tints(self):
        menu = self.new[patch.SKIN+'xml/Home.xml'].find(".//control[@id='9000']")
        for layout_name in ('focusedlayout','itemlayout'):
            groups = menu.find(layout_name).findall('control')
            self.assertEqual(len(groups),2)
            for group in groups:
                theme = group.findtext('description').split()[-1]
                palette = patch.PALETTES[theme]
                for c in group.iter('control'):
                    tex = c.find('texture')
                    if tex is not None:
                        self.assertNotIn('$VAR[',tex.get('colordiffuse',''))
                    if c.get('type') == 'label':
                        expected = palette['fg' if layout_name=='focusedlayout' else 'text']
                        self.assertEqual(c.findtext('textcolor'),expected)
                        self.assertEqual(c.findtext('selectedcolor'),expected)
                if layout_name == 'focusedlayout':
                    row = next(c for c in group.iter('control') if c.findtext('width')=='462'
                               and c.findtext('texture')=='colors/white.png')
                    self.assertEqual(row.find('texture').get('colordiffuse'),palette['bg'])
                    self.assertGreaterEqual(contrast(palette['bg'],palette['fg']),4.5)

    def test_body_centering_is_not_reset_by_grouplist(self):
        root = self.new[patch.SKIN+'xml/Includes_Home.xml']
        gl = root.find("include[@name='ImageWidget']/definition/control/control")
        self.assertEqual(gl.findtext('usecontrolcoords'),'true')
        for c in gl.findall("control[@type='textbox']"):
            self.assertEqual(c.findtext('centerleft'),'50%')
            self.assertIsNone(c.find('left'))
            self.assertEqual(c.findtext('align'),'center')
            self.assertGreater(int(c.find('height').get('max')),300)
            # Center equals the hero/button center on each existing skin canvas.
            for canvas in (1920,2040,2160,2338,2560):
                parent_width = canvas - 462 - 80
                child_width = float(c.findtext('width'))
                left = parent_width*.5-child_width*.5
                self.assertGreaterEqual(left,0)
                self.assertAlmostEqual(left+child_width/2,parent_width/2)

    def test_example_copy_fits_height_using_bundled_font_estimate(self):
        text = ('Your library is currently empty. In order to populate it with your personal media, '
                'enter "Files" section, add a media source and configure it. After the source has been '
                'added and indexed you will be able to browse your library.')
        definitions = ET.fromstring(self.font_xml).find('fontset')
        sizes = {f.findtext('name'):int(f.findtext('size')) for f in definitions.findall('font')}
        _, _, body = self.branding(self.new)
        for c in body:
            font = ImageFont.truetype(io.BytesIO(self.font_data), sizes[c.findtext('font')])
            lines, line = [], ''
            for word in text.split():
                candidate = (line+' '+word).strip()
                if font.getlength(candidate) > int(c.findtext('width')):
                    lines.append(line);line=word
                else:
                    line=candidate
            lines.append(line)
            estimated_height = len(lines)*sum(font.getmetrics())*1.2
            self.assertLess(estimated_height,int(c.find('height').get('max')))
            self.assertLess(330+estimated_height+24+76,900)

    def test_fonts_and_hero_controls_preserved(self):
        for old,new in zip(self.branding(self.old)[2],self.branding(self.new)[2]):
            self.assertEqual(old.findtext('font'),new.findtext('font'))
            self.assertEqual(old.findtext('label'),new.findtext('label'))
        for old,new in zip(self.branding(self.old)[1],self.branding(self.new)[1]):
            for field in ('width','height','texture','aspectratio'):
                self.assertEqual(old.findtext(field),new.findtext(field))
        self.assertNotIn(patch.SKIN+'xml/Font.xml',self.result)
        self.assertEqual(set(self.result),set(patch.XML_FILES))

    def test_neutral_texture_paths_and_idempotence(self):
        for root in self.new.values():
            self.assertFalse(any(t.text=='white.png' for t in root.iter('texture')))
        self.assertEqual(patch.transform(self.result),self.result)

if __name__ == '__main__':
    unittest.main(verbosity=2)
