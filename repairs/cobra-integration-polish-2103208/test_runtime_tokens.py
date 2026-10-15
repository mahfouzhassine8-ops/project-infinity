"""The eight current-parent DEX markers are all mandatory, not alternatives."""
import unittest
from branding_package import RUNTIME_TOKENS, verify_runtime_tokens

EXPECTED = (
    b'InfinityExtendedBackgroundService', b'InfinityBackgroundControlActivity',
    b'BACKGROUND_MODE_NORMAL', b'BACKGROUND_MODE_EXTENDED', b'InfinityCoreBridge',
    b'InfinityCobraDeviceBridge', b'getPlayWhenReady', b'Turn off',
)

class RuntimeTokenContractTest(unittest.TestCase):
    def test_exact_current_parent_marker_inventory(self):
        self.assertEqual(EXPECTED, RUNTIME_TOKENS)

    def test_all_current_parent_markers_pass(self):
        verify_runtime_tokens(b'\0'.join(EXPECTED))

    def test_each_missing_current_marker_is_rejected(self):
        for missing in EXPECTED:
            with self.subTest(missing=missing):
                joined = b'\0'.join(token for token in EXPECTED if token != missing)
                with self.assertRaisesRegex(RuntimeError, 'Missing source-built runtime'):
                    verify_runtime_tokens(joined)

    def test_obsolete_copy_cannot_replace_any_current_marker(self):
        for missing in EXPECTED:
            with self.subTest(missing=missing):
                joined = b'EXTENDED BACKGROUND MODE\0' + b'\0'.join(token for token in EXPECTED if token != missing)
                with self.assertRaisesRegex(RuntimeError, 'Missing source-built runtime'):
                    verify_runtime_tokens(joined)

if __name__ == '__main__':
    unittest.main(verbosity=2)
