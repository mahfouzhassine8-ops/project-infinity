"""Preserve every baseline class and exact encoded field, except one method hook."""
import os
import re
import subprocess
from pathlib import Path
import components96 as c

TARGETS = {'com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali',
           'com/projectinfinity/kodi/InfinityEvidence95.smali'}


def patch_evidence(original_smali, modified, work, android, tools, cp, api):
    """Replace only the defective collector method and add exact-size hashing."""
    import dex96
    source = c.HERE / 'InfinityEvidence95.java'
    classes = work / 'evidence96-classes'
    classes.mkdir()
    subprocess.run(['javac', '--release', '8', '-g:none', '-Xlint:all,-options',
        '-Werror', '-cp', str(android), '-d', str(classes), str(source)], check=True)
    files = list(classes.rglob('*.class'))
    c.require(len(files) == 1 and files[0].name == 'InfinityEvidence95.class',
              'unexpected evidence class inventory')
    dex = work / 'evidence96-dex'
    dex.mkdir()
    subprocess.run([str(tools/'d8'), '--release', '--min-api', str(api), '--lib',
        str(android), '--output', str(dex), str(files[0])], check=True)
    decoded = work / 'evidence96-smali'
    subprocess.run(['java', '-cp', cp, 'org.jf.baksmali.Main', 'disassemble',
        '--sequential-labels', str(dex/'classes.dex'), '-o', str(decoded)], check=True)
    name = 'com/projectinfinity/kodi/InfinityEvidence95.smali'
    before = original_smali[name]
    methods = dex96.previous().methods
    candidate = methods((decoded/name).read_text())
    old = methods(before)
    append = 'append(Landroid/content/Context;Lorg/json/JSONObject;)V'
    exact = 'digestExact(Ljava/io/InputStream;J)Ljava/lang/String;'
    c.require(set(candidate) == set(old) | {exact}, 'evidence method inventory differs')
    c.require('->digestExact(Ljava/io/InputStream;J)' in candidate[append],
              'exact-size native fingerprint missing')
    result = before.replace(old[append], candidate[append], 1)
    result += '\n' + candidate[exact].rstrip() + '\n'
    c.require(result.removesuffix('\n'+candidate[exact].rstrip()+'\n').replace(
        candidate[append], old[append], 1) == before, 'evidence change escaped authorized methods')
    (modified/name).write_text(result)


def preserve_fields(original, assembled, work, api, cp, original_smali):
    classes = work / 'field-preservation96'
    classes.mkdir()
    adapter = c.HERE / 'PreserveDexFields96.java'
    subprocess.run(['javac', '--release', '8', '-g:none', '-cp', cp,
                    '-d', str(classes), str(adapter)], check=True)
    intermediate = work / 'assembler-output.dex'
    os.rename(assembled, intermediate)
    result = subprocess.run(['java', '-cp', str(classes) + os.pathsep + cp,
        'org.jf.dexlib2.writer.pool.PreserveDexFields96', str(original),
        str(intermediate), str(assembled), str(api)], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, flush=True)
    c.require(result.returncode == 0, 'original field preservation failed')
    count = re.search(r'VERIFIED_EXACT_FIELD_DEFINITIONS=(\d+)', result.stdout)
    protected = re.search(r'PRESERVED_CLASSES=(\d+)', result.stdout)
    expected_fields = sum(len(re.findall(r'^\.field ', body, re.M))
                          for body in original_smali.values())
    c.require(count and protected and int(count[1]) == expected_fields and
        int(protected[1]) == len(original_smali)-len(TARGETS), 'complete original field/class proof differs')
    return dict(build_only_adapter_sha256=c.digest(adapter),
        exact_field_definitions_verified=int(count[1]),
        all_original_field_definitions_verified=True,
        protected_class_definitions_from_original=int(protected[1]),
        encoded_values_and_presence_preserved=True,
        field_normalization_or_exemption_added=False,
        protected_runtime_classes_recompiled=False,
        adapter_packaged_into_app=False)
