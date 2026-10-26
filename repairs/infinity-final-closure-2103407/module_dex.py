"""One exact407 installer adapter; preserve every other DEX definition/index."""
from __future__ import annotations
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).parent.resolve()
ROOT=HERE.parents[1]
TARGET='com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'
CLASS='L'+TARGET[:-6]+';'
DEX='7ea38f88187dfec80211b3c5be6e09ef3cbd38928527c42570b8b89deeed3185'
APPLY='applyBeforeNative(Landroid/content/Context;)Z'
LEGACY='verify(Ljava/io/File;)Ljava/lang/String;'
ADAPTER='verify(Landroid/content/Context;Ljava/io/File;)Ljava/lang/String;'
NEW={ADAPTER,'verify(Ljava/lang/String;)Z','read(Ljava/io/InputStream;I)[B',
     'read(Ljava/io/File;I)[B','hash([B)Ljava/lang/String;',
     'verify([B[B)[Ljava/lang/String;','verify(Ljava/io/File;[B[B)Ljava/lang/String;',
     'write(Ljava/io/File;[B)V'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def run(args):
    p=subprocess.run(list(map(str,args)),text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p.stdout


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Nonunique exact source anchor')
    return text.replace(old,new,1)


def methods(text):
    return {m.group(1).split()[-1]:m.group(0) for m in re.finditer(r'(?ms)^\.method ([^\n]+)\n.*?^\.end method',text)}


def strings(raw):
    import struct
    count,start=struct.unpack_from('<II',raw,56);result=[]
    for i in range(count):
        pos=struct.unpack_from('<I',raw,start+4*i)[0]
        while raw[pos]&128:pos+=1
        pos+=1;result.append(raw[pos:raw.index(b'\0',pos)])
    return result


def source():
    key=HERE/'ORIGINAL-INFINITY-PUBLIC-KEY.pem'
    if sha(key.read_bytes())!='bc883be4515d328935b1f3e28294bfc0fe0f2614083274db63b1d24d4da172e8':
        raise ValueError('Immutable original public key required')
    der=subprocess.check_output(['openssl','pkey','-pubin','-in',str(key),'-outform','DER'])
    template=(HERE/'InfinityInstalledModules.java.in').read_text()
    text=once(template,'@PUBLIC_KEY_DER@',','.join(str(v if v<128 else v-256) for v in der))
    # As in the retained exact-source producer, char payloads preserve the
    # existing DEX string indices and forbid Cobra opcode widening.
    return re.sub(r'"(?:[^"\\]|\\.)*"',lambda match:'new String(new char[]{'+
                  ','.join(str(ord(c)) for c in json.loads(match.group()))+'})',text)


def prepare(apk,jars,android,d8,java,javac,out):
    if out.exists():raise ValueError('Fresh adapter output required')
    pins=json.loads((ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    if {p.name:sha(p.read_bytes()) for p in jars.glob('*.jar')}!=pins:raise ValueError('Unverified DEX tools')
    if sha(android.read_bytes())!='6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad':
        raise ValueError('Verified existing Android API signature jar required')
    if sha(d8.read_bytes())!='305622ad00535684534eb8f742cbf5e628a9abc09d8ea4d39d1babb95bf0cee5':
        raise ValueError('Existing build-tools35 D8 required')
    out.mkdir(parents=True)
    cp=os.pathsep.join(str(p.resolve()) for p in sorted(jars.glob('*.jar')))
    with ZipFile(apk) as archive:original=archive.read('classes.dex')
    if sha(original)!=DEX:raise ValueError('Exact signed407 DEX required')
    (out/'original.dex').write_bytes(original)
    run([java,'-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',out/'original.dex','-o',out/'original-smali'])
    before={p.relative_to(out/'original-smali').as_posix():p.read_text() for p in (out/'original-smali').rglob('*.smali')}
    original_target=before[TARGET];old=methods(original_target)
    ledger=json.loads((HERE/'JAVA-MODULE-MIGRATION-PLAN.json').read_text())
    if sha(original_target.encode())!=ledger['target_smali_sha256'] or {k:sha(v.encode()) for k,v in old.items()}!=ledger['method_preimages']:
        raise ValueError('Installer baseline differs from pre-edit ledger')
    file=out/'java/InfinityInstalledCheckpointInstaller.java';file.parent.mkdir();file.write_text(source())
    classes=out/'classes';classes.mkdir()
    run([javac,'--release','8','-g:none','-Xlint:all,-options','-Werror','-cp',android,'-d',classes,file])
    produced=list(classes.rglob('*.class'))
    if len(produced)!=1:raise ValueError('Unexpected compiled runtime classes')
    helper=out/'helper-dex';helper.mkdir()
    run([java,'-cp',d8,'com.android.tools.r8.D8','--release','--min-api','21','--lib',android,'--output',helper,*produced])
    run([java,'-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',helper/'classes.dex','-o',out/'helper-smali'])
    compiled=methods((out/'helper-smali'/TARGET).read_text())
    if set(compiled)!=NEW|{LEGACY,'<init>()V'} or set(old)&NEW:raise ValueError('Unexpected helper method inventory')
    # D8's unused tool marker is not a class definition and is omitted by the
    # assembler. Every actual final DEX string/index still must be identical.
    helper_strings={v for v in strings((helper/'classes.dex').read_bytes()) if not v.startswith(b'~~D8{')}
    if not helper_strings<=set(strings(original)):
        added=sorted(helper_strings-set(strings(original)))
        raise ValueError('New DEX strings forbidden: '+repr(added))
    previous='    invoke-static {v5}, '+CLASS+'->'+LEGACY
    replacement='    invoke-static {p0, v5}, '+CLASS+'->'+ADAPTER
    block=once(old[APPLY],previous,replacement)
    merged=once(original_target,old[APPLY],block)+'\n'+'\n\n'.join(compiled[name] for name in sorted(NEW))+'\n'
    (out/'INSTALLER.patch').write_text(''.join(difflib.unified_diff(original_target.splitlines(True),merged.splitlines(True),'signed407/'+TARGET,'candidate/'+TARGET)))
    modified=out/'modified-smali';shutil.copytree(out/'original-smali',modified);(modified/TARGET).write_text(merged)
    assembled=out/'assembled.dex'
    run([java,'-cp',cp,'org.jf.smali.Main','assemble','--api','21',modified,'-o',assembled])
    adapter=(ROOT/'repairs/universal-persistence-2103401/PreserveReceiptDex.java').read_text()
    adapter=once(adapter,'Lcom/projectinfinity/kodi/InfinityCloseGuardService;',CLASS)
    adapter=once(adapter,'return name.equals("Lcom/projectinfinity/kodi/InfinityCheckpointReceipt;") || name.equals("Lcom/projectinfinity/kodi/InfinityCheckpointReceipt$Descriptor;");','return false;')
    # Signed407 retains unused Search string references from an earlier DEX
    # move. Preserve those too; dropping them changes protected string indices.
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
        raise ValueError('Protected DEX class/disassembly changed; no normalization permitted')
    if strings(final.read_bytes())!=strings(original):raise ValueError('Protected DEX string indices changed')
    checked=methods(after[TARGET])
    if set(checked)!=set(old)|NEW:raise ValueError('Unexpected final method inventory')
    for name,body in old.items():
        expected=block if name==APPLY else body
        if checked[name]!=expected:raise ValueError('Unexpected existing method difference: '+name)
    for name in NEW:
        if checked[name]!=compiled[name]:raise ValueError('Compiled helper method changed: '+name)
    report=dict(status='PASS_EXACT_DEX_SOURCE_AND_PACKAGE_BOUNDARY',baseline_dex_sha256=DEX,
        runtime_adapter_template_sha256=sha((HERE/'InfinityInstalledModules.java.in').read_bytes()),
        generated_java_sha256=sha((out/'java/InfinityInstalledCheckpointInstaller.java').read_bytes()),
        final_dex_sha256=sha(final.read_bytes()),changed_classes=[TARGET],added_classes=[],new_private_methods=sorted(NEW),
        original_legacy_verifiers_and_receipts_preserved=True,all_other_disassemblies_byte_identical=True,
        original_string_pool_and_indices_identical=True,protected_classes=len(before)-1,
        Cobra_classes_changed=[],Main_or_other_callers_changed=[],runtime_Android17='NOT RUN',physical_Fold='NOT RUN',APK_produced=False)
    (out/'DEX-MODULE-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('apk','jars','android','d8','java','javac','out'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(prepare(**vars(args)),indent=2))
