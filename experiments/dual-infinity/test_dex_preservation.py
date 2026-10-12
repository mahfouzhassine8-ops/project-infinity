import struct
import unittest
from dex_preservation import simple_code


class SyntheticPreservationTests(unittest.TestCase):
    def invoke(self, index):
        units = [0x0071, index, 0, 0x000e]
        return struct.pack('<HHHHII', 1, 0, 0, 0, 0, len(units)) + struct.pack('<4H', *units)

    def test_reference_renumbering_preserves_same_callback(self):
        target = ('Lowner;', b'save', ('V', ()))
        old = simple_code(self.invoke(0), 0, [], [], [], [target], 'LlambdaOld;')
        new = simple_code(self.invoke(1), 0, [], [], [], [('Lother;', b'other', ('V', ())),target], 'LlambdaNew;')
        self.assertEqual(old, new)

    def test_changed_callback_target_is_not_equivalent(self):
        old = simple_code(self.invoke(0), 0, [], [], [], [('Lowner;', b'save', ('V', ()))], 'Llambda;')
        wrong = simple_code(self.invoke(0), 0, [], [], [], [('Lowner;', b'cancel', ('V', ()))], 'Llambda;')
        self.assertNotEqual(old, wrong)

    def test_unknown_instruction_and_exception_handler_are_refused(self):
        data = bytearray(self.invoke(0)); data[16] = 0xff
        with self.assertRaises(ValueError): simple_code(data, 0, [], [], [], [('Lowner;', b'save', ('V', ()))], 'Llambda;')
        data = bytearray(self.invoke(0)); data[6] = 1
        with self.assertRaises(ValueError): simple_code(data, 0, [], [], [], [('Lowner;', b'save', ('V', ()))], 'Llambda;')


if __name__ == '__main__': unittest.main()
