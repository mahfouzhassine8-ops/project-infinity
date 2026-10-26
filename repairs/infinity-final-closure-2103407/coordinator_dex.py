"""Exact410 coordinator dispatch correction; preserve every other DEX definition."""
import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
from zipfile import ZipFile

from module_dex import methods, once, run, sha, strings, ROOT, HERE

TARGET='com/projectinfinity/kodi/InfinityCloseGuardService.smali'
METHOD='lambda$checkOwner$17$com-projectinfinity-kodi-InfinityCloseGuardService(Lorg/json/JSONObject;Lcom/projectinfinity/kodi/InfinityCloseGuardService$Session;)V'
CLASS='Lcom/projectinfinity/kodi/InfinityCloseGuardService;'
FIELD='    iget-object p1, p0, '+CLASS+'->ui:Landroid/os/Handler;'
WORKER='    iget-object p1, p0, '+CLASS+'->worker:Ljava/util/concurrent/ExecutorService;'
POST='    invoke-virtual {p1, v0}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z'
EXECUTE='    invoke-interface {p1, v0}, Ljava/util/concurrent/ExecutorService;->execute(Ljava/lang/Runnable;)V'


def plan():return json.loads((HERE/'COORDINATOR-2103411-PLAN.json').read_text())


def patch(text):
    ownership=plan()['ownership']
    if sha(text.encode())!=ownership['class_preimage_sha256']:
        raise ValueError('Exact signed410 coordinator class required')
    old=methods(text);body=old[METHOD]
    if sha(body.encode())!=ownership['method_preimage_sha256']:
        raise ValueError('Exact signed410 completion dispatch required')
    success,failure=body.split('    :catch_0\n',1)
    success=once(success,FIELD,WORKER)
    success=once(success,POST,EXECUTE)
    changed=success+'    :catch_0\n'+failure
    return once(text,body,changed)


def prepare(apk,jars,java,javac,out):
    apk,jars,out=map(Path,(apk,jars,out))
    ownership=plan()['ownership']
    if out.exists():raise ValueError('Fresh DEX output required')
    if sha(apk.read_bytes())!=ownership['parent_apk_sha256']:
        raise ValueError('Exact signed410 APK required')
    pins=json.loads((ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    if {p.name:sha(p.read_bytes()) for p in jars.glob('*.jar')}!=pins:
        raise ValueError('Unverified DEX tools')
    cp=os.pathsep.join(str(p.resolve()) for p in sorted(jars.glob('*.jar')))
    with ZipFile(apk) as archive:original=archive.read('classes.dex')
    if sha(original)!=ownership['parent_dex_sha256']:raise ValueError('Exact410 DEX required')
    out.mkdir(parents=True);(out/'original.dex').write_bytes(original)
    run([java,'-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',out/'original.dex','-o',out/'original-smali'])
    before={p.relative_to(out/'original-smali').as_posix():p.read_text() for p in (out/'original-smali').rglob('*.smali')}
    old=before[TARGET];changed=patch(old)
    modified=out/'modified-smali';shutil.copytree(out/'original-smali',modified);(modified/TARGET).write_text(changed)
    (out/'COORDINATOR.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),changed.splitlines(True),'signed410/'+TARGET,'candidate411/'+TARGET)))
    assembled=out/'assembled.dex'
    run([java,'-cp',cp,'org.jf.smali.Main','assemble','--api','21',modified,'-o',assembled])
    adapter=(ROOT/'repairs/universal-persistence-2103401/PreserveReceiptDex.java').read_text()
    adapter=once(adapter,'return name.equals("Lcom/projectinfinity/kodi/InfinityCheckpointReceipt;") || name.equals("Lcom/projectinfinity/kodi/InfinityCheckpointReceipt$Descriptor;");','return false;')
    adapter=once(adapter,'        ExactValuePool pool = new ExactValuePool(originalDex.getOpcodes());',
        '        ExactValuePool pool = new ExactValuePool(originalDex.getOpcodes());\n'
        '        for (org.jf.dexlib2.iface.reference.StringReference value :\n'
        '                ((org.jf.dexlib2.dexbacked.DexBackedDexFile)originalDex).getStringReferences())\n'
        '            pool.stringSection.intern(value.getString());')
    file=out/'adapter/PreserveReceiptDex.java';file.parent.mkdir();file.write_text(adapter)
    adapterclasses=out/'adapter-classes';adapterclasses.mkdir()
    run([javac,'--release','8','-g:none','-cp',cp,'-d',adapterclasses,file])
    final=out/'classes.dex'
    log=run([java,'-cp',str(adapterclasses)+os.pathsep+cp,'org.jf.dexlib2.writer.pool.PreserveReceiptDex',out/'original.dex',assembled,final,'21'])
    (out/'FIELD-PRESERVATION.txt').write_text(log)
    if 'PRESERVED_CLASSES='+str(len(before)-1) not in log:raise ValueError('Protected field inventory incomplete')
    run([java,'-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',final,'-o',out/'verified-smali'])
    after={p.relative_to(out/'verified-smali').as_posix():p.read_text() for p in (out/'verified-smali').rglob('*.smali')}
    if set(before)!=set(after) or [n for n in before if before[n]!=after[n]]!=[TARGET]:
        raise ValueError('Protected DEX definitions changed')
    if after[TARGET]!=changed or methods(old).keys()!=methods(changed).keys():
        raise ValueError('Unowned coordinator change')
    for name,body in methods(old).items():
        if name!=METHOD and methods(changed)[name]!=body:raise ValueError('Other method changed: '+name)
    if strings(final.read_bytes())!=strings(original):raise ValueError('Protected string indices changed')
    report=dict(status='PASS_EXACT_DEX_DEFINITIONS',parent_dex_sha256=sha(original),
        final_dex_sha256=sha(final.read_bytes()),changed_classes=[TARGET],changed_method=METHOD,
        changed_instructions=2,protected_classes=len(before)-1,added_classes=[],
        class_and_method_inventory_identical=True,original_string_pool_and_indices_identical=True,
        all_other_disassemblies_byte_identical=True,authorization_receipt_and_failure_methods_unchanged=True,
        Cobra_classes_changed=[],runtime_Android17='NOT RUN',physical_Fold='NOT RUN')
    (out/'DEX-COORDINATOR-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('apk','jars','java','javac','out'):parser.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(prepare(**vars(parser.parse_args())),indent=2))
