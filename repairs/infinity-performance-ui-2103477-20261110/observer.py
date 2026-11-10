"""Disposable performance observer. Never included in an Infinity release."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import types

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from context_batch_prototype import LabelReader

QA = 'script.infinity.performanceprobe'
OUT = Path(xbmcvfs.translatePath('special://profile/addon_data/' + QA))
OUT.mkdir(parents=True, exist_ok=True)
MONITOR = xbmc.Monitor()
HOME = xbmcgui.Window(10000)


def save(name, value):
    path = OUT / name
    tmp = path.with_suffix('.pending')
    tmp.write_text(json.dumps(value, sort_keys=True))
    tmp.replace(path)


def require(value, message):
    if not value:
        raise RuntimeError(message)


def authenticated_loading():
    cc = xbmcaddon.Addon('script.infinity.commandcenter')
    root = Path(xbmcvfs.translatePath(cc.getAddonInfo('path')))
    require(cc.getAddonInfo('version') == '0.3.5.75', 'EXACT_BASELINE_CC75')
    require(xbmcaddon.Addon('skin.infinity.diggz').getAddonInfo('version') == '1.0.5.270', 'EXACT_BASELINE_SKIN270')
    raw = (root / 'module_contract.py').read_bytes()
    require(hashlib.sha256(raw).hexdigest() ==
            '759e60439fae0b1bf0f8a2ff6895209ac848101b9544ac6c0e297b9c73df1267', 'ORIGINAL_TRUST_BOOTSTRAP')
    module = types.ModuleType('module_contract')
    module.__file__ = str(root / 'module_contract.py')
    sys.modules['module_contract'] = module
    exec(compile(raw, module.__file__, 'exec', dont_inherit=True), module.__dict__)
    contract = module.active_contract(str(root), '0.3.5.75')
    sys.path.insert(0, str(root))  # This interpreter only, after the signed ImportGuard is active.
    require(contract.identity.manifest_sha256 ==
            '63110023bf70f4ec32b0ab4750b3c1293a4976aa58cdfd1afbcd55027758b371', 'EXACT_ORIGINAL80_MANIFEST')
    loading = module.source_module(contract, 'performance_probe_loading',
                                   'script.infinity.commandcenter/action_loading.py')
    return contract, loading, module


def state():
    window = xbmcgui.getCurrentWindowId()
    dialog = xbmcgui.getCurrentWindowDialogId()
    focused_window = dialog if dialog not in (0, 9999) else window
    try:
        focus = xbmcgui.Window(focused_window).getFocusId()
    except RuntimeError:
        focus = None
    return dict(at=time.monotonic(), window=window, dialog=dialog, focused_window=focused_window,
                focus=focus, skin=xbmc.getSkinDir(),
                properties={key: HOME.getProperty('Infinity.Loading.' + key)
                            for key in ('Active', 'Global', 'Token', 'State', 'Control', 'Window')},
                motion=HOME.getProperty('Infinity.OptionalMotionAllowed'),
                resident_context=HOME.getProperty('Infinity.Loading.Context'),
                resident_current_window=HOME.getProperty('Infinity.Loading.CurrentWindow'),
                screen=[xbmc.getInfoLabel('System.ScreenWidth'), xbmc.getInfoLabel('System.ScreenHeight')])


def preparation_probe(loading, outcome, sequence):
    """Measure the real resident's handling of a controlled diagnostic preparation.

    This is not provider performance, input-to-photon latency or proof of a
    completed real-provider workflow. No provider or playback call is made.
    """
    require(outcome in ('ready', 'failed', 'context-cancel'), 'SELECTED_PROBE_OUTCOME')
    rows = []
    initial = state()
    begin = time.monotonic()
    token = None
    failed = False
    back_sent = None
    body_entered = None
    try:
        with loading.preparation('performance-diagnostic-' + str(sequence)) as token:
            body_entered = time.monotonic()
            deadline = time.monotonic() + 2.0
            navigated = False
            while time.monotonic() < deadline and not MONITOR.abortRequested():
                row = state()
                row['phase'] = 'controlled_preparation'
                rows.append(row)
                if row['properties']['Token'] == token and row['properties']['Active'] == 'true':
                    save('visible.json', dict(sequence=sequence, token=token, at=row['at']))
                if outcome == 'context-cancel' and not navigated and time.monotonic() - body_entered > .8:
                    # Existing native Back from System Hub, never app Close.
                    require(xbmcgui.getCurrentWindowDialogId() == 11191, 'BACK_ONLY_FROM_SELECTED_HUB_DIALOG')
                    back_sent = time.monotonic()
                    xbmc.executebuiltin('Action(Back)')
                    navigated = True
                MONITOR.waitForAbort(.02)
            if outcome == 'failed':
                raise ValueError('Selected controlled preparation failure')
    except ValueError as error:
        require(outcome == 'failed' and str(error) == 'Selected controlled preparation failure', 'EXACT_CONTROLLED_FAILURE')
        failed = True
    terminal = time.monotonic()
    deadline = terminal + 1.8
    while time.monotonic() < deadline and not MONITOR.abortRequested():
        row = state()
        row['phase'] = 'after_terminal'
        rows.append(row)
        if row['properties']['Token'] != token or row['properties']['Active'] != 'true':
            break
        MONITOR.waitForAbort(.02)
    active = [r['at'] for r in rows if r['properties']['Token'] == token and r['properties']['Active'] == 'true']
    cleared = [r['at'] for r in rows if r['at'] >= terminal and
               (r['properties']['Token'] != token or r['properties']['Active'] != 'true')]
    global_rows = [r['at'] for r in rows if r['properties']['Global'] == 'true']
    published_before_back = bool(back_sent and any(a < back_sent for a in active))
    context_clear = [r['at'] for r in rows if back_sent and back_sent <= r['at'] < terminal and
                     (r['properties']['Token'] != token or r['properties']['Active'] != 'true')]
    return dict(begin=begin, terminal=terminal, outcome=outcome, token=token, failed_fixture=failed,
                body_entered=body_entered,
                context_capture_and_notify_call_ms=1000*(body_entered-begin) if body_entered else None,
                first_active_property_ms=1000*(active[0]-begin) if active else None,
                local_owner_measurement='OBSERVED_MATCHING_TOKEN' if active else 'NOT_AVAILABLE_NO_PUBLISHED_MATCHING_TOKEN',
                unattributed_global_cue_observation=global_rows,
                initial=initial, global_cue_has_no_published_token=True,
                terminal_clear_property_ms=1000*(cleared[0]-terminal) if active and cleared and not back_sent else None,
                back_sent=back_sent,
                context_cancel_token_disappearance_ms=1000*(context_clear[0]-back_sent)
                    if published_before_back and context_clear else None,
                context_cancel_measured=bool(published_before_back and context_clear),
                rows=rows, controlled_fixture=True, actual_provider_performance=False,
                diagnostic_sampling_interval_seconds=.02, diagnostic_load_included=True,
                first_visible_presentation_or_input_latency_measured=False)


def main():
    contract, loading, trust = authenticated_loading()
    save('ready.json', dict(qa=QA, pid=os.getpid(), manifest=contract.identity.manifest_sha256,
                           files=len(contract.files), state=state()))
    until = time.monotonic() + 240
    last = 0
    while time.monotonic() < until and not MONITOR.abortRequested():
        request = OUT / 'request.json'
        if not request.exists():
            MONITOR.waitForAbort(.1)
            continue
        value = json.loads(request.read_text())
        sequence = value['sequence']
        if sequence <= last:
            MONITOR.waitForAbort(.1)
            continue
        last = sequence
        require(value['pid'] == os.getpid(), 'SAME_OBSERVED_PROCESS')
        try:
            contract.current()
            action = value['action']
            if action == 'hub':
                xbmc.executebuiltin('ActivateWindow(1191)')
                deadline = time.monotonic() + 8
                while xbmcgui.getCurrentWindowDialogId() != 11191 and time.monotonic() < deadline:
                    MONITOR.waitForAbort(.05)
                require(xbmcgui.getCurrentWindowDialogId() == 11191, 'REAL_SYSTEM_HUB_DIALOG')
                # Focus the existing Command Center button, never activate Cobra.
                xbmcgui.Window(11191).setFocusId(1191102)
                deadline = time.monotonic() + 2
                while xbmcgui.Window(11191).getFocusId() != 1191102 and time.monotonic() < deadline:
                    MONITOR.waitForAbort(.05)
                require(xbmcgui.Window(11191).getFocusId() == 1191102, 'EXISTING_HUB_COMMAND_BUTTON_FOCUS')
                result = state()
            elif action == 'home-focus':
                require(xbmcgui.getCurrentWindowId() == 10000, 'REAL_HOME_ONLY')
                candidates = HOME.getProperty('Infinity.Loading.FrameControls').split('|')
                selected = None
                for value in candidates[:512]:
                    if not value.isdigit():
                        continue
                    try:
                        control = HOME.getControl(int(value))
                        label = control.getLabel() if hasattr(control, 'getLabel') else ''
                        if not control.isVisible() or 'cobra' in label.lower():
                            continue
                        HOME.setFocusId(int(value))
                        deadline = time.monotonic() + .3
                        while HOME.getFocusId() != int(value) and time.monotonic() < deadline:
                            MONITOR.waitForAbort(.02)
                        if HOME.getFocusId() == int(value):
                            selected = int(value)
                            break
                    except (RuntimeError, AttributeError):
                        continue
                result = dict(state=state(), selected_visible_frame_control=selected)
            elif action == 'state':
                result = state()
            elif action == 'loading':
                result = preparation_probe(loading, value['outcome'], sequence)
            elif action == 'context-compare':
                rows = []
                for pair in range(7):
                    outputs = {}
                    for batch in ((False, True) if pair % 2 == 0 else (True, False)):
                        before = state()
                        reader = LabelReader(xbmc, batch, before['focus'])
                        started = time.monotonic()
                        context = loading._context(reader, xbmcgui)
                        elapsed = 1000*(time.monotonic()-started)
                        outputs[str(batch)] = dict(context=context, elapsed_ms=elapsed,
                            direct_label_calls=reader.direct_calls, batch_calls=reader.batch_calls,
                            batch_valid=reader.batch_valid, adapter_control=reader.control,
                            before=before, after=state())
                    rows.append(dict(pair=pair, order='AB' if pair % 2 == 0 else 'BA',
                        exact_context_equal=outputs['False']['context']==outputs['True']['context'], outputs=outputs))
                    MONITOR.waitForAbort(.15)
                result = dict(rows=rows, actual_signed_context=True, production_patch=False,
                              global_monkeypatch=False, GUI_focus_may_invalidate_pairs=True)
            elif action == 'skin-integrity-cost':
                load_started = time.monotonic()
                common = trust.source_module(contract, 'performance_probe_common',
                                             'script.infinity.commandcenter/common.py')
                module_load_ms = 1000*(time.monotonic()-load_started)
                started = time.monotonic()
                integrity = common.skin_baseline_integrity()
                result = dict(elapsed_ms=1000*(time.monotonic()-started), module_load_ms=module_load_ms, integrity=integrity,
                    source_operation='Exact signed common.skin_baseline_integrity, read-only',
                    warm_cache_may_apply=True, not_attribution_of_original_cold_span=True)
            elif action == 'finish':
                save('reply.json', dict(pid=os.getpid(), sequence=sequence, result=state()))
                return  # Retire this diagnostic interpreter only, not the app.
            else:
                raise RuntimeError('Unselected diagnostic action')
            save('reply.json', dict(pid=os.getpid(), sequence=sequence, result=result))
        except Exception:
            save('reply.json', dict(pid=os.getpid(), sequence=sequence, error=traceback.format_exc()))
            raise


try:
    main()
except Exception:
    save('fatal.json', dict(pid=os.getpid(), error=traceback.format_exc()))
    raise
