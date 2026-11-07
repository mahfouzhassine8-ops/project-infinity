"""Owner-selected repair checks only; no Android, provider network or shutdown."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'repairs/infinity-2103460-nine-corrections-20261106'))
sys.path.insert(0,str(ROOT/'repairs/infinity-master-corrective-20261105'))
import test_search_correction
import test_search_cache_race
import test_search_handoff_268
import test_integrated_corrections

suite=unittest.TestSuite()
# Retain original evidence. These two old assertions describe the pre-cache-
# race implementation / old function inventory, not this reviewed correction.
# CacheRace and the source inventory test below cover their current contracts.
excluded={'test_cache_hit_race_rejected_without_reissuing_provider',
          'test_only_two_search_functions_and_rejection_diagnostic_changed'}
for name in unittest.defaultTestLoader.getTestCaseNames(test_search_correction.SearchCorrection):
    if name not in excluded:suite.addTest(test_search_correction.SearchCorrection(name))
for case in (test_search_cache_race.CacheRace,test_search_handoff_268.Host,
             test_integrated_corrections.ProviderDispatch,
             test_integrated_corrections.WatchedActions,
             test_integrated_corrections.SkinAndProtectedPasses):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
print('Selected current Search validator/cache/handoff, Info, watched and protected-pass checks.\n'
      'Known benign settings acceptance and actual Android/native crash remain UNRESOLVED/NOT_RUN.',flush=True)
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
