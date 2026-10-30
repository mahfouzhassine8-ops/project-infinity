"""Prepare ONLY the explicitly selected frozen432 observational control.

This is a separate fixed-binary admission, never a bypass/override of the current
prototype source guards in prepare.py or prepare_release.py.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
OWNER=HERE.parents[1]
REPO=OWNER.parents[2]
NS='{http://maven.apache.org/POM/4.0.0}'
PRODUCTION='926bcc3bcc3b78d424742af38116d86f1f71367e1e429828e42f10e618cea92e'
SUPPORT='016a9ca405468cbc86fb6da8634e943ada67ffa615a3b804a1d9680fca84f1ad'
DEX={'part-0.dex':'47c9635ce03485013d19200db15ee7a703d5e4368197f35f084d0cc9a8afcde6','part-1.dex':'3360d86366c77771c21af868db10dabe95503fd876977c5ecf201a32af2c384e'}
METHOD='nativeSigned432SingleBindSelectionControl'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text())
def prepare(protected_host,out):
 protected_host=protected_host.resolve();out=out.resolve();assert not out.exists()
 bindings=load(protected_host/'SOURCE-BINDINGS.json');assert bindings['production_jar_sha256']==sha(protected_host/'production.jar')==PRODUCTION;assert bindings['support_jar_sha256']==sha(protected_host/'support.jar')==SUPPORT
 assert bindings['owner_DEX_sha256']==DEX and bindings['owner_BUILD']['candidate_component_version']=='2103432.cobra.1'
 proof=protected_host/'INDEPENDENT-CANONICAL-RESULT.json';assert sha(proof)==bindings['canonical_chain']['independent_proof_sha256'];canonical=load(proof);assert canonical['new_DEX_sha256']==DEX and canonical['status']=='PASS_EXACT_FIVE_CLASS_DELTA'
 assert sha(protected_host/'OWNER-BUILD.json')==bindings['owner_BUILD_sha256'];assert sha(protected_host/'pom.xml')==bindings['pom_sha256']
 out.mkdir(parents=True)
 for n in ('production.jar','support.jar'):shutil.copyfile(protected_host/n,out/n)
 shutil.copytree(protected_host/'android-test-libs',out/'android-test-libs')
 sources=[HERE/'CobraCardsSigned432SelectionControlTest.java',HERE/'CobraCardsVisualCloseoutTest.java',OWNER/'layout-qa/CobraCardsLayoutTest.java'];target=out/'src/test/java/com/projectinfinity/kodi';target.mkdir(parents=True)
 for p in sources:shutil.copyfile(p,target/p.name)
 ET.register_namespace('',NS[1:-1]);root=ET.fromstring((protected_host/'pom.xml').read_text());nodes=root.findall('.//'+NS+'systemPropertyVariables');assert len(nodes)==1
 for name,value in {'cards.closeout.output':str(out/'measurements'),'cards.layout.output':str(out/'measurements')}.items():ET.SubElement(nodes[0],NS+name).text=value
 (out/'pom.xml').write_text(ET.tostring(root,encoding='unicode').replace(str(protected_host),str(out))+'\n')
 selection={'class':'CobraCardsSigned432SelectionControlTest','methods':[METHOD],'recorded_before_execution':True,'scope':'Root explicitly approved observational protected432 same-sequence control; no current-height expectations or app/global changes'}
 inputs={'phase':'PROTECTED432_FIXED_BINARY_OBSERVATIONAL_CONTROL','production_jar_sha256':PRODUCTION,'support_jar_sha256':SUPPORT,'actual_owner_DEX_sha256':DEX,'protected_source_bindings_sha256':sha(protected_host/'SOURCE-BINDINGS.json'),'canonical_proof_sha256':sha(proof),'test_sources':{str(p.relative_to(REPO)):sha(p) for p in sources},'test_sha256':sha(sources[0]),'prepare_sha256':sha(Path(__file__)),'selected_methods':[METHOD],'historical_tests':'COMPILED_ONLY_NOT_SELECTED','behavior':'NOT_RUN','shutdown':'NOT_RUN','physical_Fold':'NOT_RUN'}
 (out/'SELECTION.json').write_text(json.dumps(selection,indent=2)+'\n');(out/'INPUTS.json').write_text(json.dumps(inputs,indent=2)+'\n');print('Prepared one protected432 observational method; no execution')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--protected-host',type=Path,required=True);p.add_argument('--out',type=Path,required=True);prepare(**vars(p.parse_args()))
