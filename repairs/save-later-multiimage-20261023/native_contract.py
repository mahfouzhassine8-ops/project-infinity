"""Apply the bounded multi-image contract to the exact passed RC8 native inputs."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEFORE = {
    'xbmc/guilib/GUIMultiImage.cpp': 'dfe2d92a2d344fcf0e9e6130d78e65d3a39bdb6774c6a79c5fe3095220aa67ab',
    'xbmc/guilib/GUIMultiImage.h': 'c8dbd13d27d84a5682b7522f32f3e2576acaaf945e78c3769e647c14f5a0d6ee',
    'xbmc/filesystem/DirectoryFactory.cpp': '05e24bbe57a5309d8f5a016209d7d58901bd76b942e2f8adb465d3753a0208b7',
}
HEADER = 'xbmc/guilib/InfinityMultiImagePersistence.h'


def sha(data): return hashlib.sha256(data).hexdigest()


def once(source, before, after):
    if source.count(before) != 1: raise RuntimeError('Native preimage occurrence mismatch: '+before[:100])
    return source.replace(before, after)


def apply(source, overlay):
    if overlay.exists(): raise RuntimeError('Overlay already exists')
    originals = {name: (source/name).read_bytes() for name in BEFORE}
    if {name:sha(data) for name,data in originals.items()} != BEFORE:
        raise RuntimeError('Native source differs from passed RC8')
    h = originals['xbmc/guilib/GUIMultiImage.h'].decode()
    h = once(h, '    bool DoWork() override;\n', '''    bool DoWork() override;
#if defined(TARGET_ANDROID)
    CheckpointResponsibility GetCheckpointResponsibility(const IJobCallback*) const override;
    const char* GetCheckpointPersistenceOwner() const override { return "background_jobs"; }
    const char* GetCheckpointOperation() const override { return "multiimage-enumeration"; }
    bool RequiresCheckpointCompletionReceipt() const override { return true; }
    bool RequiresCheckpointCallback() const override { return true; }
    bool CheckpointSucceeded(bool success) const override;
    bool CheckpointCancelledWithoutWork() const override;
    std::string GetCheckpointResource() const override;
  private:
    bool m_checkpointReadOnly{false};
  public:
#endif
''')
    cpp = originals['xbmc/guilib/GUIMultiImage.cpp'].decode()
    cpp = once(cpp, '#include <mutex>\n', '''#include <mutex>
#if defined(TARGET_ANDROID)
#include "InfinityMultiImagePersistence.h"
#include "URL.h"
#include <typeinfo>
#endif
''')
    anchor = 'bool CGUIMultiImage::CMultiImageJob::DoWork()\n{\n'
    at = cpp.index(anchor)
    if not cpp[at:].rstrip().endswith('return true;\n}'):
        raise RuntimeError('Unexpected original job body')
    body = cpp[at+len(anchor):].rstrip()[:-1]
    start = '''#if defined(TARGET_ANDROID)
  m_checkpointReadOnly = false;
  InfinityMultiImagePersistence::Scope evidence(CJobManager::CheckpointRecord(this));
  // Only HTTP/shout MIME lookup can enter a network backend here. The other
  // original MIME branches use this fresh item's extension and memory only.
  if (StringUtils::StartsWithNoCase(m_path, "http://") ||
      StringUtils::StartsWithNoCase(m_path, "https://") ||
      StringUtils::StartsWithNoCase(m_path, "shout://"))
    evidence.Reject("multiimage_network_mime_lookup_unverified");
  const bool originalResult = [&]() -> bool {
#endif
'''
    end = '''#if defined(TARGET_ANDROID)
  }();
  m_checkpointReadOnly = evidence.Finish(originalResult);
  return originalResult;
#endif
}
'''
    cpp = cpp[:at] + (HERE/'multiimage_methods.inc').read_text()+'\n'+anchor+start+body+end
    factory = originals['xbmc/filesystem/DirectoryFactory.cpp'].decode()
    factory = once(factory, '#include "utils/StringUtils.h"\n', '''#include "utils/StringUtils.h"
#if defined(TARGET_ANDROID)
#include "guilib/InfinityMultiImagePersistence.h"
#include "utils/URIUtils.h"
#endif
''')
    factory = once(factory, 'IDirectory* CDirectoryFactory::Create(const CURL& url)\n{\n', '''IDirectory* CDirectoryFactory::Create(const CURL& url)
{
#if defined(TARGET_ANDROID)
  InfinityMultiImagePersistence::DirectoryFactoryObservation multiImageFactory(
      !InfinityMultiImagePersistence::current || URIUtils::GetExtension(url).empty());
#endif
''')
    for type_name in ('CPosixDirectory', 'CSpecialProtocolDirectory'):
        original = 'return new '+type_name+'();'
        changed = '''{
#if defined(TARGET_ANDROID)
    return multiImageFactory.Reviewed(new '''+type_name+'''());
#else
    '''+original+'''
#endif
  }'''
        factory = once(factory, original, changed)
    after = {'xbmc/guilib/GUIMultiImage.h':h.encode(),
             'xbmc/guilib/GUIMultiImage.cpp':cpp.encode(),
             'xbmc/filesystem/DirectoryFactory.cpp':factory.encode(),
             HEADER:(HERE/'InfinityMultiImagePersistence.h').read_bytes()}
    if (source/HEADER).exists(): raise RuntimeError('Unexpected pre-existing contract header')
    for name,data in after.items():
        target=overlay/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return {name:dict(original_sha256=BEFORE.get(name), final_sha256=sha(data),
        defect='Essential-First multi-image operation ownership',
        justification='Exact job/callback ownership and actual audited backend observation; required completion with verified unchanged outcome; unknown dispatch stays unresolved')
        for name,data in after.items()}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--overlay',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.write_text(json.dumps(apply(a.source,a.overlay),indent=2)+'\n')
