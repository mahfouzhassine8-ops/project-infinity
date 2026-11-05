"""Focused compile-only authority and real source-restoration checks."""
from pathlib import Path
import ast
import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import compile_only as candidate


class CompilePolicy(unittest.TestCase):
    def test_configuration_recipe_has_no_broad_native_precheck_or_build(self):
        original=candidate.subprocess.check_output(['git','show','HEAD:scripts/infinity_live_app_ci_2.sh'],cwd=candidate.ROOT,text=True)
        if hasattr(candidate,'configure_script'):
            stage=candidate.configure_script(original)
        else:
            # The first job used this exact inherited slicing sequence.
            old='python3 scripts/infinity_gui_render_hardening_v3.py apply --source kodi --receipt engine/gui-render-hardening-source.json'
            stage=original.replace(old,'python3 scripts/infinity_gui_render_hardening_v3.py verify --source kodi')
            start=stage.index('rm -f "$TARBALLS/fontconfig-2.14.0.tar.xz"')
            end=stage.index('make -C target/cmakebuildsys BUILD_DIR="$BUILD_DIR"',start)
            stage=stage[:start]+stage[end:]
            stage=stage[:stage.index('make -C "$BUILD_DIR" -j"$(nproc)"')]
        self.assertNotIn('native-check',stage)
        self.assertNotIn('make -C "$BUILD_DIR"',stage)
        self.assertNotIn(' apk ',stage)
        self.assertIn('-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',stage)

    def test_wrong_repository_or_branch_stops_before_network_and_restore(self):
        for repo,branch in [('other/repo','refs/heads/'+candidate.BRANCH),
                            ('mahfouzhassine8-ops/project-infinity','refs/heads/main')]:
            with patch.dict(os.environ,{'GITHUB_REPOSITORY':repo,'GITHUB_REF':branch}),patch.object(candidate.subprocess,'check_output') as call:
                with self.assertRaises(AssertionError):candidate.metadata()
                call.assert_not_called()

    def test_workflow_never_links_packages_signs_or_runs_application(self):
        workflow=(candidate.ROOT/candidate.WORKFLOW).read_text()
        for required in ('contents: read','actions: read',candidate.BRANCH,'compile_only.py compile',
                         "artifact-ids: '13274901825'","artifact-ids: '11698374892'","NDK_VER: '21.4.7075529'"):
            self.assertIn(required,workflow)
        for forbidden in ('secrets.', 'contents: write','apk -j','apksigner','release452.py','sign-only','adb ', 'shutdown-verification'):
            self.assertNotIn(forbidden,workflow)
        raw=(candidate.HERE/'compile_only.py').read_text()
        module=ast.parse(raw)
        function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='compile_objects')
        body=ast.get_source_segment(raw,function)
        self.assertIn("stage=configure_script(original)",body)
        self.assertIn("assert len(selected)==2",body)
        self.assertIn("'AArch64' in header",body)
        self.assertIn("assert all(actual.get(n)==h for n,h in expected.items())",body)
        self.assertNotIn('compile_engine(',body)

    def test_prerequisites_are_original_external_targets_without_Kodi_source(self):
        native=Path('/isolated/kodi')
        targets=[dict(id='fmt',name='fmt',type='UTILITY'),
                 dict(id='jni',name='libandroidjni',type='UTILITY',dependencies=[{'id':'fmt'}]),
                 dict(id='kodi',name='kodi',type='SHARED_LIBRARY',sources=[{'path':'xbmc/Application.cpp'}])]
        self.assertEqual(candidate.prerequisite_plan(targets,native),['fmt','libandroidjni'])
        targets[1]['dependencies'].append({'id':'kodi'})
        with self.assertRaises(AssertionError):candidate.prerequisite_plan(targets,native)
        targets[1]['dependencies']=[{'id':'fmt'}]
        targets[0]['sources']=[{'path':'xbmc/guilib/Unselected.cpp'}]
        with self.assertRaises(AssertionError):candidate.prerequisite_plan(targets,native)

    def test_exact_reviewed_patch_and_after_bytes_are_fixed(self):
        receipt=json.loads((candidate.HERE/'APPLIED-SOURCE-DELTA.json').read_text())
        self.assertEqual(receipt['reviewed_patch_sha256'],candidate.PATCH_SHA)
        self.assertEqual(len(receipt['changed_files']),2)
        self.assertEqual(receipt['protected_native_sources_byte_identical'],9409)
        for name,row in receipt['changed_files'].items():
            self.assertEqual(candidate.sha(candidate.HERE/'native'/name),row['after_sha256'])
        self.assertEqual(candidate.sha(candidate.HERE/'BASELINE451-RESTORATION.patch'),receipt['baseline_restoration_patch_sha256'])

    def test_actual_verified_archive_restores_frozen451_then_exact_two_file_patch(self):
        # No application run. The real authenticated local archive/map are used;
        # only a disposable source tree is written and removed afterward.
        with tempfile.TemporaryDirectory(prefix='infinity-touch-restore-check-',dir='/tmp') as tmp:
            root=Path(tmp);out=root/'evidence'
            (root/'verified-inputs').symlink_to('/tmp/kodi451-restored-proof',target_is_directory=True)
            dest=root/'repairs/infinity-master-corrective-20261105';dest.mkdir(parents=True)
            (dest/'TOUCH-NATIVE-PROPOSAL.patch').symlink_to(candidate.ROOT/'repairs/infinity-master-corrective-20261105/TOUCH-NATIVE-PROPOSAL.patch')
            with patch.object(candidate,'ROOT',root),patch.object(candidate,'OUT',out):candidate.restore()
            binding=json.loads((out/'SOURCE-BINDING.json').read_text())
            self.assertTrue(binding['full_baseline_match_before_patch'])
            self.assertEqual(binding['reviewed_source_count'],9411)
            self.assertEqual(binding['protected_native_source_count'],9409)
            self.assertEqual(len(binding['changed_files']),2)
            actual=candidate.hashes(root/'kodi')
            expected=json.loads(Path('/tmp/kodi451-restored-proof/BASELINE-NATIVE-SOURCE-MAP.json').read_text())
            self.assertEqual({n for n in actual if actual[n]!=expected[n]},set(binding['changed_files']))
            self.assertFalse(binding['APK_built'])


if __name__=='__main__':unittest.main(verbosity=2)
