#!/usr/bin/env python3
"""Phase-comparison controls; Android owners/logs are explicit read-only peers.

These verify that the optional comparison cannot reuse an old startup log or
call an already-observed service window an initialization reproduction. They
do not grant save, process-death, APK-promotion, or physical Fold acceptance.
"""
import copy
import datetime
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('upgrade_phase_boundary', HERE/'observer_upgrade_android_probe.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


def epoch(text, offset='+0000'):
    return round(datetime.datetime.strptime(text+offset, '%Y-%m-%d %H:%M:%S.%f%z').timestamp()*1000)


def log(start='2026-10-16 20:14:34.017', done='2026-10-16 20:14:47.910', thread=8207):
    return ('\ufeff'+start+' T:'+str(thread)+'     info <general>: Starting Kodi (21.3). Platform: Android\n'+
            (done+' T:'+str(thread)+'     info <general>: initialize done\n'+
             done+' T:'+str(thread)+'     info <general>: Running the application...\n' if done else ''))


class CoreBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.owner = dict(owner='candidate-owner', pid=8134, phase='RUNNING',
                          began=epoch('2026-10-16 20:14:32.503'))
        self.baseline = dict(device_utc_offset='+0000', before_log_sha256=hashlib.sha256(b'retained old log').hexdigest(),
                             before_log_sample_bytes=16, log_sample_limit=upgrade.CORE_LOG_LIMIT)

    def marker(self, text, **owner):
        return upgrade.core_initialization_marker(text, dict(self.owner, **owner), self.baseline)

    def wait(self, *, owner=None, native=None, text=None, task=None):
        current = dict(self.owner if owner is None else owner)
        engine = dict(self.owner if native is None else native)
        def read(path):
            return current if path.endswith('infinity-kodi-process.json') else engine
        def shell(*args, **kwargs):
            self.assertIn(args[0], ('head', 'cat'))
            if args[0] == 'head': return log() if text is None else text
            return 'Tgid:\t8134\nPid:\t8207\n' if task is None else task
        with patch.object(upgrade.probe, 'read_json', side_effect=read), \
                patch.object(upgrade.probe, 'shell', side_effect=shell), \
                patch.object(upgrade.time, 'monotonic', return_value=10):
            return upgrade.wait_core_initialized(self.owner, self.baseline)

    def test_current_start_and_core_marker_bind_to_candidate_lifetime(self):
        marker = self.marker(log())
        self.assertEqual(marker['main_native_tid'], 8207)
        self.assertEqual(marker['core_initialized_epoch_ms'], epoch('2026-10-16 20:14:47.910'))
        self.assertGreaterEqual(marker['starting_kodi_epoch_ms'], self.owner['began'])

    def test_device_offset_is_applied_instead_of_host_timezone(self):
        self.baseline['device_utc_offset'] = '+0100'
        self.owner['began'] = epoch('2026-10-16 03:10:10.000')
        marker = self.marker(log('2026-10-16 04:10:10.100', '2026-10-16 04:10:10.998'))
        self.assertEqual(marker['core_initialized_epoch_ms'], epoch('2026-10-16 03:10:10.998'))

    def test_unchanged_retained_log_is_refused_even_if_timestamp_looks_new(self):
        self.baseline['before_log_sha256'] = hashlib.sha256(log().encode()).hexdigest()
        self.assertIsNone(self.marker(log()))

    def test_modified_old_log_cannot_satisfy_new_owner(self):
        self.assertIsNone(self.marker(log('2026-10-16 20:12:34.017', '2026-10-16 20:12:47.910')+'new trailing text'))

    def test_new_start_does_not_borrow_old_or_foreign_thread_core_marker(self):
        self.assertIsNone(self.marker(log(done='2026-10-16 20:12:47.910')))
        self.assertIsNone(self.marker(log().replace('47.910 T:8207', '47.910 T:6851')))
        self.assertIsNone(self.marker(log(done=None)))

    def test_initialize_done_alone_does_not_prove_startup_scope_completed(self):
        self.assertIsNone(self.marker(log().replace('Running the application...', 'not running yet')))
        self.assertIsNone(self.marker(log().replace('47.910 T:8207     info <general>: Running',
                                                   '47.910 T:6448     info <general>: Running')))

    def test_ambiguous_start_markers_and_missing_lifetime_are_refused(self):
        self.assertIsNone(self.marker(log()+log()))
        self.assertIsNone(self.marker(log(), began=0))
        self.assertIsNone(self.marker(log(), began='1792181672503'))

    def test_real_current_thread_and_owner_produce_read_only_gate_evidence(self):
        evidence = self.wait()
        self.assertEqual(evidence['boundary'], 'core-initialized')
        self.assertEqual(evidence['owner'], self.owner['owner'])
        self.assertTrue(evidence['current_native_thread_verified'])
        self.assertTrue(evidence['stale_log_rejected'])
        self.assertNotIn('passed', evidence)
        self.assertNotIn('authorization_consumed', evidence)

    def test_replaced_java_or_native_owner_is_refused_before_close(self):
        with self.assertRaisesRegex(RuntimeError, 'owner changed'):
            self.wait(owner=dict(self.owner, owner='replacement'))
        with self.assertRaisesRegex(RuntimeError, 'owner changed'):
            self.wait(native=dict(self.owner, pid=9999))

    def test_log_read_cannot_cross_owner_change(self):
        reads = iter((self.owner, self.owner, dict(self.owner, owner='replacement'), self.owner))
        with patch.object(upgrade.probe, 'read_json', side_effect=lambda *_:next(reads)), \
                patch.object(upgrade.probe, 'shell', return_value=log()), \
                patch.object(upgrade.time, 'monotonic', return_value=10):
            with self.assertRaisesRegex(RuntimeError, 'owner changed'):
                upgrade.wait_core_initialized(self.owner, self.baseline)

    def test_old_thread_identity_cannot_be_reused_for_new_native_process(self):
        with self.assertRaisesRegex(RuntimeError, 'thread is not owned'):
            self.wait(task='Tgid:\t6448\nPid:\t8207\n')

    def test_bad_device_timezone_fails_before_launch(self):
        with patch.object(upgrade.probe, 'shell', return_value='unknown'):
            with self.assertRaisesRegex(RuntimeError, 'UTC offset unavailable'):
                upgrade.core_boundary_baseline()


class NativeWindowTest(unittest.TestCase):
    def setUp(self):
        self.owner = dict(owner='candidate-owner', pid=8134)
        self.receipt = dict(self.owner, session='current-session', last_native_status=dict(self.owner,
            session='current-session', phase='CHECKPOINT_REQUESTED', elapsed_ms=1475,
            application_core_initialized=True, application_startup_in_progress=False,
            write_admission_started=False, pending_detail='python_persistence_observer_initialization',
            script_persistence=dict(active_writers=41, observed_writers=2)))

    def observe(self, receipt=None, report=None):
        report = {} if report is None else report
        upgrade.observe_native_admission(report, self.receipt if receipt is None else receipt, self.owner)
        return report

    def test_pending_proof_uses_native_phase_not_arbitrary_adb_delay(self):
        report = self.observe()
        self.assertTrue(report['pending_observer_window_verified'])
        self.assertEqual(report['pending_observer_window_evidence']['elapsed_ms'], 1475)
        self.assertNotIn('passed', report)
        self.assertNotIn('authorization_consumed', report)

    def test_old_owner_pid_or_session_cannot_supply_pending_proof(self):
        for target, key, value in (('outer','owner','old'), ('outer','pid',6448),
                                   ('native','owner','old'), ('native','pid',6448),
                                   ('native','session','old-session')):
            receipt = copy.deepcopy(self.receipt)
            (receipt if target == 'outer' else receipt['last_native_status'])[key] = value
            self.assertEqual(self.observe(receipt), {})

    def test_loaded_quiesced_or_not_yet_core_initialized_samples_are_not_reproduction(self):
        for change in ({'phase':'QUIESCE'}, {'write_admission_started':True},
                       {'application_core_initialized':False},
                       {'script_persistence':dict(active_writers=41, observed_writers=41)}):
            receipt = copy.deepcopy(self.receipt)
            receipt['last_native_status'].update(change)
            self.assertFalse(self.observe(receipt).get('pending_observer_window_verified', False))

    def test_diagnostic_cap_does_not_hide_late_pending_phase_proof(self):
        report = {}
        receipt = copy.deepcopy(self.receipt)
        receipt['last_native_status']['application_core_initialized'] = False
        for elapsed in range(40):
            receipt['last_native_status']['elapsed_ms'] = elapsed
            self.observe(receipt, report)
        self.observe(report=report)
        self.assertEqual(len(report['native_admission_samples']), upgrade.NATIVE_ADMISSION_SAMPLE_LIMIT)
        self.assertTrue(report['native_admission_samples_truncated'])
        self.assertTrue(report['pending_observer_window_verified'])
        self.assertEqual(report['pending_observer_window_evidence']['elapsed_ms'], 1475)

    def retrospective(self):
        receipt = copy.deepcopy(self.receipt)
        receipt['total_duration_ms'] = 10100
        receipt['last_native_status'].update(phase='QUIESCE', elapsed_ms=10000, write_admission_started=True,
            script_persistence=dict(active_writers=2, observed_writers=2, initialization_progress=[
                dict(writer_id=0, writer='canonical:service.py', pid=8134, observed=True, stage='complete',
                     elapsed_ms=12000, stage_elapsed_ms=1000)]))
        return receipt

    def test_retrospective_inference_requires_margin_and_bounded_capture_lag(self):
        report = self.observe(self.retrospective())
        evidence = report['pending_observer_window_evidence']
        self.assertTrue(report['pending_observer_window_verified'])
        self.assertEqual(evidence['proof_kind'], 'retrospective_native_monotonic_timing_inference')
        self.assertEqual(evidence['uncertainty_margin_ms'], 250)
        self.assertEqual(evidence['coordinator_capture_lag_upper_bound_ms'], 100)

    def test_retrospective_cannot_borrow_later_admission_or_preclose_completion(self):
        for field, value in (('elapsed_ms',10249), ('stage_elapsed_ms',9750),
                             ('stage_elapsed_ms',13000), ('pid',6448), ('observed',False)):
            receipt = self.retrospective()
            receipt['last_native_status']['script_persistence']['initialization_progress'][0][field] = value
            self.assertFalse(self.observe(receipt).get('pending_observer_window_verified', False))

    def test_slow_or_missing_coordinator_capture_cannot_make_postrequest_writer_appear_early(self):
        for duration in (None, 9999, 10251, True):
            receipt = self.retrospective()
            receipt['total_duration_ms'] = duration
            self.assertFalse(self.observe(receipt).get('pending_observer_window_verified', False))


class ComparisonRouteTest(unittest.TestCase):
    def run_case(self, pending):
        report, events = {}, []
        owner = dict(owner='candidate', pid=8134)
        ready = {identity:{} for identity in upgrade.IDS}
        def close(current, output, **kwargs):
            events.append(('close', kwargs))
            return dict(passed=True, requested_monotonic=15, ready_at_close={},
                        pending_observer_window_verified=pending)
        def shell(*args, **kwargs):
            if args[0] == 'cat':
                identity = args[1].split('/')[-2]
                return '<settings><setting id="retained-proof">'+identity+'</setting></settings>\n'
            return 'Starting activity'
        patches = [patch.object(upgrade, 'core_boundary_baseline', side_effect=lambda:events.append(('baseline',)) or {}),
            patch.object(upgrade, 'wait_owner', return_value=owner),
            patch.object(upgrade, 'wait_core_initialized', side_effect=lambda *_:events.append(('core',)) or {'boundary':'core-initialized'}),
            patch.object(upgrade, 'close', side_effect=close),
            patch.object(upgrade, 'verify_saved_state', side_effect=lambda *_:events.append(('verify_saved',))),
            patch.object(upgrade.probe, 'shell', side_effect=shell),
            patch.object(upgrade.probe, 'wait_ready', return_value=dict(owner='reopened', pid=9000)),
            patch.object(upgrade.probe, 'enable_first_party'), patch.object(upgrade, 'wait_services', return_value=ready),
            patch.object(upgrade.time, 'monotonic', return_value=10)]
        for item in patches: item.start(); self.addCleanup(item.stop)
        if pending:
            upgrade.run_candidate_scenario('early', {'owner':'baseline'}, Path('/unused'), report,
                lambda:None, early_boundary='core-initialized')
        else:
            with self.assertRaisesRegex(AssertionError, 'missed native pending-observer window'):
                upgrade.run_candidate_scenario('early', {'owner':'baseline'}, Path('/unused'), report,
                    lambda:None, early_boundary='core-initialized')
        return report, events

    def test_optional_comparison_requires_core_gate_and_actual_pending_evidence(self):
        report, events = self.run_case(True)
        self.assertEqual(report['early_boundary'], 'core-initialized')
        self.assertLess(events.index(('baseline',)), events.index(('core',)))
        self.assertLess(events.index(('core',)), events.index(('close', {'collect_native_admission':True})))
        self.assertTrue(report['saved_data_reopen_verified'])

    def test_successful_close_does_not_turn_missed_observer_window_into_valid_comparison(self):
        report, events = self.run_case(False)
        self.assertTrue(report['candidate_early_close']['passed'])
        self.assertFalse(any(event[0] == 'verify_saved' for event in events))
        self.assertNotIn('saved_data_reopen_verified', report)


if __name__ == '__main__':
    unittest.main(verbosity=2)
