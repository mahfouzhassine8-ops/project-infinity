"""Unwired test-only proposal for the existing signed69 theme prerequisite.

Design owns integration. Nothing runs at import; no installation, source writes,
settings writes, service launch, polling loop, or theme acceptance occurs here.
The sole optional state action is normal enabling of an identity-checked existing
addon. That can start its original primary service and normal checkpoint writes.

rpc(method, params, timeout=5) uses the driver's bounded transport.
read_runtime_bytes(path, limit) must read only the actual returned runtime root,
resolve special:// through the runtime VFS if necessary, enforce the byte limit,
and return bytes under the driver's finite deadline. It must not import addons.
The driver retains this instance and its events; an uncertain enable reply is
never retried by this instance. Its existing finite condition polling can call
observe_theme; there are no arbitrary sleeps or publisher-start workarounds.
"""
import hashlib
import json
import time
import xml.etree.ElementTree as ET


ADDON = 'service.infinity.compat'
CC = 'script.infinity.commandcenter'
VERSION = '0.7.2'
EVIDENCE_SHA256 = 'b3e818c6a0621076223eede73b5c1ddf18e04a4b4cb51a33a07a1cb5020442aa'
PREFIX = 'assets/addons/' + ADDON + '/'
PROPERTIES = ['enabled', 'version', 'path', 'installed']
# Exact protected69 sources already pinned in VIEW-BASELINE-PREREQUISITES.json.
# This engine's FillDetails assigns installed = IsAddonInstalled(id) (bool),
# not an installation timestamp. Keep the strict installed/enabled checks below.
INSTALLED_SOURCE_CONTRACT = {
    'source': 'xbmc/interfaces/json-rpc/AddonsOperations.cpp',
    'sha256': 'f5ffa7acdd3e47a6661345d63dd8ea86b996922c4373ca2e138f9c8dfd2911d7',
    'function': 'CAddonsOperations::FillDetails',
    'lines': [291, 299],
    'installed_type': 'boolean from IsAddonInstalled(addon->ID())',
}
LABELS = [
    'Window(Home).Property(Infinity.Theme)',
    'Window(Home).Property(Infinity.ThemeReady)',
    'Window(Home).Property(Infinity.ThemeRevision)',
    'Window(Home).Property(Infinity.ThemeContractSignature)',
    'Window(Home).Property(Infinity.ThemeContract)',
    'Window(Home).Property(Infinity.SystemTheme)',
    'Window(Home).Property(Infinity.NativeSystemTheme)',
    'Skin.String(Infinity.DarkAppearance)',
]
PUBLIC_THEME_SELECTION = {
    'entrypoint': {'addonid': CC, 'params': ['theme']},
    'required_skin': 'skin.infinity.diggz',
    'dialog_title': 'Infinity Theme',
    'control': 50,
    'selector_source': {
        'asset': 'assets/addons/script.infinity.commandcenter/infinity_settings.py',
        'sha256': 'a846e6fa285618495e572ff77665b4914eb2438ae3c1d7f38f2e53b150cb8e3d',
        'entry': 'open_settings(theme) lines127-138 -> choose() lines34-80',
        'implementation': 'Selector(xbmcgui.WindowXMLDialog), InfinityItemOptions.xml; onInit fills/focuses50; onClick50 returns selected index.',
        'not_standard_Dialog_select': True,
    },
    'light': {'label': 'Light Pearl', 'requested_policy': 'light'},
    'dark': {'label': 'Dark', 'requested_policy': 'dark'},
    'requested_policy_accessor': "xbmcaddon.Addon('service.infinity.compat').getSetting('theme_mode')",
    'action_contract': 'Use existing measured native menu selection; no direct settings or Home-property writes.',
    'acceptance': 'Requires the same genuine recorded playback state and actual effective publication/render captures; this helper makes no mode claim.',
}


class PrerequisiteBlocked(RuntimeError):
    pass


class CompatPrerequisite:
    def __init__(self, rpc, read_runtime_bytes, prerequisites_bytes):
        if hashlib.sha256(prerequisites_bytes).hexdigest() != EVIDENCE_SHA256:
            raise PrerequisiteBlocked('PINNED_EXISTING_PREREQUISITE_EVIDENCE_REQUIRED')
        evidence = json.loads(prerequisites_bytes)
        self.expected = evidence['complete_signed69_compat_asset_member_sha256']
        if len(self.expected) != 17 or not all(p.startswith(PREFIX) for p in self.expected):
            raise PrerequisiteBlocked('EXACT_SIGNED69_17_MEMBER_MAP_REQUIRED')
        self.rpc, self.read_runtime_bytes = rpc, read_runtime_bytes
        self.events, self.enable_attempted = [], False

    def _call(self, method, params):
        event = dict(method=method, params=params, monotonic=time.monotonic())
        self.events.append(event)
        try:
            result = self.rpc(method, params, timeout=5)
        except Exception as error:
            event['error'] = repr(error)
            # Unknown addon/errors do not establish absence or permission to install.
            raise PrerequisiteBlocked('RUNTIME_STATE_UNRESOLVED:' + method) from error
        event['result'] = result
        return result

    def inspect(self):
        result = self._call('Addons.GetAddonDetails', dict(addonid=ADDON, properties=PROPERTIES[:]))
        addon = result.get('addon') if isinstance(result, dict) else None
        if not isinstance(addon, dict) or addon.get('addonid') != ADDON or addon.get('version') != VERSION:
            raise PrerequisiteBlocked('EXACT_EXISTING_COMPAT_072_REQUIRED')
        if type(addon.get('enabled')) is not bool or addon.get('installed') is not True:
            raise PrerequisiteBlocked('EXPLICIT_INSTALLED_ENABLED_STATE_REQUIRED')
        root = addon.get('path')
        if (not isinstance(root, str) or '\x00' in root or '\\' in root or
                not root.startswith(('/', 'special://')) or
                root.rstrip('/').split('/')[-1] != ADDON or '..' in root.split('/')):
            raise PrerequisiteBlocked('ACTUAL_ADDON_SOURCE_ROOT_REQUIRED')
        root = root.rstrip('/')
        actual, descriptor = {}, None
        for member, expected in sorted(self.expected.items()):
            relative = member[len(PREFIX):]
            raw = self.read_runtime_bytes(root + '/' + relative, 4 * 1024 * 1024)
            if not isinstance(raw, bytes) or len(raw) > 4 * 1024 * 1024:
                raise PrerequisiteBlocked('BOUNDED_RUNTIME_SOURCE_BYTES_REQUIRED:' + relative)
            actual[member] = hashlib.sha256(raw).hexdigest()
            if actual[member] != expected:
                raise PrerequisiteBlocked('SIGNED69_RUNTIME_SOURCE_MISMATCH:' + relative)
            if relative == 'addon.xml':
                descriptor = ET.fromstring(raw)
        if descriptor is None or descriptor.get('id') != ADDON or descriptor.get('version') != VERSION:
            raise PrerequisiteBlocked('SIGNED69_DESCRIPTOR_ID_VERSION_REQUIRED')
        proof = dict(addon=dict(addon), source_root=root, member_sha256=actual,
                     evidence_sha256=EVIDENCE_SHA256, monotonic=time.monotonic())
        self.events.append(dict(identity=proof))
        return proof

    def enable_existing(self):
        # Re-read current registry and every source immediately before any action.
        proof = self.inspect()
        if proof['addon']['enabled']:
            return dict(action='ALREADY_ENABLED_NO_ACTION', identity=proof)
        if self.enable_attempted:
            raise PrerequisiteBlocked('NO_ENABLE_RETRY_AFTER_ATTEMPT')
        self.enable_attempted = True
        result = self._call('Addons.SetAddonEnabled', dict(addonid=ADDON, enabled=True))
        if result != 'OK':
            raise PrerequisiteBlocked('NORMAL_ENABLE_REPLY_NOT_OK')
        after = self.inspect()
        if not after['addon']['enabled']:
            raise PrerequisiteBlocked('NORMAL_ENABLE_NOT_OBSERVED')
        return dict(action='EXISTING_EXACT_072_NORMALLY_ENABLED', identity=after)

    def observe_theme(self):
        # One actual sample. Blank state remains unknown; enabling/menu entry does
        # not prove that the separately declared theme publisher actually ran.
        labels = self._call('XBMC.GetInfoLabels', dict(labels=LABELS[:]))
        if not isinstance(labels, dict) or any(not isinstance(labels.get(k), str) for k in LABELS):
            raise PrerequisiteBlocked('ACTUAL_THEME_LABEL_SAMPLE_REQUIRED')
        ready, revision, signature = (labels[LABELS[i]].strip() for i in (1, 2, 3))
        return dict(monotonic=time.monotonic(), labels=dict(labels),
                    publication_observed=ready.lower() == 'true' and bool(revision) and bool(signature),
                    requested_policy='NOT_READ_BY_THIS_HELPER', mode_acceptance='NOT_RUN')
