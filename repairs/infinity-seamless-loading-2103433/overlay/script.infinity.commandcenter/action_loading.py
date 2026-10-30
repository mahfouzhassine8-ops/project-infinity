# SPDX-License-Identifier: GPL-2.0-or-later
"""Ephemeral Infinity UI loading. No worker, timer, network or persistence owner.

Clients report their *actual* preparation boundaries; the existing foreground
service drains a bounded notification mailbox on its existing UI tick. Kodi's
original action/window/directory consumer remains the sole navigation owner.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from contextlib import contextmanager
import hashlib
import json
import threading
import time
import uuid

EVENT = 'seamless.loading'
SENDER = 'script.infinity.commandcenter'
TERMINAL = frozenset(('ready', 'failed', 'canceled'))
MAX_JOBS = 128
MAX_RETIRED = 256
MAX_EVENTS = 512
MAX_EVENT_BYTES = 1536
THRESHOLD = .18
OBSERVATION_LIMIT = 120.0  # Retires UI observation only, never times out a provider.
PREFIX = 'Infinity.Loading.'
PROPERTIES = ('Token', 'State', 'Window', 'Control', 'Item', 'Target',
              'Active', 'Global', 'Status')


class LoadingState:
    """Pure serial state machine; tokens never revive after terminal delivery."""
    def __init__(self):
        self.action = None
        self.jobs = OrderedDict()
        self.retired = OrderedDict()
        self.retired_before = -1.0

    def _retire(self, token, state="canceled"):
        if token:
            self.retired[token] = state
            self.retired.move_to_end(token)
            while len(self.retired) > MAX_RETIRED:
                self.retired.popitem(last=False)

    def cancel_action(self):
        if self.action:
            self.retired_before = max(self.retired_before, self.action['born'])
            self._retire(self.action['token'])
            self.action = None

    def cancel_all(self):
        self.cancel_action()
        for token in self.jobs:
            self._retire(token)
        self.jobs.clear()

    def event(self, value, now, context):
        token, state = value.get('token', ''), value.get('state', '')
        if not isinstance(token, str) or not (len(token) == 32 and all(c in '0123456789abcdef' for c in token)):
            return
        if state in TERMINAL:
            sent = value.get('sent', now)
            if isinstance(sent, (float, int)) and not isinstance(sent, bool) and 0 <= sent <= now:
                self.retired_before = max(self.retired_before, sent)
            self.jobs.pop(token, None)
            if self.action and self.action['token'] == token:
                self.action = None
            self._retire(token, state)
            return
        if state != 'preparing' or token in self.retired or token in self.jobs:
            return
        born = value.get('born')
        if not isinstance(born, (float, int)) or isinstance(born, bool) or not self.retired_before <= born <= now or now - born >= OBSERVATION_LIMIT:
            return
        if not context['allowed']:
            self._retire(token)
            return
        owner = value.get('owner')
        if not isinstance(owner, dict):
            owner = {}
        # A delayed event must never attach itself to the current, different
        # screen/row/profile. Missing UI ownership may only become a global job.
        matches = all(str(owner.get(key, '')) == str(context.get(key, ''))
                      for key in ('window', 'control', 'item', 'profile', 'geometry'))
        foreground = value.get('foreground') is True and matches
        target = value.get('target', '')
        if not isinstance(target, str) or len(target) != 64 or any(c not in '0123456789abcdef' for c in target):
            return
        entry = dict(token=token, state='pending', target=target,
                     started=born, born=born, context=dict(context), owner=dict(owner),
                     foreground=foreground, navigation=value.get('navigation') is True,
                     busy_seen=False)
        if value.get('foreground') is True and not matches:
            self._retire(token)
            return  # Stale foreground work must not become a phantom drawer job.
        if foreground:
            self.cancel_action()
            self.action = entry
        else:
            if len(self.jobs) >= MAX_JOBS:
                return  # UI observation bounded; original operation unaffected.
            self.jobs[token] = entry

    def tick(self, now, context):
        if not context['allowed']:
            self.retired_before = max(self.retired_before, now)
            self.cancel_all()
            return self.presentation(now)
        action = self.action
        if action:
            before = action['context']
            same = all(context.get(k) == before.get(k)
                       for k in ('window', 'control', 'item', 'profile', 'geometry'))
            same = same and (context.get('dialog') in (0, 10101, 10138, 10160) or context.get('dialog') == before.get('dialog'))
            if not same or context.get('playback') != before.get('playback') or now - action['started'] >= OBSERVATION_LIMIT:
                self.retired_before = max(self.retired_before, now)
                self.cancel_action()
            elif action['navigation']:
                if context.get('busy'):
                    action['busy_seen'] = True
                elif action['busy_seen']:
                    self.cancel_action()  # Native busy lifetime ended, not invented readiness.
        if self.action and now - self.action['started'] >= THRESHOLD:
            self.action['state'] = 'preparing'
        for token, job in list(self.jobs.items()):
            before = job['context']
            if (context.get('profile') != before.get('profile') or
                    context.get('geometry') != before.get('geometry') or
                    now - job['started'] >= OBSERVATION_LIMIT):
                self.jobs.pop(token, None)
                self._retire(token)
        return self.presentation(now)

    def presentation(self, now):
        action = self.action
        pending = bool(action and now - action['started'] >= THRESHOLD)
        visible = pending and bool(action['context'].get('framed', False))
        global_visible = not visible and (pending or any(now - job['started'] >= THRESHOLD for job in self.jobs.values()))
        if not visible:
            return dict(Token='', State='idle', Window='', Control='', Item='', Target='',
                        Active='false', Global='true' if global_visible else 'false',
                        Status='Loading' if global_visible else '')
        owner = action['owner']
        return dict(Token=action['token'], State='preparing', Window=str(owner['window']),
                    Control=str(owner['control']), Item=str(owner['item']), Target=action['target'],
                    Active='true', Global='false', Status='Loading')


def _context(xbmc, gui, foreground=True):
    window = gui.getCurrentWindowId()
    dialog = gui.getCurrentWindowDialogId()
    try:
        control = gui.Window(window).getFocusId()
    except RuntimeError:
        control = 0
    item = xbmc.getInfoLabel('Container(%d).CurrentItem' % control) if control else ''
    profile = xbmc.getInfoLabel('System.ProfileName')
    geometry = '|'.join(str(xbmc.getInfoLabel(k)) for k in ('System.ScreenWidth', 'System.ScreenHeight'))
    home = gui.Window(10000)
    experience = home.getProperty('Infinity.Experience') or home.getProperty('Infinity.NativeExperience')
    allowed = foreground and xbmc.getSkinDir() == 'skin.infinity.diggz' and experience.lower() != 'cobra'
    framed = '|%d|' % control in home.getProperty(PREFIX + 'FrameControls.' + str(window)) if control else False
    return dict(window=window, control=control, item=item, profile=profile, framed=framed,
                geometry=geometry, dialog=dialog, allowed=bool(allowed),
                playback=str(xbmc.getInfoLabel('Player.Filenameandpath')),
                busy=bool(xbmc.getCondVisibility('Window.IsActive(busydialog) | Window.IsActive(busydialognocancel) | Window.IsActive(progressdialog)')))


def _send(xbmc, value):
    # Values contain only generated tokens, numeric IDs, route hashes and bounded
    # owner metadata. JSON quotes/commas stay inside Kodi's quoted third argument.
    value = dict(value, sent=time.monotonic())
    raw = json.dumps(value, ensure_ascii=True, separators=(',', ':'))
    if len(raw) > MAX_EVENT_BYTES:
        return
    escaped = raw.replace('\\', '\\\\').replace('"', '\\"')
    xbmc.executebuiltin('NotifyAll(%s,%s,"%s")' % (SENDER, EVENT, escaped))


@contextmanager
def preparation(target, *, background=False):
    """Observe an actual synchronous owned preparation, never execute it twice."""
    import xbmc
    import xbmcgui
    context = _context(xbmc, xbmcgui)
    token = uuid.uuid4().hex
    born = time.monotonic()
    active = context['allowed']
    if active:
        _send(xbmc, dict(token=token, born=born, state='preparing', foreground=not background and bool(context['control']),
                        target=hashlib.sha256(target.encode('utf-8')).hexdigest(),
                        owner={key:context[key] for key in ('window','control','item','profile','geometry')}))
    try:
        yield token
    except BaseException:
        if active:
            _send(xbmc, dict(token=token, state='failed'))
        raise
    else:
        if active:
            _send(xbmc, dict(token=token, state='ready'))


def make_monitor(xbmc, gui):
    """Separate UI observer. Protected CheckpointMonitor is never replaced."""
    class LoadingMonitor(xbmc.Monitor):
        def __init__(self):
            super().__init__()
            self.state = LoadingState()
            self.mailbox = deque()
            self.lock = threading.Lock()
            self.home = gui.Window(10000)
            self.published = {}
            self.overflow = False
            self.epoch = uuid.uuid4().hex
            self.fingerprint = None

        def onNotification(self, sender, method, data):
            if method not in (EVENT, 'Other.' + EVENT, SENDER + '.' + EVENT) or sender != SENDER:
                return
            if not isinstance(data, str) or len(data) > MAX_EVENT_BYTES:
                return
            try:
                value = json.loads(data)
            except (ValueError, TypeError):
                return
            if not isinstance(value, dict):
                return
            value['_arrival'] = time.monotonic()
            with self.lock:
                if len(self.mailbox) == MAX_EVENTS:
                    self.mailbox.clear()
                    self.overflow = True  # Clear all observed state on lost events.
                self.mailbox.append(value)

        def tick(self, foreground=True):
            context = _context(xbmc, gui, foreground)
            now = time.monotonic()
            fingerprint = tuple(context[key] for key in ('profile', 'geometry', 'window', 'allowed'))
            if fingerprint != self.fingerprint:
                self.state.cancel_all()
                self.epoch = uuid.uuid4().hex
                self.fingerprint = fingerprint
                self.home.setProperty(PREFIX + 'Context', self.epoch)
                self.home.setProperty(PREFIX + 'CurrentWindow', str(context['window']))
            with self.lock:
                events = list(self.mailbox)
                self.mailbox.clear()
                overflow = self.overflow
                self.overflow = False
            if overflow:
                self.state.cancel_all()
            for value in events:
                if value.get('state') == 'cancel':
                    self.state.event(dict(value, state='canceled'), now, context)
                elif value.get('state') == 'action':
                    # Static XML reports only original explicit actions. No
                    # generic onclick is added to an implicit Kodi list route.
                    supplied = value.get('owner', {})
                    if not isinstance(supplied, dict) or supplied.get('epoch') != self.epoch:
                        continue
                    owner = dict(supplied, profile=context['profile'], geometry=context['geometry'])
                    value = dict(value, state='preparing', token=uuid.uuid4().hex,
                                 foreground=True, owner=owner, navigation=True, born=value['_arrival'])
                    self.state.event(value, now, context)
                else:
                    self.state.event(value, now, context)
            presentation = self.state.tick(now, context)
            for key in PROPERTIES:
                next_value = presentation[key]
                if self.published.get(key) != next_value:
                    if next_value:
                        self.home.setProperty(PREFIX + key, next_value)
                    else:
                        self.home.clearProperty(PREFIX + key)
                    self.published[key] = next_value

    return LoadingMonitor()
