"""Focused auditor fixture, with no Android/application or owner-data access."""
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1] / "build_dex.py"
spec = importlib.util.spec_from_file_location("lock_dex_builder", SOURCE)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class LabelDefinitionParsing(unittest.TestCase):
    def test_repeated_switch_references_are_legal_but_duplicate_definitions_are_not(self):
        original = '''.method private sample(I)Z
    .registers 3
    .line 40
    const-string v0, ":pswitch_a"
    packed-switch p1, :pswitch_data_20
    :pswitch_a
    return p1
    :pswitch_data_20
    .packed-switch 0x1
        :pswitch_a
        :pswitch_a
    .end packed-switch
.end method'''
        shifted = original.replace(":pswitch_data_20", ":pswitch_data_23").replace(
            "    :pswitch_a", "    :pswitch_d").replace(".line 40", ".line 44")
        self.assertEqual(builder.normalize(original), builder.normalize(shifted))
        changed_constant = shifted.replace('":pswitch_a"', '":pswitch_d"')
        self.assertNotEqual(builder.normalize(original), builder.normalize(changed_constant))
        duplicate = original.replace("    return p1", "    :pswitch_a\n    return p1")
        with self.assertRaisesRegex(RuntimeError, "Duplicate method label"):
            builder.normalize(duplicate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
