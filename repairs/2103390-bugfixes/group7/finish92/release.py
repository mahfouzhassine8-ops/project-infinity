#!/usr/bin/env python3
"""Deterministic coordinated 2103392 component identities from signed 2103391.

The user-profile upgrade is a normal same-ID Kodi ZIP installation. This tool
never edits installed code or user data. Native/Java guard matching is required;
no post-signing manifest retags, synthetic owner exemptions, or force-green.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import release_coherence as coherence

APK_SHA = '47609f2ada1d6bbc7cdbddb791d11815bdbf1100a083bd8205d60ac21c882151'
PREVIOUS_SOURCE = '335de7d7e1390abc8486f223997fe05c50dbdfb4'
CC = 'script.infinity.commandcenter'
UI = 'script.infinity.uirepair'
WB = 'script.infinity.watchedbridge'
SKIN = 'skin.infinity.diggz'
PACKAGES = ((CC, '0.3.5.20', '0.3.5.22'), (WB, '1.0.1', '1.0.3'),
            (UI, '0.1.2', '0.1.4'), ('script.infinity.rails', '0.2.7', '0.2.7'),
            (SKIN, '1.0.5.228', '1.0.5.229'))
CONTRACT_PATH = 'xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
COORDINATOR_PATH = 'xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp'
NATIVE_BASE = ROOT / 'repairs/android-checkpoint-shutdown/runtime/native/overlay'
JAVA_PATH = 'tools/android/packaging/xbmc/src/InfinityInstalledCheckpointInstaller.java.in'
JAVA_BASE = ROOT / 'repairs/android-checkpoint-shutdown/runtime/android/overlay'
FINAL_COORDINATOR_PREIMAGE = 'eb74a3730456fc4c4fb0bfd65a45afcd7823dfdd66125fd16fd4119fa8d3c6ee'
# Verified against locked TEST4 artifact 12079997774 / run 38975950035.
# Later 2103384 and Group7 native ledgers retain this coordinator unchanged.
NATIVE_PREIMAGE = '8c9de99346b1e74a08cf8b00fd1f29acef514b07041d40ebbe2678700a59abc8'
CHANGED_ADDON_MEMBERS = {CC+'/addon.xml', CC+'/checkpoint_runtime.py', WB+'/addon.xml',
                       WB+'/controller.py', WB+'/CONTROLLER-PREIMAGES.json',
                       UI+'/addon.xml', UI+'/CONTROLLER-PREIMAGES.json', SKIN+'/addon.xml'}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_one(raw: bytes, old: bytes, new: bytes) -> bytes:
    if raw.count(old) != 1:
        raise ValueError('Exact source anchor missing or ambiguous: '+repr(old[:90]))
    return raw.replace(old, new, 1)


def retag(raw: bytes, addon: str, old: str, new: str) -> bytes:
    root = ET.fromstring(raw)
    if root.get('id') != addon or root.get('version') != old:
        raise ValueError('Unexpected signed manifest '+addon)
    if old == new:
        return raw
    opening = re.search(rb'<addon\b[^>]*>', raw)
    if opening is None:
        raise ValueError('Missing root addon manifest')
    tag = opening.group(0)
    change = replace_one(tag, b'version="'+old.encode()+b'"', b'version="'+new.encode()+b'"')
    return raw[:opening.start()]+change+raw[opening.end():]


def read_original(apk: Path) -> dict[str, bytes]:
    if sha(apk.read_bytes()) != APK_SHA:
        raise ValueError('Not the exact original signed 2103391 APK')
    with ZipFile(apk) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError('Invalid original APK')
        ids={x[0] for x in PACKAGES}
        return {n[len('assets/addons/'):]:z.read(n) for n in names
                if n.startswith('assets/addons/') and not n.endswith('/')
                and n[len('assets/addons/'):].split('/')[0] in ids}


def components(original: dict[str, bytes]) -> dict[str, bytes]:
    result=dict(original)
    for addon, old, new in PACKAGES:
        key=addon+'/addon.xml';result[key]=retag(original[key],addon,old,new)
    result[CC+'/checkpoint_runtime.py']=replace_one(original[CC+'/checkpoint_runtime.py'],
        b'ADDON_VERSION = "0.3.5.20"', b'ADDON_VERSION = "0.3.5.22"')
    result[WB+'/controller.py']=replace_one(original[WB+'/controller.py'],
        b'get("version") != "0.3.5.20"', b'get("version") != "0.3.5.22"')
    # Existing dependency only: make the requirement agree with the reviewed
    # controller. No newly activated third-party or compatibility dependencies.
    result[UI+'/addon.xml']=replace_one(result[UI+'/addon.xml'],
        b'addon="script.infinity.commandcenter" version="0.3.5.20"',
        b'addon="script.infinity.commandcenter" version="0.3.5.22"')
    for addon in (UI,WB):
        key=addon+'/CONTROLLER-PREIMAGES.json'
        pins=json.loads(original[key])
        if len(pins)!=13 or any(sha(original[CC+'/'+name])!=digest for name,digest in pins.items()):
            raise ValueError('Original complete controller contract differs')
        raw=original[key]
        for name in ('addon.xml','checkpoint_runtime.py'):
            raw=replace_one(raw,pins[name].encode(),sha(result[CC+'/'+name]).encode())
        result[key]=raw
    delta={n for n in result if result[n]!=original[n]}
    if set(result)!=set(original) or delta!=CHANGED_ADDON_MEMBERS:
        raise ValueError('Unapproved component delta '+repr(delta))
    for n,raw in result.items():
        if n.endswith('.py'):compile(raw,n,'exec')
        elif n.endswith('.xml'):ET.fromstring(raw)
    return result


def contracts(before: bytes, payload: dict[str, bytes]) -> bytes:
    if sha(before)!=NATIVE_PREIMAGE:
        raise ValueError('Saved Pro classifier source was replaced')
    text=before.decode()
    hashes={path:sha(raw) for path,raw in payload.items()}
    blocks=[]
    for endpoint in coherence.ENDPOINTS:
        variants=[v for v in coherence.contracts(text) if v['script']==CC+'/'+endpoint
                  and v['pins'].get(CC+'/plugin.py')==coherence.FINAL['plugin.py']]
        if len(variants)!=1 or len(variants[0]['pins'])!=13:
            raise ValueError('Saved complete Group1 variant missing')
        variant=variants[0]
        block=variant['block'].encode()
        for path,pin in variant['pins'].items():
            if path not in hashes:raise ValueError('Incomplete final controller')
            if hashes[path]!=pin:
                if path not in (CC+'/addon.xml',CC+'/checkpoint_runtime.py'):
                    raise ValueError('Unapproved final controller change')
                block=replace_one(block,pin.encode(),hashes[path].encode())
        blocks.append(block)
    anchor=b'  };\n  return *contracts;'
    insertion=b'    // GROUP7_EXACT_CC22_COHERENT_INSTALL_OVER_V1\n'+b'\n'.join(blocks)+b'\n'
    after=replace_one(before,anchor,insertion+anchor)
    report=coherence.controller_report(payload,after.decode())
    if report['errors']:raise ValueError(report['errors'])
    if after.replace(insertion,b'',1)!=before:raise ValueError('Legacy classifier altered')
    return after


def original_coordinator() -> bytes:
    """Recover the final Essential-First file, NOT the older base overlay.

    Each historical intermediate checksum remains enforced. The resulting hash
    must also equal the downloaded final TEST4 source-preservation receipt.
    This produces a single source file for tests/staging, not a native build.
    """
    sys.path.insert(0, str(ROOT / 'repairs/essential-first-2103377'))
    import reconstruct_coordinator
    import apply_runtime
    with tempfile.TemporaryDirectory(prefix='infinity-reviewed-coordinator-') as tmp:
        locked = reconstruct_coordinator.reconstruct(tmp)
        data = apply_runtime.checkpoint(locked.read_text()).encode()
    if sha(data) != FINAL_COORDINATOR_PREIMAGE:
        raise ValueError('Reconstruction is not the exact final Essential-First coordinator')
    return data


def coordinator(before: bytes) -> bytes:
    if sha(before) != FINAL_COORDINATOR_PREIMAGE:
        raise ValueError('Refusing obsolete/unverified shutdown coordinator')
    # Identity negotiation only. Exact complete native source classification,
    # resident count, previous ownership and all sixteen save guards remain.
    old=b'active["addon_version"].asString() != "0.3.5.19" && active["addon_version"].asString() != "0.3.5.20"'
    return replace_one(before,old,old+b' && active["addon_version"].asString() != "0.3.5.22"')


def java_router(before: bytes, payload: dict[str, bytes]) -> bytes:
    if b'0.3.5.22' in before:raise ValueError('Routing correction already applied')
    pinmap=json.loads(payload[UI+'/CONTROLLER-PREIMAGES.json'])
    marker=sha(payload[CC+'/addon.xml'])
    old=b'      if(CC20.equals(cc)||CC20_CONTEXT.equals(cc)) {'
    new=(b'      if("'+marker.encode()+b'".equals(cc)) {\n'
         b'        controllerVersion="0.3.5.22";\n'
         b'        controller=verifyReviewedController22(addons);\n'
         b'      } else if(CC20.equals(cc)||CC20_CONTEXT.equals(cc)) {')
    after=replace_one(before,old,new)
    # A verification-only route: it cannot overwrite .21 or customized code.
    # Normal same-ID ZIP upgrade supplies .22 before the next clean process.
    body='''  private static boolean verifyReviewedController22(File addons) throws Exception {
    File root = new File(addons, "script.infinity.commandcenter").getAbsoluteFile();
    if (!root.equals(root.getCanonicalFile()) || !root.isDirectory()) return false;
    final String[][] pins = new String[][] {
'''
    body+=''.join('      {"'+name+'", "'+pin+'"},\n' for name,pin in sorted(pinmap.items()))
    body+='''    };
    for (String[] pin : pins) {
      File file = new File(root, pin[0]).getAbsoluteFile();
      if (!file.equals(file.getCanonicalFile()) || !file.isFile()) return false;
      MessageDigest digest = MessageDigest.getInstance("SHA-256");
      try (FileInputStream input = new FileInputStream(file)) {
        byte[] bytes = new byte[8192]; int count, total = 0;
        while ((count = input.read(bytes)) != -1) {
          total += count;
          if (total > 4 * 1024 * 1024) return false;
          digest.update(bytes, 0, count);
        }
      }
      StringBuilder actual = new StringBuilder();
      for (byte value : digest.digest())
        actual.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
      if (!pin[1].equals(actual.toString())) return false;
    }
    return true;
  }
'''
    anchor=b'  private static String hash(File file)throws Exception {'
    return replace_one(after,anchor,body.encode()+anchor)


def stage(apk: Path, destination: Path) -> dict:
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Staging output must be empty')
    original=read_original(apk);final=components(original)
    native=contracts((NATIVE_BASE/CONTRACT_PATH).read_bytes(),final)
    coordinator_before=original_coordinator()
    coordinator_source=coordinator(coordinator_before)
    java=java_router((JAVA_BASE/JAVA_PATH).read_bytes(),final)
    report=dict(source_apk_sha256=APK_SHA,component_versions={a:new for a,_,new in PACKAGES},
                actual_android_runtime_tested=False,physical_fold_verified=False,final_lock=False,
                component_changes={n:dict(before=sha(original[n]),after=sha(final[n]))
                                   for n in sorted(CHANGED_ADDON_MEMBERS)},
                native_changes={CONTRACT_PATH:dict(before=sha((NATIVE_BASE/CONTRACT_PATH).read_bytes()),after=sha(native)),
                                COORDINATOR_PATH:dict(before=sha(coordinator_before),after=sha(coordinator_source))},
                java_changes={JAVA_PATH:dict(before=sha((JAVA_BASE/JAVA_PATH).read_bytes()),after=sha(java))},
                full_native_source_tree_reconstructed=False,
                android_native_library_compiled=False,
                coordinator_source_matches_locked_test4=True,
                required_install_over_components=[CC,WB,UI],
                existing_skin229_and_rails027_code_unchanged=True,
                database_migrations=0,shutdown_required_owner_count_changed=False,
                classifier_legacy_variants_retained=True,original_apk_modified=False,
                cobra_code_resources_or_data_changed=False,
                group5_crash_root_cause_fixed=False,group1_task19_fixed=False)
    for n,raw in final.items():
        target=destination/'addons'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    for n,raw in ((CONTRACT_PATH,native),(COORDINATOR_PATH,coordinator_source)):
        target=destination/'native'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    target=destination/'java'/JAVA_PATH;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(java)
    (destination/'COHERENT92-SOURCE.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(stage(a.apk,a.output),indent=2))
