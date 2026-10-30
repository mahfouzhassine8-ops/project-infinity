"""Independently bind actual owner DEX to accepted431 class/method budgets.

No app, lifecycle, shutdown or signing execution. The pinned canonical DEX
comparison is independent of dex2jar's JVM temporary-register allocation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
APP='Lcom/projectinfinity/kodi/'
EXISTING={APP+n+';' for n in ('InfinityLiveActivity','InfinityLiveActivity$CobraPosterChannelCard',
    'InfinityCobraFeatureRuntime','CobraLogoRequests','CobraComponent')}
NEW_ROOTS={APP+n for n in ('CobraCardsTiles','CobraCardsLayout','CobraProfileDataReuse','CobraCardsReuse')}
PATTERN=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def collect(folder):
    result={}
    for p in folder.rglob('*.smali'):
        raw=p.read_text();name=raw.splitlines()[0].split()[-1]
        assert name not in result,'Duplicate class '+name
        result[name]=raw
    return result


def methods(text):return {m[1]:m[0]+'\n' for m in PATTERN.finditer(text)}


def verify(work,bundles,jars,canonical_leaf='independent-canonical',receipt_leaf='INDEPENDENT-CANONICAL-RESULT.json'):
    work,bundles,jars=(p.resolve() for p in (work,bundles,jars))
    build=json.loads((work/'BUILD.json').read_text());recovery=json.loads((HERE/'BASELINE.json').read_text())
    assert build['baseline_signed_source']==recovery['signed_source']=='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
    for name,pin in recovery['component_sha256'].items():assert sha(bundles/name)==pin,'Accepted431 component differs: '+name
    with ZipFile(bundles/'COBRA.zip') as z:meta=json.loads(z.read('component.json'))
    old=collect(work/'baseline/COBRA')
    authenticated={k[6:]:v['sha256'] for k,v in meta['payload'].items() if k.startswith('class:')}
    assert set(old)==set(authenticated)
    assert all(hashlib.sha256(v.encode()).hexdigest()==authenticated[k] for k,v in old.items()),'Accepted class preimage differs'
    pins=json.loads((HERE.parents[2]/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    assert {p.name:sha(p) for p in jars.glob('*.jar')}==pins
    assert canonical_leaf in {'independent-canonical','package-canonical'}
    assert receipt_leaf in {'INDEPENDENT-CANONICAL-RESULT.json','PACKAGE-CANONICAL-RESULT.json'}
    dest=work/canonical_leaf;assert not dest.exists(),'Fresh independent output required'
    for dex in sorted((work/'owner-dex/COBRA').glob('*.dex')):
        subprocess.run(['java','-cp',str(jars/'*'),'org.jf.baksmali.Main','disassemble','--sequential-labels',str(dex),'-o',str(dest/dex.stem)],check=True)
    actual=collect(dest);assert set(old)<=set(actual),'No original class may disappear'
    changed={k for k in old if old[k]!=actual[k]};added=set(actual)-set(old)
    assert changed==EXISTING
    assert added==set(build['new_classes']) and all(k.split('$')[0].rstrip(';') in NEW_ROOTS for k in added)
    budgets=json.loads((HERE/'CARDS-SOURCE-BUDGET.json').read_text())
    projection=json.loads((HERE/'PROJECTION-SOURCE-BUDGET.json').read_text())
    reuse=json.loads((HERE/'cards-reuse/SOURCE-BUDGET.json').read_text())
    activity_allowed=set(budgets['Activity']['selected_preimages'])|set(projection['changed_methods'])|{'private cobraRefreshProgrammeLabels()V'}|set(reuse['allowed_changed_methods'])
    allowed={APP+'InfinityLiveActivity;':activity_allowed,APP+'InfinityLiveActivity$CobraPosterChannelCard;':set(budgets['Card']['selected_preimages']),
        APP+'InfinityCobraFeatureRuntime;':{'public adultLocked()Z'}}
    changes={}
    for name in changed:
        before,after=methods(old[name]),methods(actual[name]);new_methods=set(after)-set(before)
        assert set(before)<=set(after)
        assert new_methods==({'public static clear(Landroid/app/Activity;Landroid/widget/ImageView;)V'} if name==APP+'CobraLogoRequests;' else set())
        old_meta,new_meta=PATTERN.sub('',old[name]),PATTERN.sub('',actual[name])
        if new_methods:
            # The single admitted added static method contributes two empty
            # separator lines in baksmali. Every nonempty field/annotation/
            # class line still has to match exactly, including indentation.
            assert [line for line in old_meta.splitlines() if line.strip()]==[line for line in new_meta.splitlines() if line.strip()],'Class fields/metadata changed: '+name
        else:
            assert old_meta==new_meta,'Class fields/metadata changed: '+name
        modified={s for s in before if before[s]!=after[s]}
        if name==APP+'CobraComponent;':
            assert actual[name]==old[name].replace('"2103431.cobra.1"','"2103433.cobra.1"'),'Only genuine component version may change'
        elif name==APP+'CobraLogoRequests;':assert not modified,'Existing logo methods remain exact'
        else:assert modified==allowed[name],'Unreviewed method delta: '+name
        changes[name]=sorted(modified|new_methods)
    record={'status':'PASS_EXACT_FIVE_CLASS_DELTA','baseline_signed_source':recovery['signed_source'],
        'baseline_existing_classes':len(old),'unchanged_existing_classes':len(old)-len(changed),'changed_existing_classes':sorted(changed),
        'new_classes':sorted(added),'missing_classes':[],'changed_methods':changes,'unchanged_class_fields_and_annotations':True,
        'new_DEX_sha256':{p.name:sha(p) for p in (work/'owner-dex/COBRA').glob('*.dex')},'build_receipt_sha256':sha(work/'BUILD.json'),
        'compiler_source_files':build['compiler_source_files'],'verifier_source_sha256':sha(Path(__file__)),'APK':'NOT_BUILT','shutdown':'NOT_RUN'}
    (work/receipt_leaf).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('compiler_source_files','new_classes','changed_methods')},indent=2))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('work','bundles','jars'):parser.add_argument('--'+name,type=Path,required=True)
    verify(**vars(parser.parse_args()))
