"""Only package identity and unexplained-member rejection; no app acceptance."""
from io import BytesIO
import struct
import unittest
from zipfile import ZipFile
import package_search_query_cache as package


class QueryCachePackagingTests(unittest.TestCase):
    def test_only_exact_typed_version_field_can_change(self):
        raw=b'prefix\x08\x00\x00\x10'+struct.pack('<I',2103417)+b'suffix'
        self.assertEqual(package.manifest(raw),raw[:-10]+struct.pack('<I',2103418)+b'suffix')
        for invalid in (raw+raw,raw.replace(b'\x10',b'\x03'),raw+struct.pack('<I',2103418)):
            with self.assertRaises(ValueError):package.manifest(invalid)

    def test_each_unowned_difference_and_missing_required_delta_refuses_package(self):
        def archive(values):
            stream=BytesIO()
            with ZipFile(stream,'w') as z:
                for name,raw in values.items():z.writestr(name,raw)
            return ZipFile(stream)
        old={n:b'original'+n.encode() for n in package.OWNED}
        old.update({'classes.dex':b'original DEX','classes2.dex':b'original DEX2',
                    'lib/arm64-v8a/libkodi.so':b'original full native','unowned/chooser':b'original chooser'})
        changes={n:b'new'+n.encode() for n in package.OWNED}
        new=dict(old,**changes)
        with archive(old) as before,archive(new) as after:
            result=package.compare(before,after,changes)
            self.assertEqual(result['preserved_parent_members'],4)
            self.assertEqual(set(result['explained_differences']),package.OWNED)
        for bad in (dict(new,**{'classes.dex':b'other DEX'}),dict(new,**{'unowned/chooser':b'changed'}),
                    {n:v for n,v in new.items() if n!='classes2.dex'},dict(new,extra=b'unowned'),
                    dict(new,**{next(iter(package.OWNED)):old[next(iter(package.OWNED))]})):
            with archive(old) as before,archive(bad) as after:
                with self.assertRaises(ValueError):package.compare(before,after,changes)


if __name__=='__main__':unittest.main(verbosity=2)
