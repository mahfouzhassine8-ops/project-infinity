"""Actual generated skin/focus integration, not a Kodi renderer substitute.

The condition reader below evaluates the shipped XML's boolean operations for
the selected window/owner cases. It does not claim native rendering acceptance.
"""
import importlib.util
import os
from pathlib import Path
import re
import types
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(os.environ['INFINITY_STAGED'])
SKIN = STAGE / 'members/assets/addons/skin.infinity.diggz/unified'


class Conditions:
    def __init__(self, windows, *, focus=50, properties=None, labels=None, visible=(50, 9001), fullscreen=False):
        self.windows = set(map(str, windows))
        self.focus, self.properties, self.labels = focus, properties or {}, labels or {}
        self.visible, self.fullscreen = set(visible), fullscreen

    def value(self, text):
        text = text.strip()
        m = re.fullmatch(r'Window\(Home\)\.Property\(([^)]+)\)', text)
        if m:
            return self.properties.get(m[1], '')
        if text.startswith('Container('):
            return self.labels.get(text, '')
        return text

    def atom(self, text):
        text = text.strip()
        if text in ('true', 'false'):
            return text == 'true'
        if text == 'Player.IsFullscreen':
            return self.fullscreen
        m = re.fullmatch(r'Window\.IsActive\(([^)]+)\)', text)
        if m:
            return m[1] in self.windows
        m = re.fullmatch(r'Control\.(IsVisible|HasFocus)\((\d+)\)', text)
        if m:
            return int(m[2]) in self.visible if m[1] == 'IsVisible' else int(m[2]) == self.focus
        if text.startswith('String.IsEqual(') and text.endswith(')'):
            depth = 0
            raw = text[len('String.IsEqual('):-1]
            for index, char in enumerate(raw):
                depth += (char == '(') - (char == ')')
                if char == ',' and depth == 0:
                    first = raw[:index].strip()
                    if not first.startswith(('Window(Home).Property(', 'Container(')):
                        raise AssertionError('Kodi String.IsEqual first argument must be a real info label: ' + first)
                    return self.value(first).lower() == self.value(raw[index+1:]).lower()
        raise AssertionError('Unmodeled generated skin condition: ' + text)

    def evaluate(self, text):
        cursor = 0

        def spaces():
            nonlocal cursor
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1

        def primary():
            nonlocal cursor
            spaces()
            if text[cursor] == '!':
                cursor += 1
                return not primary()
            if text[cursor] == '[':
                cursor += 1
                result = disjunction()
                spaces()
                assert text[cursor] == ']'
                cursor += 1
                return result
            begin, depth = cursor, 0
            while cursor < len(text):
                char = text[cursor]
                if depth == 0 and char in '+|]':
                    break
                depth += (char == '(') - (char == ')')
                cursor += 1
            return self.atom(text[begin:cursor])

        def conjunction():
            nonlocal cursor
            result = primary()
            spaces()
            while cursor < len(text) and text[cursor] == '+':
                cursor += 1
                next_value = primary()
                result = result and next_value
                spaces()
            return result

        def disjunction():
            nonlocal cursor
            result = conjunction()
            spaces()
            while cursor < len(text) and text[cursor] == '|':
                cursor += 1
                next_value = conjunction()
                result = result or next_value
                spaces()
            return result

        answer = disjunction()
        spaces()
        assert cursor == len(text), text[cursor:]
        return answer


def definition():
    root = ET.parse(SKIN / 'Includes_InfinityActionLoading.xml').getroot()
    return next(n for n in root.findall('include') if n.get('name') == 'InfinityActionLoadingFrame')


def parameters(call):
    defaults = {n.get('name'): n.get('default') for n in definition().findall('param')}
    defaults.update({n.get('name'): n.get('value') for n in call.findall('param')})
    return defaults


def frame_visible(call, state):
    expression = definition().findtext('definition/control/visible')
    for name, value in parameters(call).items():
        if value is not None:
            expression = expression.replace('$PARAM[' + name + ']', value)
    return state.evaluate(expression)


class CurrentWindowLoadingTest(unittest.TestCase):
    def test_video_drawer_uses_actual_frame_for_native_busy_without_service(self):
        includes = ET.parse(SKIN / 'Includes.xml').getroot()
        blade = next(n for n in includes.findall('include') if n.get('name') == 'SideBladeLeft')
        original = next(n for n in blade.iter('control') if n.get('id') == '9001')
        frames = [n for n in blade.iter('include') if n.get('content') == 'InfinityActionLoadingFrame']
        self.assertEqual(1, len(frames), 'The actual Videos menu must own its busy feedback')
        call = frames[0]
        for name in ('left', 'top', 'width', 'height'):
            self.assertEqual(original.findtext(name), parameters(call)[name], name)
        self.assertEqual('true', parameters(call)['globalframe'])
        for busy in ('busydialog', 'busydialognocancel'):
            self.assertTrue(frame_visible(call, Conditions((10025, busy))))
        self.assertFalse(frame_visible(call, Conditions((10025,))))
        self.assertFalse(frame_visible(call, Conditions((10025, 'busydialog'), fullscreen=True)))
        self.assertFalse(frame_visible(call, Conditions((10025, 'busydialog'), properties={
            'Infinity.Loading.Active': 'true', 'Infinity.Loading.Window': '10025'})))
        self.assertTrue(frame_visible(call, Conditions((10025, 'busydialog'), properties={
            'Infinity.Loading.Active': 'true', 'Infinity.Loading.Window': '10000'})))
        home = ET.parse(SKIN / 'Home.xml').getroot()
        drawer = next(n for n in home.iter('include') if n.get('content') == 'InfinityActionLoadingFrame'
                      and parameters(n)['globalframe'] == 'true')
        self.assertFalse(frame_visible(drawer, Conditions((10000,10134,'busydialog'), properties={
            'Infinity.Loading.Active':'true','Infinity.Loading.Window':'10134'})),
            'Visible foreground Favorite owns the cue; underlying Home drawer must stay quiet')

    def test_native_video_frame_keeps_window_focus_and_source_ownership(self):
        path = SKIN / 'View_50_List.xml'
        if path.is_file():
            views = ET.parse(path).getroot()
        else:
            # Negative control: this file was unchanged/omitted from434 staging;
            # use the actual immutable baseline member, never a fabricated XML.
            with ZipFile(os.environ['INFINITY_BASE_COMPONENT']) as archive:
                views = ET.fromstring(archive.read('payload/assets/addons/skin.infinity.diggz/unified/View_50_List.xml'))
        frames = [n for n in views.iter('include') if n.get('content') == 'InfinityActionLoadingFrame'
                  and parameters(n)['control'] == '50']
        self.assertGreater(len(frames), 0, 'The actual native list file must have an owned frame')
        call = frames[0]
        self.assertEqual('0', parameters(call)['window'], 'Shared view definitions inherit actual supported window')
        video = ET.parse(SKIN / 'MyVideoNav.xml').getroot()
        capability = next(n.text for n in video.findall('onload') if 'Infinity.Loading.FrameControls.10025' in (n.text or ''))
        self.assertIn('|50|', capability, 'Native view frame must be registered to actual Videos owner')
        props = {'Infinity.Loading.Active': 'true', 'Infinity.Loading.Window': '10025',
                 'Infinity.Loading.Control': '50', 'Infinity.Loading.Item': '2'}
        labels = {'Container(50).CurrentItem': '2'}
        self.assertTrue(frame_visible(call, Conditions((10025,), properties=props, labels=labels)))
        self.assertFalse(frame_visible(call, Conditions((10025,), focus=51, properties=props, labels=labels)))
        self.assertFalse(frame_visible(call, Conditions((10025,), properties=dict(props, **{'Infinity.Loading.Window': '10000'}), labels=labels)))
        self.assertFalse(frame_visible(call, Conditions((10025,), properties=props, labels=dict(labels, **{'Container(50).ListItem.Property(hubsource)': 'different-provider'}))))

    def test_centered_busy_panel_is_retained_only_as_hidden_native_control(self):
        root = ET.parse(SKIN / 'DialogBusy.xml').getroot()
        panel = root.find('controls/control')
        self.assertEqual('false', panel.findtext('visible'))
        self.assertIsNotNone(next((n for n in panel.iter('control') if n.get('id') == '10'), None),
                             'Retain Kodi native progress-control identity and dialog lifetime')
        self.assertEqual('Loading…', panel.findtext("control[@type='label']/label"))

    def test_actual_favourites_context_uses_dialog_focus_and_frame_capability(self):
        source = Path(os.environ.get('INFINITY_LOADING_TEST_SOURCE', str(STAGE / 'candidate-addons/script.infinity.commandcenter/action_loading.py')))
        spec = importlib.util.spec_from_file_location('actual_current_loading', source)
        loading = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loading)
        focused = []

        class Window:
            def __init__(self, id):
                self.id = id

            def getFocusId(self):
                focused.append(self.id)
                return 450 if self.id == 10134 else 9000

            def getProperty(self, name):
                return {'Infinity.Experience': 'Infinity', 'Infinity.Loading.FrameControls.10134': '|450|'}.get(name, '')

        xbmc = types.SimpleNamespace(getSkinDir=lambda: 'skin.infinity.diggz', getInfoLabel=lambda key: {
            'Container(450).CurrentItem': '2', 'System.ProfileName': 'Default'}.get(key, ''), getCondVisibility=lambda key: False)
        gui = types.SimpleNamespace(Window=Window, getCurrentWindowId=lambda: 10000, getCurrentWindowDialogId=lambda: 10134)
        context = loading._context(xbmc, gui)
        self.assertEqual([10134], focused)
        self.assertEqual(10134, context['window'])
        self.assertEqual(450, context['control'])
        self.assertEqual('2', context['item'])
        self.assertTrue(context['framed'])

