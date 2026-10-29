"""Finite signed431 UI journey for Pro Fullscreen / More / PiP ownership.

Normal UI imports the explicitly synthetic loopback playlist. Every player
action is an adb coordinate press on its current visible accessibility bounds,
including horizontal-strip scrolling. No root, app-data injection, force-stop,
uninstall, reset, Infinity launch or application shutdown operation exists here.
"""
import argparse
import json
import re
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

from android_probe import PACKAGE, adb


def bounds(node):
    values = tuple(map(int, re.findall(r'-?\d+', node.get('bounds', ''))))
    return values if len(values) == 4 else (0, 0, 0, 0)


def center(box):
    return (box[0]+box[2])//2, (box[1]+box[3])//2


def intersect(a, b):
    return max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])


def positive(box):
    return box[2]-box[0] > 8 and box[3]-box[1] > 8


class Snapshot:
    def __init__(self, raw):
        self.root = ET.fromstring(raw)
        self.nodes = list(self.root.iter('node'))
        self.parents = {child: parent for parent in self.root.iter() for child in parent}

    def find(self, pattern, nodes=None, enabled=False, clickable=False):
        for node in reversed(self.nodes if nodes is None else list(nodes)):
            if node.get('package') != PACKAGE:
                continue
            if enabled and node.get('enabled') != 'true':
                continue
            if clickable and node.get('clickable') != 'true':
                continue
            if positive(bounds(node)) and any(re.search(pattern, node.get(k, ''))
                                              for k in ('text', 'content-desc')):
                return node
        return None

    def labels(self):
        return [n.get('text') or n.get('content-desc') for n in self.nodes
                if n.get('package') == PACKAGE and (n.get('text') or n.get('content-desc'))]

    def native_dialog_item(self, pattern):
        # Framework AlertDialog items use ListView.onItemClick: the enabled
        # text1 label and its ListView need not expose clickable=true. Keep
        # this exception separate from actual player controls.
        for node in reversed(self.nodes):
            if (node.get('resource-id') != 'android:id/text1' or
                    node.get('class') != 'android.widget.TextView' or
                    node.get('package') != PACKAGE or
                    node.get('enabled') != 'true' or
                    not any(re.search(pattern, node.get(k, ''))
                            for k in ('text', 'content-desc'))):
                continue
            hit = bounds(node)
            ancestor = self.parents.get(node)
            dialog_list = False
            while ancestor is not None and ancestor.tag == 'node':
                if (ancestor.get('package') != PACKAGE or
                        ancestor.get('enabled') != 'true' or
                        ancestor.get('visible-to-user') == 'false'):
                    hit = (0, 0, 0, 0)
                    break
                hit = intersect(hit, bounds(ancestor))
                if (ancestor.get('resource-id') == 'android:id/select_dialog_listview' and
                        ancestor.get('class') == 'android.widget.ListView'):
                    dialog_list = True
                ancestor = self.parents.get(ancestor)
            if dialog_list and node.get('visible-to-user') != 'false' and positive(hit):
                return node, hit
        return None

    def strip(self):
        for node in reversed(self.nodes):
            if node.get('class') != 'android.widget.HorizontalScrollView' or not positive(bounds(node)):
                continue
            children = list(node.iter('node'))
            # Fullscreen's separate strip uses Channels / Display. The Pro
            # inline strip has its own actual Action views and labels instead.
            if self.find(r'^Channels$|^Display$', children) is not None:
                continue
            if self.find(r'^Pause$|^Play$|^Favorite$|^Subtitles$|^Fullscreen$|^More$|^PiP$', children) is not None:
                return node
        return None

    def pro_hero(self):
        # Both source arrows are direct children of the real clickable Hero.
        # WATCHING can already be active with Preview/Unmute and the four-second
        # player strip hidden, so those controls cannot bootstrap its geometry.
        previous = self.find(r'^Previous Pro source$', enabled=True, clickable=True)
        following = self.find(r'^Next Pro source$', enabled=True, clickable=True)
        hero = self.parents.get(previous) if previous is not None else None
        if (following is not None and hero is self.parents.get(following) and
                hero.get('package') == PACKAGE and hero.get('class') == 'android.view.ViewGroup' and
                hero.get('enabled') == 'true' and hero.get('clickable') == 'true' and
                positive(bounds(hero))):
            return hero
        return None


def journey(out):
    out.mkdir(parents=True, exist_ok=False)
    steps = []
    report = {'scope': 'SIGNED431_PRO_VISIBLE_COORDINATE_BUTTONS_SYNTHETIC_QA1',
              'physical_Fold': 'NOT_RUN', 'Infinity': 'NOT_LAUNCHED',
              'shutdown': 'NOT_RUN', 'steps': steps, 'actions': {}}
    sequence = 0
    hero_box = None

    def ui():
        nonlocal sequence
        adb('shell', 'uiautomator', 'dump', '--compressed', '/sdcard/cobra-button-qa.xml')
        raw = adb('shell', 'cat', '/sdcard/cobra-button-qa.xml')
        sequence += 1
        (out/('%03d-ui.xml' % sequence)).write_text(raw)
        return Snapshot(raw)

    def screenshot(name):
        raw = subprocess.check_output(['adb', 'exec-out', 'screencap', '-p'], timeout=15)
        (out/(name+'.png')).write_bytes(raw)

    def press_node(node, purpose, clip=None):
        box = bounds(node)
        hit = intersect(box, clip) if clip else box
        assert positive(hit), ('No usable visible hit rectangle', purpose, box, clip)
        x, y = center(hit)
        adb('shell', 'input', 'tap', str(x), str(y))
        steps.append({'coordinate_press': purpose, 'node_bounds': list(box),
                      'visible_hit_bounds': list(hit), 'coordinate': [x, y],
                      'content_desc': node.get('content-desc'), 'class': node.get('class')})

    def scroll_sheet(snap):
        for node in reversed(snap.nodes):
            if node.get('class') == 'android.widget.ScrollView' and node.get('scrollable') == 'true':
                b = bounds(node)
                if not positive(b):
                    continue
                x = (b[0]+b[2])//2
                inset = max(30, (b[3]-b[1])//8)
                adb('shell', 'input', 'swipe', str(x), str(b[3]-inset),
                    str(x), str(b[1]+inset), '350')
                steps.append({'scroll_native_sheet': list(b)})
                return True
        return False

    def wait(pattern, attempts=10, absent=None):
        for _ in range(attempts):
            snap = ui()
            if snap.find(pattern) is not None and (absent is None or snap.find(absent) is None):
                return snap
            time.sleep(.5)
        raise RuntimeError('UI state not observed: '+pattern+'; labels='+repr(snap.labels()))

    def tap(pattern, attempts=8, sheet_scroll=False, native_dialog_item=False):
        for _ in range(attempts):
            snap = ui()
            node = snap.find(pattern, enabled=True, clickable=True)
            if node is not None:
                press_node(node, pattern)
                return
            item = snap.native_dialog_item(pattern) if native_dialog_item else None
            if item is not None:
                node, visible = item
                press_node(node, 'Native dialog item '+pattern, visible)
                return
            if sheet_scroll:
                scroll_sheet(snap)
            time.sleep(.5)
        raise RuntimeError('Visible clickable action not observed: '+pattern+'; labels='+repr(snap.labels()))

    def activity(name):
        raw = adb('shell', 'dumpsys', 'activity', 'activities')
        (out/(name+'-activity.txt')).write_text(raw)
        return raw

    def pinned(raw):
        return any(PACKAGE in line and re.search(r'\b(?:mode|windowingMode)=pinned\b', line)
                   for line in raw.splitlines())

    def full_screen(snap):
        return snap.find(r'^Return to preview$') is not None and snap.find(r'^Multi-View$') is not None

    def remember_hero(snap, anchor):
        nonlocal hero_box
        b = bounds(anchor)
        parent = snap.parents.get(anchor)
        while parent is not None:
            p = bounds(parent)
            if positive(p) and p[2]-p[0] >= b[2]-b[0] and p[3]-p[1] > (b[3]-b[1])*2:
                hero_box = p
                return
            parent = snap.parents.get(parent)

    def reveal():
        assert hero_box is not None, 'Pro hero geometry has not been observed'
        x = (hero_box[0]+hero_box[2])//2
        y = hero_box[1]+(hero_box[3]-hero_box[1])//3
        adb('shell', 'input', 'tap', str(x), str(y))
        steps.append({'reveal_existing_pro_controls': [x, y], 'hero_bounds': list(hero_box)})

    def strip_press(label, direction='left', force_scroll=False):
        # Only scroll the real inline strip. Pointer positions are always
        # derived from its current bounds and intersected with its viewport.
        if hero_box is not None:
            reveal()
        interacted_at = time.monotonic()
        for attempt in range(7):
            snap = ui()
            strip = snap.strip()
            if strip is None:
                reveal()
                interacted_at = time.monotonic()
                continue
            remember_hero(snap, strip)
            viewport = bounds(strip)
            target = snap.find('^'+re.escape(label)+'$', strip.iter('node'), enabled=True, clickable=True)
            if target is not None and positive(intersect(bounds(target), viewport)) and not (force_scroll and attempt == 0):
                # This hierarchy follows the last reveal OR strip gesture.
                # No new input or expensive screenshot may move/expire it
                # between measurement and the coordinate down event.
                elapsed = time.monotonic()-interacted_at
                assert elapsed < 3.5, 'Final target observation exceeded existing four-second visibility window'
                steps.append({'final_native_target_measurement': label,
                              'bounds': list(bounds(target)),
                              'viewport': list(viewport),
                              'seconds_since_last_reveal_or_strip_gesture': elapsed})
                press_node(target, 'Pro '+label, viewport)
                return
            y = (viewport[1]+viewport[3])//2
            inset = max(12, (viewport[2]-viewport[0])//8)
            left, right = viewport[0]+inset, viewport[2]-inset
            a, b = (right, left) if direction == 'left' else (left, right)
            adb('shell', 'input', 'swipe', str(a), str(y), str(b), str(y), '350')
            steps.append({'scroll_pro_strip': direction, 'viewport': list(viewport)})
            interacted_at = time.monotonic()
        raise RuntimeError('Pro strip action not observed: '+label+'; labels='+repr(snap.labels()))

    def pro_ready():
        nonlocal hero_box
        for _ in range(8):
            snap = ui()
            strip = snap.strip()
            if strip is not None:
                remember_hero(snap, strip)
                return
            if snap.find(r'^Choose a channel$') is not None:
                node = snap.find(r'^Next Pro source$', enabled=True, clickable=True)
                if node is not None:
                    press_node(node, 'Next Pro source to synthetic QA1')
                    continue
            for label in ('Unmute', 'Preview'):
                node = snap.find('^'+label+'$', enabled=True, clickable=True)
                if node is not None:
                    remember_hero(snap, node)
                    press_node(node, 'Pro '+label+' normal watching entry')
                    break
            else:
                hero = snap.pro_hero()
                if hero is not None:
                    hero_box = bounds(hero)
                    press_node(hero, 'Pro watching Hero to reveal controls')
                elif hero_box is not None:
                    reveal()
            time.sleep(.5)
        raise RuntimeError('Pro watching controls not observed; labels='+repr(snap.labels()))

    try:
        tap(r'ADD TV SOURCE')
        tap(r'^M3U / M3U8 playlist$', native_dialog_item=True)
        for index, value in enumerate(('CobraQA', 'http://10.0.2.2:8765/qa.m3u')):
            fields = [n for n in ui().nodes if n.get('class') == 'android.widget.EditText']
            assert len(fields) == 3, 'Normal M3U form must have three fields'
            press_node(fields[index], 'M3U field '+str(index))
            focused = [n for n in ui().nodes if n.get('class') == 'android.widget.EditText']
            assert focused[index].get('focused') == 'true', 'IME moved expected form field'
            adb('shell', 'input', 'text', value)
        tap(r'^TEST & SAVE$')
        snap = wait(r'^QA 1,|^Multi-View$', attempts=15)
        if full_screen(snap):
            adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
            steps.append({'navigation': 'Back from observed source-test fullscreen to preview'})
        tap(r'^Choose one of five view modes$|^Choose view mode$|^Views$')
        tap(r'^Pro,', sheet_scroll=True)
        wait(r'^Pro$|^COBRA LIVE$')
        screenshot('pro-entry')
        pro_ready()

        strip_press('Fullscreen')
        snap = wait(r'^Return to preview$')
        assert full_screen(snap), 'Fullscreen press did not expose native fullscreen controls'
        assert not pinned(activity('fullscreen')), 'Fullscreen press entered system PiP'
        screenshot('fullscreen-result')
        report['actions']['Fullscreen'] = 'FULLSCREEN_NATIVE_RETURN_TO_PREVIEW_AND_MULTI_VIEW; NOT_PINNED'
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        wait(r'^Pro$|^COBRA LIVE$', absent=r'^Return to preview$')
        pro_ready()

        strip_press('More', direction='left')
        snap = wait(r'^Channel playback$')
        assert snap.find(r'^Channel actions$') is not None, 'Original More menu heading missing'
        assert not pinned(activity('more')), 'More press entered system PiP'
        screenshot('more-result')
        report['actions']['More'] = 'ORIGINAL_CHANNEL_ACTIONS_MENU_WITH_CHANNEL_PLAYBACK'
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        wait(r'^Pro$|^COBRA LIVE$', absent=r'^Channel playback$')
        pro_ready()
        # Return leftward toward Fullscreen, then scroll rightward again for
        # PiP. This exercises both native horizontal-scroll directions.
        strip_press('Fullscreen', direction='right', force_scroll=True)
        snap = wait(r'^Return to preview$')
        assert full_screen(snap) and not pinned(activity('fullscreen-after-scroll'))
        screenshot('fullscreen-after-scroll-result')
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        wait(r'^Pro$|^COBRA LIVE$', absent=r'^Return to preview$')
        pro_ready()

        strip_press('PiP', direction='left')
        entered = False
        for _ in range(10):
            if pinned(activity('pip')):
                entered = True
                break
            time.sleep(.5)
        assert entered, 'PiP press did not produce an actual pinned Cobra task'
        screenshot('pip-result')
        report['actions']['PiP'] = 'SYSTEM_PINNED_COBRA_TASK'
        # Existing activity is manifest singleTask. Normal explicit foreground
        # return neither recreates the package nor clears/stops its data/player.
        (out/'pip-normal-return.txt').write_text(adb('shell', 'am', 'start', '-W', '-n',
                                                   PACKAGE+'/.InfinityLiveActivity'))
        wait(r'^Pro$|^COBRA LIVE$', absent=r'^Return to preview$')
        assert not pinned(activity('pip-return')), 'Cobra remained pinned after normal foreground return'
        screenshot('pip-return-result')
        pro_ready()
        strip_press('More', direction='left')
        wait(r'^Channel playback$')
        screenshot('more-reopened-after-pip')
        report['status'] = 'PASS_ACTUAL_PRO_FULLSCREEN_MORE_PIP_COORDINATE_JOURNEY'
        report['limits'] = ('Android17 emulator, synthetic QA1, non-Sports Pro. Host tests cover '
                            'other mode/resize/clipped/remote routes; no physical Fold, live provider '
                            'or decoder-internal/session-state acceptance is claimed.')
    except Exception as exc:
        report['status'] = 'FAILED_AT_RECORDED_UI_OR_ACTION_OBSERVATION'
        report['error'] = str(exc)
        (out/'ERROR.txt').write_text(traceback.format_exc())
        raise
    finally:
        diagnostics = [('activity.txt', ('shell', 'dumpsys', 'activity', 'activities')),
                       ('window.txt', ('shell', 'dumpsys', 'window', 'windows')),
                       ('meminfo.txt', ('shell', 'dumpsys', 'meminfo', PACKAGE)),
                       ('logcat.txt', ('logcat', '-d', '-v', 'threadtime'))]
        for name, args in diagnostics:
            try:
                (out/name).write_text(adb(*args, check=False))
            except Exception as exc:
                report.setdefault('diagnostic_errors', []).append(name+': '+str(exc))
        try:
            screenshot('last-screen')
        except Exception as exc:
            report.setdefault('diagnostic_errors', []).append('screenshot: '+str(exc))
        report.setdefault('status', 'FAILED_BEFORE_COMPLETION')
        (out/'OUTCOME.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    journey(**vars(parser.parse_args()))
