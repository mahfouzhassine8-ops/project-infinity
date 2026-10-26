"""Five exact407 native gates/build-list edits; every other source stays exact."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).parent
ACTIVITY='xbmc/platform/android/activity/'
CONTRACTS=ACTIVITY+'InfinityScriptCheckpointContracts.cpp'
TITLE='xbmc/guilib/GUIBaseContainer.cpp'
POPUP='xbmc/interfaces/legacy/WindowXML.cpp'
CHECKPOINT=ACTIVITY+'InfinityAndroidCheckpoint.cpp'
CMAKE=ACTIVITY+'CMakeLists.txt'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def edits(name):
    if name==CONTRACTS:
        return [('#include "InfinityAndroidCheckpoint.h"',
                 '#include "InfinityAndroidCheckpoint.h"\n#include "InfinityInstalledModules.h"'),
                ('    const std::string actual = CSpecialProtocol::TranslatePath(script);',
                 '    const std::string actual = CSpecialProtocol::TranslatePath(script);\n'
                 '    const auto moduleOwner = InfinityInstalledModules::Classify(actual, addon);\n'
                 '    if (!moduleOwner.empty()) return moduleOwner;')]
    if name==TITLE:
        return [('#include "threads/InfinityStabilityProbe.h"',
                 '#include "threads/InfinityStabilityProbe.h"\n'
                 '#include "platform/android/activity/InfinityInstalledModules.h"\n'
                 '#include "filesystem/SpecialProtocol.h"'),
                ('       addon->Version().asString() == "0.3.5.36");',
                 '       addon->Version().asString() == "0.3.5.36" ||\n'
                 '       InfinityInstalledModules::CapabilityReady(addon->ID(),\n'
                 '           CSpecialProtocol::TranslatePath(addon->Path()), "title-actions-v1"));')]
    if name==POPUP:
        return [('#include "WindowXML.h"',
                 '#include "WindowXML.h"\n#if defined(TARGET_ANDROID)\n'
                 '#include "platform/android/activity/InfinityInstalledModules.h"\n#endif'),
                ('                 responsiveOwner->Version().asString() == "0.3.5.36"))',
                 '                 responsiveOwner->Version().asString() == "0.3.5.36" ||\n'
                 '                 InfinityInstalledModules::CapabilityReady(responsiveOwner->ID(),\n'
                 '                     CSpecialProtocol::TranslatePath(responsiveOwner->Path()), "dialog-reflow-v1")))'),
                ('                responsiveOwner->Version().asString() == "0.1.18")',
                 '                (responsiveOwner->Version().asString() == "0.1.18" ||\n'
                 '                 InfinityInstalledModules::CapabilityReady(responsiveOwner->ID(),\n'
                 '                     CSpecialProtocol::TranslatePath(responsiveOwner->Path()), "dialog-reflow-v1")))')]
    if name==CHECKPOINT:
        return [('#include "InfinityAndroidCheckpoint.h"',
                 '#include "InfinityAndroidCheckpoint.h"\n#include "InfinityInstalledModules.h"'),
                ('active["addon_version"].asString() != "0.3.5.36"',
                 '(active["addon_version"].asString() != "0.3.5.36" &&\n'
                 '              !(active["module_manifest_sha256"].isString() &&\n'
                 '                InfinityInstalledModules::Participant(active["addon_version"].asString(),\n'
                 '                    static_cast<unsigned int>(active["participant_api"].asInteger()),\n'
                 '                    active["module_manifest_sha256"].asString())))')]
    if name==CMAKE:
        return [('            InfinityScriptCheckpointContracts.cpp\n',
                 '            InfinityScriptCheckpointContracts.cpp\n'
                 '            InfinityInstalledModules.cpp\n            InfinityModuleManifest.cpp\n'),
                ('            InfinityAndroidCheckpoint.h\n',
                 '            InfinityAndroidCheckpoint.h\n'
                 '            InfinityInstalledModules.h\n            InfinityModuleManifest.h\n')]
    raise ValueError('Unowned native source: '+name)


def patch(name,raw):
    plan=json.loads((ROOT/'NATIVE-INTEGRATION-PLAN.json').read_text())['changes']
    if name not in plan or sha(raw)!=plan[name]['reconstructed_signed407_preimage_sha256']:
        raise ValueError('Wrong exact407 native source preimage: '+name)
    text=raw.decode();result=text
    for old,new in edits(name):
        if result.count(old)!=1:raise ValueError('Missing/nonunique exact407 native boundary: '+name)
        result=result.replace(old,new,1)
    restored=result
    for old,new in reversed(edits(name)):
        if restored.count(new)!=1:raise ValueError('Native inverse-diff not unique: '+name)
        restored=restored.replace(new,old,1)
    if restored!=text:raise ValueError('Unrelated native source changed: '+name)
    return result.encode()


def stage(native,source_map,out):
    native,out=Path(native),Path(out)
    if out.exists():raise ValueError('Refuse existing native integration stage')
    expected=json.loads(Path(source_map).read_text())
    actual={p.relative_to(native).as_posix():sha(p.read_bytes()) for p in native.rglob('*') if p.is_file()}
    if len(expected)!=9407 or actual!=expected:raise ValueError('Reconstructed407 whole source inventory mismatch')
    out.mkdir(parents=True)
    final=dict(expected);changes={}
    for name in (CONTRACTS,TITLE,POPUP,CHECKPOINT,CMAKE):
        result=patch(name,(native/name).read_bytes())
        changes[name]={'signed407_source_sha256':expected[name],'candidate_source_sha256':sha(result)}
        (native/name).write_bytes(result);final[name]=sha(result)
    for file in sorted((ROOT/'isolated-native').iterdir()):
        if file.suffix not in ('.cpp','.h'):continue
        name=ACTIVITY+file.name;path=native/name
        if path.exists() or name in expected:raise ValueError('Native trust file collides with existing source')
        shutil.copyfile(file,path);final[name]=sha(path.read_bytes())
    if len(final)!=9411:raise ValueError('Unexpected added native source count')
    after={p.relative_to(native).as_posix():sha(p.read_bytes()) for p in native.rglob('*') if p.is_file()}
    if after!=final:raise ValueError('Unexplained native source member difference')
    receipt={'signed407_source_count':9407,'candidate_source_count':9411,'changed_existing_sources':changes,
             'unchanged_existing_sources':9402,'new_trust_files':sorted(set(final)-set(expected)),
             'original_input_and_Favourites_source_header_identical':True,
             'original_class_layouts_and_virtual_interfaces_changed':False,
             'unowned_sources_changed':False,'complete_ARM64_compile':'NOT RUN',
             'Android17':'NOT RUN','physical_Fold':'NOT RUN','release_accepted':False}
    (out/'NATIVE-SOURCE-MAP.json').write_text(json.dumps(final,sort_keys=True,indent=2)+'\n')
    (out/'NATIVE-MODULE-INTEGRATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--map',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(stage(a.native,a.map,a.out),indent=2))
