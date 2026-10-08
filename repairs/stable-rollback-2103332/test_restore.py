#!/usr/bin/env python3
"""Fail-closed metadata and ZIP validation tests on the exact original manifest."""
import io,os,struct,unittest,zipfile
from pathlib import Path
import restore as r
BASE=Path(os.environ['RESTORE_BASE_APK'])
class RestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(BASE) as z:cls.original=z.read(r.MANIFEST)
    def test_original_identity(self):
        f=r.axml(self.original);self.assertEqual((f['versionCode']['data'],f['package']['value']),(2103327,r.PACKAGE))
    def test_new_identity(self):
        f=r.axml(r.patch_manifest(self.original));self.assertEqual((f['versionCode']['data'],f['versionName']['value']),(2103332,r.NEW_NAME))
    def test_two_fields_only(self):
        b=bytearray(r.patch_manifest(self.original));f=r.axml(b);struct.pack_into('<I',b,f['versionCode']['offset']+16,2103327)
        a,e=f['versionName']['text_range'];b[a:e]=r.OLD_NAME.encode('utf-16le');self.assertEqual(bytes(b),self.original)
    def test_refuse_second_restamp(self):
        with self.assertRaises(ValueError):r.patch_manifest(r.patch_manifest(self.original))
    def test_refuse_wrong_package(self):
        b=bytearray(self.original);a,e=r.axml(b)['package']['text_range'];b[a:a+2]=b'x\0'
        with self.assertRaises(ValueError):r.patch_manifest(bytes(b))
    def test_refuse_wrong_version(self):
        b=bytearray(self.original);struct.pack_into('<I',b,r.axml(b)['versionCode']['offset']+16,2103330)
        with self.assertRaises(ValueError):r.patch_manifest(bytes(b))
    def test_refuse_nonincreasing_version(self):
        with self.assertRaises(ValueError):r.patch_manifest(self.original,2103327)
    def test_refuse_resized_version_name(self):
        with self.assertRaises(ValueError):r.patch_manifest(self.original,name='different')
    def test_refuse_truncated_xml(self):
        with self.assertRaises(ValueError):r.axml(self.original[:-1])
    def test_refuse_wrong_xml_kind(self):
        with self.assertRaises(ValueError):r.axml(b'\0\0'+self.original[2:])
    def test_refuse_duplicate_zip_entries(self):
        f=io.BytesIO()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(f,'w') as z:z.writestr('a','one');z.writestr('a','two')
        with zipfile.ZipFile(f) as z:
            with self.assertRaises(ValueError):r.valid_zip(z)
    def test_refuse_path_traversal(self):
        f=io.BytesIO()
        with zipfile.ZipFile(f,'w') as z:z.writestr('../bad','one')
        with zipfile.ZipFile(f) as z:
            with self.assertRaises(ValueError):r.valid_zip(z)
if __name__=='__main__':unittest.main(verbosity=2)
