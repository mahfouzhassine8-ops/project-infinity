"""Six selected release-protocol checks only; no application or shutdown test."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile
import yaml
from combined_owners import *
from release_gate import Rejected

class CoordinatedReleaseProtocolTest(unittest.TestCase):
    def bundle(self,root,owner='CHOOSER_SHELL',labels=b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103434\n'):
        source=root/'input.zip';dex=b'HOST_FIXTURE_NOT_AN_APPLICATION_DEX';ui=b'HOST_FIXTURE_FROZEN_CHOOSER_UI'
        files={METADATA:labels,'assets/fixture-chooser-ui':ui}
        meta=dict(owner=owner,version='2103434.version-metadata.1',approved_source='a'*40,settings_schema='fixture-unchanged',
                  dex={'dex/part-0.dex':digest(dex)},members={n:dict(sha256=digest(raw),compress_type=0,external_attr=0) for n,raw in files.items()},
                  payload={'member:'+n:dict(owner=owner,sha256=digest(raw)) for n,raw in files.items()})
        meta['digest']=component_digest(meta['payload'],owner)
        with ZipFile(source,'w') as z:
            z.writestr(record('dex/part-0.dex'),dex)
            for n,raw in files.items():z.writestr(record('payload/'+n),raw)
            z.writestr(record('component.json'),canonical(meta))
        row=dict(file=source.name,sha256=file_sha(source),**{n:meta[n] for n in ('version','digest','approved_source','settings_schema')})
        return source,row

    def test_metadata_updates_only_genuine_labels_and_freezes_every_other_byte(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,row=self.bundle(root);target=root/'CHOOSER_SHELL.zip'
            before=file_sha(source);result=metadata_bundle(source,row,target,'b'*40);read_bundle(target,result)
            self.assertEqual(before,file_sha(source))
            with ZipFile(source) as old,ZipFile(target) as new:
                self.assertEqual(set(old.namelist()),set(new.namelist()))
                self.assertEqual(LABELS,new.read('payload/'+METADATA))
                for name in old.namelist():
                    if name not in ('component.json','payload/'+METADATA):self.assertEqual(old.read(name),new.read(name))

    def test_metadata_refuses_other_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,row=self.bundle(root,owner='INFINITY')
            with self.assertRaisesRegex(Rejected,'VERSION_METADATA_CHOOSER_OWNER_ONLY'):metadata_bundle(source,row,root/'out.zip','b'*40)

    def test_metadata_refuses_stale_or_unverified_label_preimage(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,row=self.bundle(root,labels=b'infinity.last_updated_in=2103426\ncobra.last_updated_in=2103434\n')
            with self.assertRaisesRegex(Rejected,'EXACT_COBRA_ONLY_PREPARED_LABELS'):metadata_bundle(source,row,root/'out.zip','b'*40)

    def test_official_archive_tampering_fails_before_extraction_or_network(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.zip';p.write_bytes(b'altered official archive')
            with mock.patch('combined_owners.subprocess.run',side_effect=AssertionError('No retry/network permitted')):
                with self.assertRaisesRegex(Rejected,'OFFICIAL_ARCHIVE_BYTES'):archive(dict(name='official',digest='sha256:'+'0'*64,id=1),p)
                (Path(temp)/'artifact-1.zip').write_bytes(b'tampered cache')
                with mock.patch.dict(os.environ,{'COORDINATED_ARTIFACT_CACHE':temp}):
                    with self.assertRaisesRegex(Rejected,'OFFICIAL_ARCHIVE_BYTES'):archive(dict(name='official',digest='sha256:'+'0'*64,id=1),Path(temp)/'fresh.zip')

    def test_extracted_evidence_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);z=root/'official.zip';folder=root/'extracted';folder.mkdir();(folder/'receipt.json').write_bytes(b'changed')
            with ZipFile(z,'w') as out:out.writestr('receipt.json',b'original')
            with self.assertRaisesRegex(Rejected,'LOCAL_EVIDENCE_CHANGED'):bind_files(z,folder,{'receipt.json'})

    def test_original_key_roles_remain_conditional_and_after_real_gates(self):
        w=yaml.safe_load((REPO/'.github/workflows/infinity-combined-release.yml').read_text());jobs=w['jobs']
        self.assertEqual({'combined','authenticate-infinity-owner'},set(jobs))
        auth=jobs['authenticate-infinity-owner'];final=jobs['combined']
        self.assertIn("inputs.operation == 'authenticate-infinity-owner'",auth['if']);self.assertIn("github.event_name == 'workflow_dispatch'",auth['if'])
        self.assertIn("inputs.operation == 'final-combined'",final['if'])
        for job,gate in [(auth,'prepare_combined.py precheck'),(final,'Hard pre-sign gate')]:
            steps=job['steps'];keys=[i for i,s in enumerate(steps) if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
            self.assertEqual(1,len(keys));key=keys[0]
            gates=[i for i,s in enumerate(steps) if gate in s.get('name','')+' '+s.get('run','')];self.assertEqual(1,len(gates));self.assertLess(gates[0],key)
        auth_key=next(s for s in auth['steps'] if 'INFINITY_KEYSTORE_B64' in s.get('env',{}))
        self.assertIn('authenticate.py',auth_key['run']);self.assertNotIn('assemble.py',auth_key['run'])
        original=next(s for s in final['steps'] if 'INFINITY_KEYSTORE_B64' in s.get('env',{}));self.assertIn('assemble.py sign',original['run'])
        self.assertTrue(any('register_combined.py check-registered' in s.get('run','') for s in final['steps']))
        self.assertTrue(any('consolidated434/verify_delivery.py' in s.get('run','') for s in final['steps']))

if __name__=='__main__':
    scope=load(HERE/'RELEASE-SCOPE.json');names=scope['selected_protocol_methods']
    assert scope['selected_before_execution'] is True and len(set(names))==6
    suite=unittest.TestSuite(CoordinatedReleaseProtocolTest(name) for name in names)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun!=6 or result.skipped:raise SystemExit(1)
