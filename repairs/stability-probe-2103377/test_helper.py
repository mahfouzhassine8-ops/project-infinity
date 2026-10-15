import ast,hashlib,importlib.util,json,tempfile,types,unittest,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stability_export',HERE/'helper/resources/lib/stability_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

class TraceTests(unittest.TestCase):
    def test_only_native_rails_requests_are_logged(self):
        for request,expected in [('r1',2),('r123456',2),('n1',0),('r../x',0),('',0),('r'+'1'*21,0)]:
            rows=[];xb=types.SimpleNamespace(LOGINFO=1,log=lambda message,level:rows.append(message))
            trace=probe.RailTrace({'infinity_trace':[request]},'movies',xb);trace.mark('data_ready',3)
            self.assertEqual(len(rows),expected)
            for row in rows:
                data=json.loads(row.split(' ',1)[1]);self.assertEqual(data['request'],request);self.assertNotIn('url',data)

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for name in ['temp','profile','log','addons']: (self.root/name).mkdir()
        for aid in ['skin.infinity.diggz','script.infinity.rails','script.infinity.commandcenter','plugin.video.umbrella','script.trakt']:
            d=self.root/'addons'/aid;d.mkdir();(d/'addon.xml').write_text('<addon id="'+aid+'"/>')
        (self.root/'addons/plugin.video.umbrella/service.py').write_text('print("public code")')
        (self.root/'addons/plugin.video.umbrella/settings.xml').write_text('PRIVATE_SENTINEL')
        (self.root/'temp/infinity-stability-probe.jsonl').write_text('{"schema":1}\n')
        (self.root/'log/kodi.log').write_text('ordinary PRIVATE_SENTINEL\nINFINITY_RAIL_TIMING {"stage":"helper_start"}\n')
        root=self.root
        class Addon:
            def __init__(self,aid):self.aid=aid
            def getAddonInfo(self,key):return str(root/'addons'/self.aid) if key=='path' else 'fixture'
        self.xa=types.SimpleNamespace(Addon=Addon)
        self.vfs=types.SimpleNamespace(translatePath=lambda p:p.replace('special://temp/',str(root/'temp')+'/').replace('special://profile/',str(root/'profile')+'/').replace('special://logpath/',str(root/'log')+'/'))
    def test_export_is_read_only_and_excludes_settings_and_unfiltered_logs(self):
        secret=self.root/'addons/plugin.video.umbrella/settings.xml';before=secret.read_bytes()
        path=self.root/'capture.zip';result=probe.collect(self.xa,self.vfs,path)
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip());self.assertTrue(all('settings.xml' not in n for n in z.namelist()))
            self.assertTrue(all(b'PRIVATE_SENTINEL' not in z.read(n) for n in z.namelist()))
            self.assertEqual(z.read('native/infinity-stability-probe.jsonl'),b'{"schema":1}\n')
        self.assertEqual(secret.read_bytes(),before)
        h=result['installed']['plugin.video.umbrella']['hashes']['service.py']
        self.assertEqual(h,hashlib.sha256((self.root/'addons/plugin.video.umbrella/service.py').read_bytes()).hexdigest())
    def test_unavailable_files_are_explicit_not_passes(self):
        result=probe.collect(self.xa,self.vfs,self.root/'capture.zip')
        self.assertIn('checkpoint/coordinator-receipt.json',result['unavailable'])
        self.assertFalse(result['physical_acceptance'])
    def test_oversized_evidence_is_not_silently_truncated(self):
        (self.root/'temp/infinity-stability-probe.jsonl').write_bytes(b'x'*(768*1024+1))
        result=probe.collect(self.xa,self.vfs,self.root/'capture.zip')
        self.assertIn('native/infinity-stability-probe.jsonl: exceeds cap',result['unavailable'])

class PreservationTests(unittest.TestCase):
    def test_locked_helper_store_catalog_mocha_and_defaults_are_byte_identical(self):
        manifest=json.loads((HERE/'HELPER-025-HASHES.json').read_text())
        allowed={'addon.xml','resources/lib/runtime.py','resources/lib/stability_probe.py'}
        for p in (HERE/'helper').rglob('*'):
            if p.is_file() and '__pycache__' not in str(p):
                name=str(p.relative_to(HERE/'helper'))
                if name not in allowed:self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),manifest['files'][name],name)
        source=(HERE/'helper/resources/lib/runtime.py').read_bytes()
        lines=source.splitlines(keepends=True)
        # ast.dump is not stable across Python versions (3.12 adds type_params).
        # Hash the exact approved method source, including its comments instead.
        methods={n.name:hashlib.sha256(b''.join(lines[n.lineno-1:n.end_lineno])).hexdigest()
            for n in ast.parse(source.decode('utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        for name,value in manifest['unchanged_runtime_source_sha256'].items():self.assertEqual(methods[name],value,name)

if __name__=='__main__':unittest.main()
