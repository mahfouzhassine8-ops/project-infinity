"""Stage observation-only hooks on the exact green 2103377 native source."""
from pathlib import Path
import hashlib
import json
import re
import shutil

HERE = Path(__file__).resolve().parent
ACTIVITY = 'xbmc/platform/android/activity/'
HEADER = ACTIVITY + 'InfinityVfsOpenTrace.h'
FILES = ['xbmc/filesystem/File.cpp', 'xbmc/filesystem/FileFactory.cpp',
         'xbmc/filesystem/CurlFile.cpp', 'xbmc/interfaces/python/PythonInvoker.cpp',
         'xbmc/interfaces/generic/ScriptInvocationManager.cpp', ACTIVITY + 'InfinityShutdownTrace.h']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Missing or ambiguous exact trace anchor: ' + repr(old[:100]))
    return text.replace(old, new, 1)

MACROS = '''
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityVfsOpenTrace.h"
#define INFINITY_VFS_STEP(s) InfinityVfsOpenTrace::Mark(InfinityVfsOpenTrace::Stage::s)
#define INFINITY_VFS_BACKEND(expression,b) (InfinityVfsOpenTrace::Select(InfinityVfsOpenTrace::Backend::b), (expression))
#define INFINITY_VFS_CANCEL(p,o,e) InfinityVfsOpenTrace::BackendCancellation(p,o,e)
#else
#define INFINITY_VFS_STEP(s) ((void)0)
#define INFINITY_VFS_BACKEND(expression,b) (expression)
#define INFINITY_VFS_CANCEL(p,o,e) ((void)0)
#endif
'''

def transform(name, s):
    if name == ACTIVITY + 'InfinityShutdownTrace.h':
        s = once(s, 'inline std::atomic<unsigned> count{0};', '''struct OperationMetadata
{
  unsigned long long id,parent;
  long long startedMonotonicNs;
  const char* backend;
  const char* stage;
  const char* scheme;
  unsigned cancelObserved;
};
inline std::atomic<unsigned> count{0};''')
        s = once(s, 'std::strncmp(phase,"capture.",8)==0', 'std::strncmp(phase,"vfs.",4)==0 || std::strncmp(phase,"capture.",8)==0')
        s = once(s, 'const char* target=nullptr) noexcept\n{', 'const char* target=nullptr,\n                  const OperationMetadata* operation=nullptr) noexcept\n{')
        s = once(s, '  char row[1024]{};\n', '''  char extension[512]{};
  if(operation)
  {
    // Callers supply only fixed vocabulary and operation numbers. No resource
    // names, paths, URLs, headers, exception text or file-pointer values.
    char backend[33]{},stage[41]{},scheme[17]{};
    Token(operation->backend,backend,sizeof(backend));
    Token(operation->stage,stage,sizeof(stage));Token(operation->scheme,scheme,sizeof(scheme));
    const auto ignored=std::snprintf(extension,sizeof(extension),
      ",\\\"operation_id\\\":%llu,\\\"operation_parent_id\\\":%llu,\\\"operation_start_monotonic_ns\\\":%lld,\\\"backend_category\\\":\\\"%s\\\",\\\"operation_stage\\\":\\\"%s\\\",\\\"resource_category\\\":\\\"%s\\\",\\\"curl_cancel_callback_observed\\\":%u",
      operation->id,operation->parent,operation->startedMonotonicNs,backend,stage,scheme,operation->cancelObserved);
    (void)ignored;
  }
  char row[1536]{};
''')
        s = once(s, '\\\"target_thread\\\":\\\"%s\\\"}\\n",', '\\\"target_thread\\\":\\\"%s\\\"%s}\\n",')
        s = once(s, 'durationNs,outcome,safeTarget);', 'durationNs,outcome,safeTarget,extension);')
    elif name == 'xbmc/filesystem/File.cpp':
        s = once(s, '#include "File.h"\n', '#include "File.h"\n' + MACROS)
        start = s.index('bool CFile::Open(const CURL& file, const unsigned int flags)\n{')
        end = s.index('\nbool CFile::ShouldUseStreamBuffer', start)
        body = s[start:end]
        body = once(body, 'bool CFile::Open(const CURL& file, const unsigned int flags)\n{\n', '''bool CFile::Open(const CURL& file, const unsigned int flags)
{
  const char* const infinityOriginalFunction=__FUNCTION__;
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Open infinityOpen(InfinityVfsOpenTrace::Protocol(file));
  const bool infinityResult = [&]() -> bool {
#endif
''')
        for anchor, stage in [
            ('      return m_pFile->ReOpen(', 'Reopen'),
            ('    CURL url(URIUtils::SubstitutePath(file))', 'SubstitutePath'),
            ('    if (!g_directoryCache.FileExists(', 'DirectoryCache'),
            ('        return m_pFile->Open(url);', 'CacheOpen'),
            ('    m_pFile.reset(CFileFactory::CreateLoader(url));', 'Factory'),
            ('    CURL authUrl(url);', 'Authentication'),
            ('\n      if (!m_pFile->Open(authUrl))', 'BackendOpen'),
            ('      // the file implementation decided', 'Redirect'),
            ('    if (ShouldUseStreamBuffer(url))', 'StreamBufferCheck'),
            ('      m_pBuffer->Attach(m_pFile.get());', 'StreamBufferAttach'),
            ('    if (m_flags & READ_BITRATE)', 'BitrateSetup')]:
            body = once(body, anchor, '    INFINITY_VFS_STEP(' + stage + ');\n' + anchor)
        body = once(body, '    m_pFile.reset(CFileFactory::CreateLoader(url));',
                    '    m_pFile.reset(CFileFactory::CreateLoader(url));\n#if defined(TARGET_ANDROID)\n    infinityOpen.Bind(m_pFile.get());\n#endif')
        body = once(body, '        m_pFile.reset(pRedirectEx->m_pNewFileImp);',
                    '        m_pFile.reset(pRedirectEx->m_pNewFileImp);\n#if defined(TARGET_ANDROID)\n        infinityOpen.Bind(m_pFile.get());\n#endif')
        # Redirected implementations may not run the normal factory. Report that
        # identity as unknown rather than reusing an incorrect earlier backend.
        body = once(body, '        m_pFile.reset(pRedirectEx->m_pNewFileImp);',
                    '        INFINITY_VFS_BACKEND((void)0,Unknown);\n        m_pFile.reset(pRedirectEx->m_pNewFileImp);')
        body = once(body, '\n  return false;\n}\n', '''
  return false;
#if defined(TARGET_ANDROID)
  }();
  infinityOpen.Returned(infinityResult);
  return infinityResult;
#endif
}
''')
        # A lambda changes __FUNCTION__; preserve the original error label.
        body = once(body, '__FUNCTION__); }', 'infinityOriginalFunction); }')
        body = once(body, '__FUNCTION__, file.GetRedacted());', 'infinityOriginalFunction, file.GetRedacted());')
        s = s[:start] + body + s[end:]
    elif name == 'xbmc/filesystem/FileFactory.cpp':
        s = once(s, '#include "FileFactory.h"\n', '#include "FileFactory.h"\n' + MACROS)
        s = once(s, '  if (!CWakeOnAccess::GetInstance().WakeUpHost(url))',
                    '  INFINITY_VFS_STEP(WakeOnAccess);\n  if (!CWakeOnAccess::GetInstance().WakeUpHost(url))')
        s = once(s, '  if (!url.GetProtocol().empty() && CServiceBroker::IsAddonInterfaceUp())',
                    '  INFINITY_VFS_STEP(AddonLookup);\n  if (!url.GetProtocol().empty() && CServiceBroker::IsAddonInterfaceUp())')
        names = {'CVFSEntryIFileWrapper':'Addon','CAPKFile':'Apk','CZipFile':'Zip','CXbtFile':'Xbt',
          'CMusicDatabaseFile':'MusicDb','CVideoDatabaseFile':'VideoDb','CPluginFile':'Plugin',
          'CSpecialProtocolFile':'Special','CMultiPathFile':'MultiPath','CImageFile':'Image',
          'CPosixFile':'Posix','CWin32File':'Windows','CTVOSFile':'TvOs','CWinLibraryFile':'WinLibrary',
          'CFileCDDA':'Cdda','CISO9660File':'Iso','CUDFFile':'Udf','CFileAndroidApp':'AndroidApp',
          'CPipeFile':'Pipe','CBlurayFile':'Bluray','CResourceFile':'Resource','CCurlFile':'Curl',
          'CDAVFile':'Dav','CShoutcastFile':'Shoutcast','CSMBFile':'Smb','CWin32SMBFile':'WinSmb',
          'CNFSFile':'Nfs','CUPnPFile':'Upnp'}
        def replace(match):
            cls, args = match.group(1), match.group(2)
            return 'return INFINITY_VFS_BACKEND(new ' + cls + '(' + args + '),' + names[cls] + ');'
        s, count = re.subn(r'return new (\w+)\(([^()]*)\);', replace, s)
        assert count == 29, count
    elif name == 'xbmc/filesystem/CurlFile.cpp':
        s = once(s, '#include "CurlFile.h"\n', '#include "CurlFile.h"\n' + MACROS)
        s = once(s, 'bool CCurlFile::Open(const CURL& url)\n{',
                    'bool CCurlFile::Open(const CURL& url)\n{\n  INFINITY_VFS_STEP(CurlSetup);')
        s = once(s, '  m_httpresponse = m_state->Connect(m_bufferSize);',
                    '  INFINITY_VFS_STEP(CurlConnect);\n  m_httpresponse = m_state->Connect(m_bufferSize);')
        s = once(s, '    CURLMcode result = g_curlInterface.multi_perform(m_multiHandle, &m_stillRunning);',
                    '    INFINITY_VFS_STEP(CurlPerform);\n    CURLMcode result = g_curlInterface.multi_perform(m_multiHandle, &m_stillRunning);')
        s = once(s, '        const CURLMcode waitResult = g_curlInterface.multi_poll(m_multiHandle, 200, &ready);',
                    '        INFINITY_VFS_STEP(CurlPoll);\n        const CURLMcode waitResult = g_curlInterface.multi_poll(m_multiHandle, 200, &ready);')
        s = once(s, '          if (msg->msg == CURLMSG_DONE)\n          {',
                    '          if (msg->msg == CURLMSG_DONE)\n          {\n#if defined(TARGET_ANDROID)\n            InfinityVfsOpenTrace::TransferResult(static_cast<int>(msg->data.result));\n#endif')
        s = once(s, 'void CCurlFile::Cancel()\n{\n  m_state->m_cancelled = true;\n  while (m_opened)\n    KODI::TIME::Sleep(1ms);\n}', '''void CCurlFile::Cancel()
{
  INFINITY_VFS_CANCEL(static_cast<IFile*>(this),"callback_entered",true);
  m_state->m_cancelled = true;
  INFINITY_VFS_CANCEL(static_cast<IFile*>(this),"existing_flag_set",false);
  while (m_opened)
    KODI::TIME::Sleep(1ms);
  INFINITY_VFS_CANCEL(static_cast<IFile*>(this),"callback_returned",false);
}''')
    elif name == 'xbmc/interfaces/python/PythonInvoker.cpp':
        s = once(s, '#include "platform/android/activity/InfinityAndroidCheckpoint.h"',
                    '#include "platform/android/activity/InfinityAndroidCheckpoint.h"\n#include "platform/android/activity/InfinityVfsOpenTrace.h"')
        s = once(s, '  m_sourceFile = script;\n', '''  m_sourceFile = script;
#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Invoker infinityVfsSubject(GetId(),
    m_addon && m_addon->ID()=="plugin.video.playlistbrowser" &&
    URIUtils::GetFileName(script)=="service.py");
#endif
''')
        s = once(s, '  InfinityShutdownTrace::Scope methodEvidence("python.stop", GetId(), nullptr, nullptr);', '''#if defined(TARGET_ANDROID)
  InfinityVfsOpenTrace::Request(GetId(),abort?"escalation_stop_called":"cooperative_stop_called");
#endif
  InfinityShutdownTrace::Scope methodEvidence("python.stop", GetId(), nullptr, nullptr);''')
        s = once(s, '\n    m_stop = true;\n', '\n    m_stop = true;\n    InfinityVfsOpenTrace::Request(GetId(),"legacy_abort_flag_set");\n')
        s = once(s, '\n  m_stop = true;\n', '\n  m_stop = true;\n#if defined(TARGET_ANDROID)\n  InfinityVfsOpenTrace::Request(GetId(),"legacy_abort_flag_set");\n#endif\n')
        s = once(s, '      // If a dialog entered its doModal(),', '#if defined(TARGET_ANDROID)\n      InfinityVfsOpenTrace::Request(GetId(),"async_python_exception_set");\n#endif\n      // If a dialog entered its doModal(),')
        s = once(s, '        executeScript(fp, realFilename, moduleDict);', '''        executeScript(fp, realFilename, moduleDict);
#if defined(TARGET_ANDROID)
        InfinityVfsOpenTrace::Milestone(GetId(),"vfs.python.bytecode_return","observed");
#endif''')
    elif name == 'xbmc/interfaces/generic/ScriptInvocationManager.cpp':
        anchor='#include "platform/android/activity/InfinityShutdownTrace.h"'
        s = once(s, anchor, anchor + '\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/InfinityVfsOpenTrace.h"\n#endif')
        s = once(s, '    if (invoker)\n      invoker->Stop(false);', '''    if (invoker)
    {
      InfinityVfsOpenTrace::Request(invoker->GetId(),"monitor_notification_sent");
      invoker->Stop(false);
    }''')
        s = once(s, '    const bool retired = InfinityScriptPersistence::TakeInterpreterRetirement(scriptId);', '''    const bool retired = InfinityScriptPersistence::TakeInterpreterRetirement(scriptId);
    InfinityVfsOpenTrace::Milestone(scriptId,"vfs.python.interpreter_retired",
      retired?"durability_receipt_taken":"no_durability_receipt",true);''')
    else:
        raise ValueError(name)
    return s

def apply(root, expected):
    root = Path(root)
    assert len(expected) == 9392
    assert sha(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()) == GREEN_MAP_SHA
    before = {n:sha((root/n).read_bytes()) for n in FILES}
    assert all(before[n] == expected[n] for n in FILES)
    assert not (root/HEADER).exists()
    for name in FILES:
        p=root/name
        p.write_text(transform(name,p.read_text()))
    shutil.copyfile(HERE/'InfinityVfsOpenTrace.h',root/HEADER)
    after = dict(expected)
    for name in [*FILES,HEADER]:after[name]=sha((root/name).read_bytes())
    return after

# Filled from the complete successful run, not a caller-defined partial map.
GREEN_MAP_SHA = '684b77fea120a7efa9fd0c11990f149fdabe3280fbac8f686dd99012dc929700'
