"""Preservation and inherited Experience checks against exact .173 (not .174)."""
import argparse,hashlib,importlib.util,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from lxml import etree as E

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert hashlib.sha256(a.parent.read_bytes()).hexdigest()=='e70cbcc974dbb646c4061432ce458d513911108aad943cddcc663dc7b937b98e'
    with zipfile.ZipFile(a.parent) as z:old={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(a.candidate) as z:new={n:z.read(n) for n in z.namelist()}
    assert not old.keys()-new.keys()
    prefix='skin.infinity.diggz/'
    # Every legacy action/visibility/geometry/video control survives verbatim as
    # an XML tree; only newly allocated IDs and observer-owned nodes are removed.
    checked=[]
    for name in old:
        if name.endswith('/Home.xml') or name.endswith('/Includes_InfinityHomePlayback.xml'):
            before=E.fromstring(old[name]);after=E.fromstring(new[name])
            oldids={n.get('id') for n in before.iter('control')}
            for node in list(after):
                if node.tag in ('onload','onunload') and 'NativeAmbient' in (node.text or ''):after.remove(node)
                elif node.tag=='onload' and 'infinity_native_ambient.py' in (node.text or ''):after.remove(node)
            for node in list(after.iter('control')):
                if node.get('id')=='39799' or node.findtext('description')=='Infinity native video light on existing material':node.getparent().remove(node)
                elif node.get('id') and node.get('id') not in oldids and 39000<=int(node.get('id'))<45000:del node.attrib['id']
            assert E.tostring(before)==E.tostring(after),name
            checked.append(name)
    protected=[n for n in old if any(key in n for key in ('FullscreenVideo','VideoOSD','Custom_1190','Custom_1191','Custom_1194','Custom_1198','Includes_InfinityExperience','Includes_InfinityHomeUnified'))]
    for n in protected:assert old[n]==new[n],n
    manifests=json.loads(new[prefix+'Infinity-Protected-Manifest.json'])
    for n,digest in manifests['protected_files'].items():assert hashlib.sha256(new[prefix+n]).hexdigest()==digest,n
    # Run the original .173 runtime tests unchanged against the unchanged
    # Command Center, plus applicable skin contracts against the new skin.
    # Two .172->.173 geometry comparisons are replaced above with .173->.175
    # structural preservation, since new observer controls are intentional.
    with tempfile.TemporaryDirectory(prefix='infinity-nine-regression-') as td:
        dest=Path(td)
        with zipfile.ZipFile(a.candidate) as z:z.extractall(dest)
        tests=a.reference/'infinity-nine-tests/test_experience.py'
        source=tests.read_text().replace("ADDON=ROOT/'infinity-nine/script.infinity.commandcenter'",'ADDON=Path('+repr(str((a.reference/'payload/script.infinity.commandcenter').resolve()))+')')
        source=source.replace("SKIN=ROOT/'infinity-nine/skin.infinity.diggz'",'SKIN=Path('+repr(str(dest/'skin.infinity.diggz'))+')')
        ns={'__name__':'inherited_experience_tests','__file__':str(tests.resolve())};exec(compile(source,str(tests),'exec'),ns)
        loader=unittest.TestLoader();suite=unittest.TestSuite([loader.loadTestsFromTestCase(ns['RuntimeTests'])])
        replaced={'test_existing_home_controls_and_actions_are_preserved','test_player_and_navigation_files_are_byte_identical'}
        for name in loader.getTestCaseNames(ns['SkinContractTests']):
            if name not in replaced:suite.addTest(ns['SkinContractTests'](name))
        a.out.mkdir(parents=True,exist_ok=True)
        with (a.out/'experience-regression.txt').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        assert result.wasSuccessful(),(len(result.failures),len(result.errors))
    controller=a.reference/'payload/script.infinity.commandcenter'
    report={'inherited_experience_tests_passed':result.testsRun,'inherited_test_logic_unchanged':True,'superseded_172_geometry_tests_replaced_by_exact_173_preservation':sorted(replaced),'original_control_trees_preserved':checked,'protected_feature_navigation_player_files_byte_identical':protected,'all_other_files_byte_identical':sum(old[n]==new[n] for n in old),'command_center_source_hashes':{str(n.relative_to(controller)):hashlib.sha256(n.read_bytes()).hexdigest() for n in controller.rglob('*') if n.is_file() and '__pycache__' not in str(n)},'actual_kodi_renderer_verified':False,'physical_fold_verified':False}
    (a.out/'experience-preservation.json').write_text(json.dumps(report,indent=2))
    print('PASS:',result.testsRun,'inherited Experience tests;',len(checked),'original control trees;',len(protected),'protected feature/player/navigation files')
if __name__=='__main__':main()
