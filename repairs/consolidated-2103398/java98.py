import os,re,subprocess
import components98 as c
TARGETS={'com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.smali'}

def preserve_fields(original, assembled, work, api, cp, original_smali):
    classes = work / 'field-preservation96'
    classes.mkdir()
    adapter = c.HERE / 'PreserveDexFields98.java'
    subprocess.run(['javac', '--release', '8', '-g:none', '-cp', cp,
                    '-d', str(classes), str(adapter)], check=True)
    intermediate = work / 'assembler-output.dex'
    os.rename(assembled, intermediate)
    result = subprocess.run(['java', '-cp', str(classes) + os.pathsep + cp,
        'org.jf.dexlib2.writer.pool.PreserveDexFields98', str(original),
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
