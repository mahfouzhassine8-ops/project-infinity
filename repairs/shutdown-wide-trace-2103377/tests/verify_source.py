"""Verify exact transformed sources and concrete-type classifier independently."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess

HERE=Path(__file__).resolve().parent

def verify(root,out):
    out.mkdir(parents=True,exist_ok=True)
    factory=(root/'xbmc/filesystem/FileFactory.cpp').read_text()
    identity=factory[factory.index('namespace InfinityVfsOpenTrace\n{'):].rsplit('\n#endif',1)[0]
    pairs=re.findall(r'typeid\(\*file\)==typeid\((\w+)::(\w+)\)\)return Backend::(\w+)',identity)
    assert len(pairs)==29 and len(set(pairs))==29
    # Compile and execute the actual classifier body against distinct polymorphic
    # fixture types. This is type-selection evidence, not backend I/O evidence.
    header='#include "InfinityVfsOpenTrace.h"\n#include <typeinfo>\n#include <cassert>\n'
    header+='namespace XFILE { class IFile { public: virtual ~IFile()=default; }; }\n'
    for ns,cls,backend in pairs:
        header+='namespace '+ns+' { class '+cls+' : public XFILE::IFile {}; }\n'
    header+='namespace XFILE { class Unclassified : public CCurlFile {}; }\n'
    for name,flags in [('posix',['TARGET_POSIX','HAS_OPTICAL_DRIVE','HAS_FILESYSTEM_SMB','HAS_FILESYSTEM_NFS','HAS_UPNP','HAS_ISO9660PP','HAS_UDFREAD','HAVE_LIBBLURAY']),
                       ('windows',['TARGET_WINDOWS','HAS_OPTICAL_DRIVE','TARGET_WINDOWS_STORE','HAS_FILESYSTEM_SMB','HAS_FILESYSTEM_NFS','HAS_UPNP','HAS_ISO9660PP','HAS_UDFREAD','HAVE_LIBBLURAY']),
                       ('tvos',['TARGET_POSIX','HAS_OPTICAL_DRIVE','TARGET_DARWIN_TVOS','HAS_FILESYSTEM_SMB','HAS_FILESYSTEM_NFS','HAS_UPNP','HAS_ISO9660PP','HAS_UDFREAD','HAVE_LIBBLURAY'])]:
        fixture=header+identity+'\nint main(){\n'
        for ns,cls,b in pairs:
            allowed=(b not in {'Windows','WinLibrary','WinSmb'} if name!='windows' else b not in {'Posix','Smb'})
            if b=='TvOs':allowed=name=='tvos'
            fixture+=' { '+ns+'::'+cls+' f; assert(InfinityVfsOpenTrace::Identify(&f)==InfinityVfsOpenTrace::Backend::'+(b if allowed else 'Unknown')+'); }\n'
        fixture+='XFILE::Unclassified f; assert(InfinityVfsOpenTrace::Identify(&f)==InfinityVfsOpenTrace::Backend::Unknown);\n'
        fixture+='assert(InfinityVfsOpenTrace::Identify(nullptr)==InfinityVfsOpenTrace::Backend::Unknown);\n}\n'
        cpp=out/(name+'.cpp');exe=out/name;cpp.write_text(fixture)
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-DTARGET_ANDROID',
                        *['-D'+f for f in flags],'-I',str(root/'xbmc/platform/android/activity'),str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    file=(root/'xbmc/filesystem/File.cpp').read_text()
    assert file.count('InfinityVfsOpenTrace::Open infinityOpen(')==19
    assert 'infinityOpen.Bind(pImp.get(),InfinityVfsOpenTrace::Identify(pImp.get())' in file
    assert 'infinityOpen.Bind(pFile.get(),InfinityVfsOpenTrace::Identify(pFile.get())' in file
    assert 'std::make_unique<CFileCache>(m_flags)' in file
    assert 'INFINITY_VFS_STEP(Reopen)' in file and 'INFINITY_VFS_STEP(Authentication)' in file
    python=(root/'xbmc/interfaces/python/PythonInvoker.cpp').read_text()
    assert 'm_addon->ID()=="plugin.video.playlistbrowser"' not in python
    assert 'AttachLanguageHook(GetId(),m_languageHook.get())' in python
    for phase in ['children_wait','children_retired','interpreter_finalize','interpreter_end_return','stopped_event']:
        assert '"vfs.python.'+phase+'"' in python
    hook=(root/'xbmc/interfaces/legacy/LanguageHook.h').read_text()
    assert hook.count('infinityVfsContext(languageHook)')==2
    checkpoint=(root/'xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp').read_text()
    assert 'DEADLINE = std::chrono::seconds(25)' in checkpoint
    assert 'CheckpointBegin(infinityDiagnosticGeneration)' in checkpoint
    assert 'CheckpointOutcome(s.generation,true)' in checkpoint
    assert checkpoint.count('CheckpointOutcome(s.generation,false)')==2
    assert 'InfinityDiagnosticOwners(s)' in checkpoint
    curl=(root/'xbmc/filesystem/CurlFile.cpp').read_text()
    cache=(root/'xbmc/filesystem/FileCache.cpp').read_text()
    assert 'Callback infinityCancellation' in curl and 'CancelFlagSeen()' in curl
    assert 'Callback infinityCancellation' in cache and 'FileContext infinityVfsContext' in cache
    assert 'ForgetFile(static_cast<IFile*>(this))' in cache
    result={'passed':True,'classifier_fixture_platforms':3,'concrete_classifier_types':len(pairs),
      'instrumented_CFile_entry_points':19,'unchanged_native_deadline_seconds':25,
      'scope':'Exact source anchors plus real RTTI classifier body on fixture classes; complete Kodi compilation remains a separate gate.',
      'shutdown_corrected':False}
    (out/'VFS-SOURCE-CAPABILITIES.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();verify(a.root,a.out)
