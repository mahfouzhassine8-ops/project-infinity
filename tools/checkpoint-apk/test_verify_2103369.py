import unittest
from verify_2103369 import compare_smali, OLD_TAG, NEW_TAG


class ImmediateParentTests(unittest.TestCase):
    def fixtures(self):
        old = {'com/projectinfinity/kodi/InfinityHealthExport.smali': 'const-string v0, "' + OLD_TAG + '"\n',
               'com/projectinfinity/kodi/BuildConfig.smali': '.field VERSION_CODE:I = 0x201848\n.field VERSION_NAME:Ljava/lang/String; = "1.0.9-Installer-Close-RC1"\n',
               'com/projectinfinity/kodi/Main.smali': 'invoke-virtual {p0}, saveAllOwners()V\n'}
        new = {name: text.replace(OLD_TAG, NEW_TAG).replace('0x201848', '0x201849').replace('1.0.9-Installer-Close-RC1', '1.0.9-Cancelled-Script-Receipt-RC1') for name, text in old.items()}
        return old, new

    def test_exact_candidate_constants(self):
        old, new = self.fixtures()
        self.assertEqual(compare_smali(old, new)['android_classes_checked'], 3)

    def test_shutdown_instruction_change_is_rejected(self):
        old, new = self.fixtures()
        new['com/projectinfinity/kodi/Main.smali'] = 'return-void\n'
        with self.assertRaisesRegex(RuntimeError, 'instructions changed'):
            compare_smali(old, new)

    def test_exporter_behavior_change_is_rejected(self):
        old, new = self.fixtures()
        new['com/projectinfinity/kodi/InfinityHealthExport.smali'] += 'return-void\n'
        with self.assertRaisesRegex(RuntimeError, 'instructions changed'):
            compare_smali(old, new)

    def test_deleted_class_is_rejected(self):
        old, new = self.fixtures()
        del new['com/projectinfinity/kodi/Main.smali']
        with self.assertRaisesRegex(RuntimeError, 'inventory drift'):
            compare_smali(old, new)


if __name__ == '__main__':
    unittest.main()
