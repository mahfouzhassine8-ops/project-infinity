import unittest
from bytecode_guard import normalize


class EncodingProofTest(unittest.TestCase):
    def test_string_width_keeps_value_and_register(self):
        self.assertEqual(normalize('    const-string v1, "same"'), normalize('    const-string/jumbo v1, "same"'))
        self.assertNotEqual(normalize('    const-string v1, "same"'), normalize('    const-string/jumbo v2, "same"'))
        self.assertNotEqual(normalize('    const-string v1, "same"'), normalize('    const-string/jumbo v1, "changed"'))

    def test_only_unreachable_unlabelled_payload_padding_is_removed(self):
        old = '    return-void\n\n    :pswitch_data_0\n    .packed-switch 0x0\n        :pswitch_0\n    .end packed-switch\n'
        new = old.replace('return-void\n', 'return-void\n    nop\n')
        self.assertEqual(normalize(old), normalize(new))
        self.assertNotEqual(normalize(old), normalize(new.replace('    nop', '    :cond_0\n    nop')))
        self.assertNotEqual(normalize(old), normalize(new.replace('return-void', 'const/4 v0, 0x0')))

    def test_branch_catch_switch_and_executable_nop_preserved(self):
        samples = ['if-eqz v0, :cond_0', '.catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0', ':pswitch_0', 'nop\nreturn-void']
        for sample in samples:
            self.assertNotEqual(normalize(sample), normalize(sample.replace('0', '1') if '0' in sample else sample.replace('nop', '')))

    def test_no_normalization_inside_literals(self):
        text = '    const-string v0, "const-string/jumbo nop :cond_0"'
        self.assertEqual(text, normalize(text))


if __name__ == '__main__':
    unittest.main()
