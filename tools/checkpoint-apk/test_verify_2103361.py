#!/usr/bin/env python3
import io,zipfile,unittest
from unittest.mock import patch
import verify_2103361 as verify

def archive(entries):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:
  for k,v in entries.items():z.writestr(k,v)
 return zipfile.ZipFile(b)
class Preservation(unittest.TestCase):
 def test_protected_payload_and_inventory_drift_rejected(self):
  entries={'AndroidManifest.xml':b'version 3361','classes.dex':b'generated identity','assets/skin.xml':b'preserved skin','lib/arm64-v8a/libkodi.so':b'old runtime'}
  with patch.object(verify,'dex_contract',return_value=(set(),{'Main'})):
   with archive(entries) as a,archive(dict(entries,**{'AndroidManifest.xml':b'version 3362','lib/arm64-v8a/libkodi.so':b'repaired runtime'})) as b:verify.compare(a,b)
   for changed in [dict(entries,**{'assets/skin.xml':b'regression'}),dict(entries,**{'assets/unrelated':b'new'})]:
    with archive(entries) as a,archive(changed) as b:
     with self.assertRaises(RuntimeError):verify.compare(a,b)
if __name__=='__main__':unittest.main()
