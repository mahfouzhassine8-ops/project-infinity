"""Add CC31's exact installed-code verifier; preserve all other DEX definitions."""
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
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DEX='8b3f0cf83cf05e99f0b6d7e141d543af0d5f096e2406e73751ea4cfbff774d7c'
TARGET='com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'
CLASS='L'+TARGET[:-6]+';'
APPLY='applyBeforeNative(Landroid/content/Context;)Z'
HELPER='verify(Ljava/io/File;)Z'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def run(args):
    r=subprocess.run([str(x) for x in args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError(r.stdout)
    return r.stdout
def methods(raw):
    return {m.group(1).split()[-1]:m.group(0) for m in re.finditer(r'(?ms)^\.method ([^\n]+)\n.*?^\.end method',raw)}
def raw(root):return {p.relative_to(root).as_posix():p.read_text() for p in root.rglob('*.smali')}
def once(text,a,b):
    if text.count(a)!=1:raise RuntimeError('Unexpected DEX binding preimage')
    return text.replace(a,b)


def inspect(apk,jars,out):
    pins=json.loads((ROOT/'repairs/universal-persistence-2103401/RECEIPT-TOOL-PINS.json').read_text())
    if {p.name:sha(p.read_bytes()) for p in jars.glob('*.jar')}!=pins:raise RuntimeError('Unverified DEX tools')
    cp=os.pathsep.join(str(p.resolve()) for p in sorted(jars.glob('*.jar')))
    if out.exists():raise RuntimeError('DEX inspection output already exists')
    out.mkdir(parents=True)
    with zipfile.ZipFile(apk) as archive:
        original=archive.read('classes.dex')
        if sha(original)!=DEX:raise RuntimeError('Exact RC8 primary DEX required')
        (out/'original.dex').write_bytes(original)
    run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',out/'original.dex','-o',out/'original-smali'])
    before=raw(out/'original-smali')
    callers=[dict(path=n,call=line.strip()) for n,b in before.items() for line in b.splitlines()
             if CLASS+'->'+APPLY in line]
    save(out/'ORIGINAL-CALLERS.json',dict(callers=callers,classes=len(before),
         target_sha256=sha(before[TARGET].encode()),original_dex_sha256=DEX))
    return cp,before


def prepare(apk,stage,jars,android,d8,out):
    cp,before=inspect(apk,jars,out)
    pins=json.loads((stage/'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
    if len(pins)!=19:raise RuntimeError('All nineteen controller source pins required')
    # Keep the original DEX string pool exactly unchanged. Adding hash strings
    # previously shifted a protected Cobra string past the 16-bit boundary and
    # widened its instruction. Character payloads avoid that encoded change.
    chars=lambda s:'new String(new char[]{'+','.join(str(ord(c)) for c in s)+'})'
    pairs=',\n'.join('      {'+chars(n)+','+chars(h)+'}' for n,h in sorted(pins.items()))
    java='''package com.projectinfinity.kodi;
import java.io.*;
import java.security.MessageDigest;
final class InfinityInstalledCheckpointInstaller {
  private static boolean verify(File addons) throws Exception {
    File root = new File(addons,"script.infinity.commandcenter").getAbsoluteFile();
    if (!root.equals(root.getCanonicalFile()) || !root.isDirectory()) return false;
    String[][] pins = {
'''+pairs+'''
    };
    for (String[] pin : pins) {
      File file = new File(root,pin[0]).getAbsoluteFile();
      if (!file.equals(file.getCanonicalFile()) || !file.isFile()) return false;
      MessageDigest digest=MessageDigest.getInstance("SHA-256");
      int size=0; byte[] buffer=new byte[8192];
      try (FileInputStream stream=new FileInputStream(file)) {
        int count; while ((count=stream.read(buffer))!=-1) {
          size+=count; if (size>4194304) return false; digest.update(buffer,0,count);
        }
      }
      StringBuilder hash=new StringBuilder();
      for (byte value : digest.digest()) hash.append(String.format(java.util.Locale.ROOT,"%02x",value&255));
      if (!hash.toString().equals(pin[1])) return false;
    }
    return true;
  }
}
'''
    source=out/'java/InfinityInstalledCheckpointInstaller.java';source.parent.mkdir();source.write_text(java)
    classes=out/'helper-classes';classes.mkdir()
    run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-d',classes,source])
    helperdex=out/'helper-dex';helperdex.mkdir()
    produced=list(classes.rglob('*.class'))
    if len(produced)!=1:raise RuntimeError('Unexpected verifier classes')
    run([d8,'--release','--min-api','21','--lib',android,'--output',helperdex,*produced])
    decoded=out/'helper-smali'
    run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',helperdex/'classes.dex','-o',decoded])
    compiled=methods((decoded/TARGET).read_text())
    if set(compiled)!={'<init>()V',HELPER}:raise RuntimeError('Unexpected compiled verifier methods')
    original=before[TARGET];old=methods(original)
    if HELPER in old or 'verifyReviewedController29(Ljava/io/File;)Z' not in old:
        raise RuntimeError('Original CC29 verifier absent or CC31 already present')
    block=old[APPLY]
    anchor='    const-string v6, "3e2e182758a890d1ad98992a8cb11ea704c54eaab41b940dde03ab6bd68fa39c"\n'
    selector=('    invoke-static {v5}, '+CLASS+'->'+HELPER+'\n'
        '    move-result v6\n    if-nez v6, :infinity_cc31_route\n\n')
    tail=('    :infinity_cc31_route\n'
        '    const/16 v2, 0x8\n    new-array v2, v2, [C\n'
        '    fill-array-data v2, :infinity_cc31_version\n'
        '    new-instance v7, Ljava/lang/String;\n'
        '    invoke-direct {v7, v2}, Ljava/lang/String;-><init>([C)V\n'
        '    move-object v2, v7\n    goto/16 :goto_1\n'
        '    :infinity_cc31_version\n    .array-data 2\n'+
        ''.join('        0x'+format(ord(c),'x')+'s\n' for c in '0.3.5.31')+
        '    .end array-data\n')
    updated=once(once(block,anchor,selector+anchor),'.end method',tail+'.end method')
    if updated.replace(selector,'',1).replace(tail,'',1)!=block:raise RuntimeError('Original installer route changed')
    merged=once(original,block,updated)+'\n'+compiled[HELPER]+'\n'
    (out/'JAVA-CALLSITE.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),merged.splitlines(True),
         'RC8/'+TARGET,'candidate/'+TARGET)))
    modified=out/'modified-smali';shutil.copytree(out/'original-smali',modified)
    (modified/TARGET).write_text(merged)
    assembled=out/'assembled.dex'
    run(['java','-cp',cp,'org.jf.smali.Main','assemble','--api','21',modified,'-o',assembled])
    # Compare the explicitly reviewed patch after the same assembler/decoder
    # round trip. Baksmali assigns canonical labels to the new named branch and
    # catch region; comparing those labels to the source spelling is invalid.
    # No branch, exception, register or instruction normalization is relaxed.
    expected_smali=out/'expected-smali'
    run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',assembled,'-o',expected_smali])
    expected_methods=methods((expected_smali/TARGET).read_text())
    # Reuse the passed exact-value writer, adapting ONLY its one permitted class
    # target and forbidding additions. All protected definitions come directly
    # from RC8, including Cobra, Search, the RC8 receipt helper and Close guard.
    adapter=(ROOT/'repairs/universal-persistence-2103401/PreserveReceiptDex.java').read_text()
    adapter=once(adapter,'Lcom/projectinfinity/kodi/InfinityCloseGuardService;',CLASS)
    adapter=once(adapter,'return name.equals("Lcom/projectinfinity/kodi/InfinityCheckpointReceipt;") || name.equals("Lcom/projectinfinity/kodi/InfinityCheckpointReceipt$Descriptor;");','return false;')
    file=out/'adapter/PreserveReceiptDex.java';file.parent.mkdir();file.write_text(adapter)
    adapterclasses=out/'adapter-classes';adapterclasses.mkdir()
    run(['javac','--release','8','-g:none','-cp',cp,'-d',adapterclasses,file])
    final=out/'classes.dex'
    log=run(['java','-cp',str(adapterclasses)+os.pathsep+cp,'org.jf.dexlib2.writer.pool.PreserveReceiptDex',out/'original.dex',assembled,final,'21'])
    (out/'EXACT-FIELDS.log').write_text(log)
    if 'PRESERVED_CLASSES='+str(len(before)-1) not in log:raise RuntimeError('Protected class inventory incomplete')
    verified=out/'verified-smali'
    run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',final,'-o',verified])
    after=raw(verified)
    spec=importlib.util.spec_from_file_location('unchanged_bytecode_guard',ROOT/'repairs/cobra-clean-restart/bytecode_guard.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);guard.selftest();norm=guard.normalize
    if set(after)!=set(before) or [n for n in before if before[n]!=after[n]]!=[TARGET]:
        raise RuntimeError('Protected DEX encoding or definition changed; opcode normalization is forbidden')
    if dex_strings(final.read_bytes())!=dex_strings((out/'original.dex').read_bytes()):
        raise RuntimeError('Original DEX string inventory or indices changed')
    checked=methods(after[TARGET])
    if set(checked)!=set(old)|{HELPER}:raise RuntimeError('Unexpected installer method inventory')
    for name,body in old.items():
        expected=expected_methods[name] if name==APPLY else body
        if norm(checked[name])!=norm(expected):raise RuntimeError('Unexpected existing method change: '+name)
    if norm(checked[HELPER])!=norm(expected_methods[HELPER]):raise RuntimeError('Verifier compilation drift')
    report=dict(passed=True,original_dex_sha256=DEX,final_dex_sha256=sha(final.read_bytes()),
        changed_classes=[TARGET],added_classes=[],added_methods=[HELPER],
        original_installer_routes_preserved=True,all_other_original_definitions_preserved=True,
        protected_class_count=len(before)-1,exact_original_field_definitions_preserved=True,
        protected_disassembly_byte_identical=True,original_string_pool_identical=True,
        protected_opcode_widening_permitted=False,
        cobra_definitions_changed=[],search_definitions_changed=[],rc8_receipt_and_close_definitions_changed=[],
        adapter_packaged=False,physical_fold_verified=False,actual_android_verified=False)
    save(out/'DEX-PRESERVATION.json',report)
    return report


def dex_strings(raw):
    import struct
    size,offset=struct.unpack_from('<II',raw,56)
    values=[]
    for i in range(size):
        at=struct.unpack_from('<I',raw,offset+4*i)[0]
        while raw[at]&128:at+=1
        at+=1
        values.append(raw[at:raw.index(b'\0',at)])
    return values


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('inspect','prepare'))
    for name in ('apk','stage','jars','android','d8','out'):p.add_argument('--'+name,type=Path,required=name in ('apk','jars','out'))
    a=p.parse_args()
    if a.mode=='inspect':inspect(a.apk,a.jars,a.out)
    else:print(json.dumps(prepare(a.apk,a.stage,a.jars,a.android,a.d8,a.out),indent=2))
