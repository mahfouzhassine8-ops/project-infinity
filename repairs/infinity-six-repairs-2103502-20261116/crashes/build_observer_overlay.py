"""Apply only the reviewed observer/factory delta to hash-bound signed502 source."""
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
ACTIVITY = 'xbmc/platform/android/activity/'


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    scope = json.loads((HERE / 'OBSERVER-SCOPE.json').read_bytes())
    rows = {}
    for name, expected in scope['existing'].items():
        source = args.baseline / name
        before = source.read_bytes()
        assert hashlib.sha256(before).hexdigest() == expected, name
        text = before.decode()
        if name.endswith('JNIMainActivity.cpp'):
            text = replace_once(text, '#include "JNIMainActivity.h"', '#include "JNIMainActivity.h"\n#include "InfinityActivityObserver.h"\n#include <android/log.h>')
            text = replace_once(text, 'namespace\n{\nstd::string CheckpointJniString', 'namespace\n{\nInfinityActivityObserver<CJNIMainActivity> g_infinityObservers;\n\nstd::string CheckpointJniString')
            text = replace_once(text, 'void CJNIMainActivity::RegisterNatives(JNIEnv* env)', '''void CJNIMainActivity::PublishInfinityObservers(CJNIMainActivity* owner)
{
  if (!g_infinityObservers.Publish(owner))
    __android_log_write(ANDROID_LOG_ERROR, "Kodi", "Infinity activity observer publication refused");
}

void CJNIMainActivity::RetireInfinityObservers(CJNIMainActivity* owner)
{
  g_infinityObservers.Retire(owner);
}

void CJNIMainActivity::RegisterNatives(JNIEnv* env)''')
            for method, default in (('infinityHasActiveVideo', 'JNI_FALSE'), ('infinityWindowWidth', '-1'), ('infinityWindowHeight', '-1'), ('infinityCanEnterPictureInPicture', 'JNI_FALSE'), ('infinityVideoAspectRatio', '16.0f / 9.0f')):
                old = f'  return m_appInstance ? m_appInstance->{method}() : {default};'
                new = f'  auto owner = g_infinityObservers.Acquire();\n  return owner ? owner->{method}() : {default};'
                text = replace_once(text, old, new)
            text = replace_once(text, '  if (m_appInstance)\n    m_appInstance->infinitySyncDisplayStateFromBridge();', '  auto owner = g_infinityObservers.Acquire();\n  if (owner)\n    owner->infinitySyncDisplayStateFromBridge();')
            text = replace_once(text, '  const auto snapshot = m_appInstance ? m_appInstance->infinityGetState() : std::array<int64_t, 16>{};', '''  const auto snapshot = [] {
    auto owner = g_infinityObservers.Acquire();
    return owner ? owner->infinityGetState() : std::array<int64_t, 16>{};
  }();''')
        elif name.endswith('JNIMainActivity.h'):
            text = replace_once(text, 'protected:\n  virtual void onNewIntent', '''protected:
  // Private factory hooks: no JNI or exported ABI additions.
  static void PublishInfinityObservers(CJNIMainActivity* owner) __attribute__((visibility("hidden")));
  static void RetireInfinityObservers(CJNIMainActivity* owner) __attribute__((visibility("hidden")));

  virtual void onNewIntent''')
        elif name.endswith('XBMCApp.h'):
            text = replace_once(text, '    m_appinstance.reset(new CXBMCApp(nativeActivity, inputhandler));', '''    // Preserve construction-before-replacement, but admit observers only once
    // construction is complete and the previous owner has drained.
    std::unique_ptr<CXBMCApp> next(new CXBMCApp(nativeActivity, inputhandler));
    RetireInfinityObservers(m_appinstance.get());
    m_appinstance = std::move(next);
    PublishInfinityObservers(m_appinstance.get());''')
            text = replace_once(text, '  static void Destroy() { m_appinstance.reset(); }', '''  static void Destroy()
  {
    RetireInfinityObservers(m_appinstance.get());
    m_appinstance.reset();
  }''')
        else:
            raise AssertionError(name)
        target = HERE / 'native' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        rows[name] = {'before': expected, 'after': hashlib.sha256(target.read_bytes()).hexdigest()}
    new = ACTIVITY + 'InfinityActivityObserver.h'
    rows[new] = {'before': None, 'after': hashlib.sha256((HERE / 'native' / new).read_bytes()).hexdigest()}
    (HERE / 'OBSERVER-SOURCE.json').write_text(json.dumps(rows, indent=2) + '\n')
    print('Applied exactly three baseline deltas and one private lifetime header')


if __name__ == '__main__':
    main()
