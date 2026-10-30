"""Prepare exactly four authorized closeout cases; never compile/run tests."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
OWNER=HERE.parents[1]
REPO=OWNER.parents[2]
NS='{http://maven.apache.org/POM/4.0.0}'
SOURCE='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
APK='3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def load(path):return json.loads(path.read_text())

def prepare(classpath,baseline_results,out,header_weight):
    classpath,baseline_results,out=(p.resolve() for p in (classpath,baseline_results,out))
    scope=load(HERE/'SCOPE.json');assert scope['selected_before_execution']
    assert len(scope['selected_methods'])==4 and len(set(scope['selected_methods']))==4
    assert 100<=header_weight<=1000,'Explicit independently reference-calibrated header weight required'
    manifest=load(classpath/'SOURCE-BINDINGS.json')
    assert manifest['status'].startswith('PASS_FRESH_SOURCE_BOUND_')
    assert manifest['baseline_signed_source']==SOURCE and manifest['baseline_APK_sha256']==APK
    for name,key in [('production.jar','production_jar_sha256'),('support.jar','support_jar_sha256'),('OWNER-BUILD.json','owner_BUILD_sha256'),('pom.xml','pom_sha256'),('HOST-OVERLAY-CLASS-HASHES.json','host_overlay_class_hash_inventory_sha256')]:assert sha(classpath/name)==manifest[key],name
    assert sha(classpath/'INDEPENDENT-CANONICAL-RESULT.json')==manifest['canonical_chain']['independent_proof_sha256']
    assert manifest['canonical_chain']['canonical_unchanged_existing_classes']==7137
    for name,pin in manifest['compiler_source_files'].items():assert sha(REPO/name)==pin,'Prototype stale for source: '+name
    golden=load(baseline_results/'SOURCE-BINDING.json')
    assert golden['baseline_binding']['source_binding']['source']==SOURCE
    assert golden['baseline_binding']['source_binding']['APK_sha256']==APK
    for name,pin in golden['files'].items():assert sha(baseline_results/name)==pin
    assert not out.exists(),'Fresh output; preserve previous evidence'
    out.mkdir(parents=True)
    for name in ('production.jar','support.jar'):shutil.copyfile(classpath/name,out/name)
    shutil.copytree(classpath/'android-test-libs',out/'android-test-libs')
    target=out/'src/test/java/com/projectinfinity/kodi';target.mkdir(parents=True)
    test=HERE/'CobraCardsVisualCloseoutTest.java';fixture=OWNER/'layout-qa/CobraCardsLayoutTest.java'
    for path in (test,fixture):shutil.copyfile(path,target/path.name)
    ET.register_namespace('',NS[1:-1]);root=ET.fromstring((classpath/'pom.xml').read_text());nodes=root.findall('.//'+NS+'systemPropertyVariables');assert len(nodes)==1
    values={'cards.closeout.output':str(out/'measurements'),'cards.layout.output':str(out/'measurements'),
            'cards.closeout.candidate':'true','cards.candidate':'true','cards.layout.baseline':str(baseline_results),
            'cards.closeout.header.weight':str(header_weight)}
    for old in list(nodes[0]):
        if old.tag.rsplit('}',1)[-1] in values:nodes[0].remove(old)
    for name,value in values.items():ET.SubElement(nodes[0],NS+name).text=value
    # Preserve portable project.basedir JAR/library resolution and official deps.
    text=ET.tostring(root,encoding='unicode').replace(str(classpath),str(out))+'\n';(out/'pom.xml').write_text(text)
    selection=dict(**{'class':'CobraCardsVisualCloseoutTest','methods':scope['selected_methods']},recorded_before_execution=True,scope_sha256=sha(HERE/'SCOPE.json'))
    selector='CobraCardsVisualCloseoutTest#'+'+'.join(scope['selected_methods'])
    receipt=dict(phase='CARDS_VISUAL_CLOSEOUT_FOUR_SELECTED_HOST_CASES_NO_EXECUTION',
      trusted_source_bindings_sha256=sha(classpath/'SOURCE-BINDINGS.json'),source_binding=manifest,
      classpath={n:sha(out/n) for n in ('production.jar','support.jar')},test_sha256=sha(test),
      test_sources={str(p.relative_to(REPO)):sha(p) for p in (test,fixture)},
      compiled_fixture_only=str(fixture.relative_to(REPO)),selected_methods=scope['selected_methods'],
      header_weight=header_weight,baseline_reference_sha256=sha(baseline_results/'SOURCE-BINDING.json'),
      scope_sha256=sha(HERE/'SCOPE.json'),prepare_sha256=sha(Path(__file__)),pom_sha256=sha(out/'pom.xml'),
      maven_selector=selector,behavior='NOT_RUN',APK='NOT_BUILT',shutdown='NOT_RUN',physical_Fold='NOT_RUN')
    (out/'INPUTS.json').write_text(json.dumps(receipt,indent=2)+'\n');(out/'SELECTION.json').write_text(json.dumps(selection,indent=2)+'\n')
    print('Prepared exact four-method selector: '+selector+'; no compilation/execution')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('classpath','baseline-results','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--header-weight',type=int,required=True);prepare(**vars(p.parse_args()))
