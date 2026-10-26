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
CRYPTO='xbmc/interfaces/python/InfinityPythonCryptoContract.h'
AUDIT='xbmc/interfaces/python/InfinityPythonPersistence.h'
MULTIIMAGE='xbmc/guilib/InfinityMultiImagePersistence.h'
DIRECTORY='xbmc/filesystem/DirectoryFactory.cpp'
OWNED=(CONTRACTS,TITLE,POPUP,CHECKPOINT,CMAKE,CRYPTO,AUDIT,MULTIIMAGE,DIRECTORY)

IDENTITY_LOOKUP=r'''inline bool ApprovedInfinityModuleIdentityLookup(const char* event,PyObject* args) {
 const bool load=std::strcmp(event,"ctypes.dlopen")==0;
 const bool direct=std::strcmp(event,"ctypes.dlsym/handle")==0;
 if(!load && !direct && std::strcmp(event,"ctypes.dlsym")!=0)return false;
 const auto count=PyTuple_CheckExact(args)?PyTuple_GET_SIZE(args):0;
 if(count!=(load?1:2))return false;
 // Other libraries/symbols take the byte-identical existing audit path. In
 // particular no Cobra/crypto lookup opens or scans an Infinity source root.
 auto* name=PyTuple_GET_ITEM(args,load?0:1);
 if(!PyUnicode_CheckExact(name))return false;
 PyObject *type=nullptr,*value=nullptr,*trace=nullptr;
 PyErr_Fetch(&type,&value,&trace);
 Py_ssize_t length=0;
 const char* text=PyUnicode_AsUTF8AndSize(name,&length);
 const std::string requested=text?std::string(text,static_cast<std::size_t>(length)):"";
 bool candidate=false;
 if(load) {
   const auto slash=requested.rfind('/');
   candidate=slash!=std::string::npos && requested.substr(slash+1)=="libkodi.so";
 } else candidate=requested=="InfinityCommandCenterIdentityV1";
 bool approved=false;
 if(candidate) {
   Dl_info running{};
   const auto ownAddress=reinterpret_cast<void*>(&InfinityCommandCenterIdentityV1);
   char canonical[PATH_MAX]{};
   if(::dladdr(ownAddress,&running)!=0 && running.dli_fname &&
      ::realpath(running.dli_fname,canonical) && (!load || requested==canonical)) {
     // Obtain only an already-loaded engine; never initialize another image.
     void* engine=::dlopen(canonical,RTLD_NOW|RTLD_NOLOAD);
     if(engine) {
       const bool exact=::dlsym(engine,"InfinityCommandCenterIdentityV1")==ownAddress;
       if(load) approved=exact;
       else {
         auto* first=PyTuple_GET_ITEM(args,0);
         auto* handle=direct?first:PyObject_GetAttrString(first,"_handle");
         if(direct)Py_INCREF(handle);
         approved=exact && handle && PyLong_CheckExact(handle) &&
                  PyLong_AsVoidPtr(handle)==engine && !PyErr_Occurred();
         Py_XDECREF(handle);
       }
       ::dlclose(engine);
     }
   }
 }
 PyErr_Clear();PyErr_Restore(type,value,trace);
 return approved;
}
inline int InfinityModuleIdentityLookupDecision(const char* event,PyObject* args) {
 if(ApprovedInfinityModuleIdentityLookup(event,args))return 1;
 // A same-name function from a shadow image must never impersonate the native
 // trust anchor, even while ordinary third-party work remains allowed to run.
 const bool symbol=std::strcmp(event,"ctypes.dlsym")==0 ||
                   std::strcmp(event,"ctypes.dlsym/handle")==0;
 if(symbol && PyTuple_CheckExact(args) && PyTuple_GET_SIZE(args)==2 &&
    PyUnicode_CheckExact(PyTuple_GET_ITEM(args,1)) &&
    PyUnicode_CompareWithASCIIString(PyTuple_GET_ITEM(args,1),"InfinityCommandCenterIdentityV1")==0)
   return -1;
 return 0; // Preserve the original audit path for every unrelated operation.
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def edits(name):
    if name==MULTIIMAGE:
        return [('  template<class T> T* Reviewed(T* directory)',
                 '  // Only an audited terminal return with no directory handler may call\n'
                 '  // this. Previous opaque dispatch failures remain sticky on the scope.\n'
                 '  void ReviewedNoBackend() { m_reviewed = true; }\n\n'
                 '  template<class T> T* Reviewed(T* directory)')]
    if name==DIRECTORY:
        return [('  CLog::Log(LOGWARNING, "{} - unsupported protocol({}) in {}", __FUNCTION__, url.GetProtocol(),',
                 '#if defined(TARGET_ANDROID)\n'
                 '  // image:// is a file wrapper, not a built-in directory backend.\n'
                 '  // Reaching this terminal branch proves that every factory declined it.\n'
                 '  // VFS handlers return above; opaque file probes already veto the scope.\n'
                 '  if (url.IsProtocol("image")) multiImageFactory.ReviewedNoBackend();\n'
                 '#endif\n'
                 '  CLog::Log(LOGWARNING, "{} - unsupported protocol({}) in {}", __FUNCTION__, url.GetProtocol(),')]
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
    if name==CRYPTO:
        return [('#include <dlfcn.h>',
                 '#include <dlfcn.h>\n#include "platform/android/activity/InfinityInstalledModules.h"'),
                ('inline bool ApprovedNativeLookup(const char* event,PyObject* args) {',
                 IDENTITY_LOOKUP+'inline bool ApprovedNativeLookup(const char* event,PyObject* args) {')]
    if name==AUDIT:
        return [('  if(std::strcmp(event,"ctypes.dlopen")==0 && count==1 && at(0)==Py_None)return 0;',
                 '  if(std::strcmp(event,"ctypes.dlopen")==0 && count==1 && at(0)==Py_None)return 0;\n'
                 '  // Exact already-loaded read-only module identity; never a general native-write exemption.\n'
                 '  const int moduleIdentityLookup=InfinityModuleIdentityLookupDecision(event,args);\n'
                 '  if(moduleIdentityLookup>0)return 0;\n'
                 '  if(moduleIdentityLookup<0) {\n'
                 '    AdmissionDenied(context,"Infinity module identity requires the actual running engine");\n'
                 '    return -1;\n  }')]
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
    for name in OWNED:
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
             'unchanged_existing_sources':9407-len(OWNED),'new_trust_files':sorted(set(final)-set(expected)),
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
