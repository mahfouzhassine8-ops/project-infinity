"""Observe original Kodi results only; never replace a saved destination."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEFORE = {
    'xbmc/windows/GUIMediaWindow.cpp': 'f5d9b935739be1c0e8290d7326ec5e1d85d271542fdf58db9ee1e68d02afef40',
    'xbmc/filesystem/PluginDirectory.cpp': 'f9993bfcd8c8213525a51473cdcbe39455b4bb73adb65c8cf7666280bb056484',
    'xbmc/interfaces/generic/ScriptRunner.cpp': 'f13605ef0b23c7b87b5447fd964b503a768186a8f1d3cab7dfe626b8fe275783',
    'xbmc/interfaces/generic/ScriptRunner.h': 'e39aeabe417cbe6a2a1f791420b9d9b9ad6db1618dbf6278619910d7f2481b15',
}

# Applied after all original Infinity Search admission checks and its shared
# three-invocation reservation. No timeout releases an invocation or writer.
LOOKUP_DEADLINE = '''    // INFINITY_SAVED_NAVIGATION_LOOKUP: only an explicit, path-bound recovery intent.
    const std::string savedLookupKey = "Infinity.SavedNavigation.Lookup." + m_infinitySearchToken;
    const bool savedLookup = InfinitySearchProperty(savedLookupKey) == proof;
    InfinitySearchProperty(savedLookupKey, "");
    if (savedLookup)
      m_infinitySearchDeadline = std::chrono::steady_clock::now() + std::chrono::seconds(60);
'''
LOOKUP_PROTOCOL = '      InfinitySearchProperty("Infinity.SavedNavigation.Lookup.Protocol", "1");\n      InfinitySearchProperty("Infinity.SavedNavigation.Protocol", "2");\n'


def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('Navigation observer preimage differs: ' + old[:100])
    return text.replace(old, new)


def wrap(text, signature, next_signature, start, finish):
    """The entire original body, including every return, remains verbatim."""
    begin = text.index(signature) + len(signature)
    end = text.index(next_signature, begin)
    original = text[begin:end]
    if not original.endswith('}\n\n'):
        raise RuntimeError('Unexpected function boundary')
    body = original[:-3]  # retain the newline immediately before the closing brace
    replacement = ('\n#if defined(TARGET_ANDROID)\n' + start +
                   '  const bool originalResult = [&]() -> bool {\n#endif\n' + body +
                   '#if defined(TARGET_ANDROID)\n  }();\n' + finish +
                   '  return originalResult;\n#endif\n}\n\n')
    return text[:begin] + replacement + text[end:]


def apply(source, overlay):
    original = {n: (source/n).read_bytes() for n in BEFORE}
    if {n: hashlib.sha256(b).hexdigest() for n, b in original.items()} != BEFORE:
        raise RuntimeError('Exact RC8 navigation sources required')
    after = {n: b.decode() for n, b in original.items()}
    window, plugin, runner, header = BEFORE
    for n, anchor in ((window, '#include "GUIMediaWindow.h"\n'),
                      (plugin, '#include "PluginDirectory.h"\n')):
        after[n] = once(after[n], anchor, anchor +
            '#if defined(TARGET_ANDROID)\n#include "guilib/InfinitySavedNavigation.h"\n#endif\n')
    # Arm only an existing Save for Later click; the original target and item
    # are not reconstructed, replaced, probed, resolved or played here.
    after[window] = once(after[window], '  CFileItemPtr pItem = m_vecItems->Get(iItem);\n\n  if (pItem->IsParentFolder())',
        '  CFileItemPtr pItem = m_vecItems->Get(iItem);\n'
        '#if defined(TARGET_ANDROID)\n'
        '  if (InfinitySavedNavigation::Begin(*pItem, m_vecItems->GetPath())) return true;\n'
        '#endif\n\n  if (pItem->IsParentFolder())')
    after[window] = wrap(after[window],
        'bool CGUIMediaWindow::Update(const std::string &strDirectory, bool updateFilterPath /* = true */)\n{',
        'bool CGUIMediaWindow::Refresh(',
        '  InfinitySavedNavigation::PrepareNext(strDirectory);\n',
        '  InfinitySavedNavigation::WindowResult(strDirectory, originalResult, *m_vecItems);\n')
    start = after[window].index('bool CGUIMediaWindow::GetDirectoryItems(')
    tail = after[window][start:]
    wait = 'CGUIDialogBusy::Wait(&getItems, 100, true)'
    if tail.count(wait) != 2:
        raise RuntimeError('Original directory cancellation points changed')
    tail = tail.replace(wait, 'waitForItems()')
    tail = once(tail, '    CGetDirectoryItems getItems(m_rootDir, url, items, useDir);\n',
        '    CGetDirectoryItems getItems(m_rootDir, url, items, useDir);\n'
        '    auto waitForItems = [&]() {\n'
        '      const bool result = CGUIDialogBusy::Wait(&getItems, 100, true);\n'
        '#if defined(TARGET_ANDROID)\n'
        '      InfinitySavedNavigation::DirectoryCancelled(url.Get(), !result);\n'
        '#endif\n      return result;\n    };\n')
    after[window] = after[window][:start] + tail
    after[plugin] = wrap(after[plugin],
        'bool CPluginDirectory::GetResolvedPluginResult(CFileItem& resultItem)\n{',
        'bool CPluginDirectory::GetPluginResult(',
        '  InfinitySavedNavigation::MovieAttempt savedAttempt(resultItem);\n',
        '  savedAttempt.Finish(originalResult, resultItem);\n')
    after[plugin] = once(after[plugin], '  bool success = newDir.StartScript(strPath, resume);\n',
        '  bool success = newDir.StartScript(strPath, resume);\n'
        '#if defined(TARGET_ANDROID)\n'
        '  success = InfinitySavedNavigation::MovieResolved(strPath, success, *newDir.m_fileResult);\n'
        '  if (!success) InfinitySavedNavigation::MovieCancelled(\n'
        '      newDir.InfinityResultCancelled() || newDir.m_cancelled);\n'
        '#endif\n')
    after[plugin] = once(after[plugin], '  bool success = StartScript(pathToUrl, false);\n',
        '  bool success = StartScript(pathToUrl, false);\n'
        '#if defined(TARGET_ANDROID)\n'
        '  if (!success) InfinitySavedNavigation::DirectoryCancelled(\n'
        '      pathToUrl, InfinityResultCancelled() || m_cancelled);\n'
        '#endif\n')
    after[header] = once(after[header], '  void SetDone();\n',
        '  void SetDone();\n#if defined(TARGET_ANDROID)\n'
        '  bool InfinityResultCancelled() const { return m_infinityResultCancelled; }\n'
        '#endif\n')
    after[header] = once(after[header], '  bool m_infinitySearch{false};\n',
        '  bool m_infinitySearch{false};\n  bool m_infinityResultCancelled{false};\n')
    after[runner] = once(after[runner], '  // reset our wait event\n',
        '#if defined(TARGET_ANDROID)\n  m_infinityResultCancelled = false;\n#endif\n'
        '  // reset our wait event\n')
    after[runner] = once(after[runner], '  if (cancelled || IsCancelled())\n',
        '#if defined(TARGET_ANDROID)\n  m_infinityResultCancelled = cancelled;\n#endif\n'
        '  if (cancelled || IsCancelled())\n')
    marker = '    m_infinitySearchDeadline = std::chrono::steady_clock::now() + std::chrono::seconds(20);\n'
    after[runner] = once(after[runner], marker, marker + LOOKUP_DEADLINE)
    marker = '      InfinitySearchProperty("Infinity.Search.Protocol", "1");\n'
    after[runner] = once(after[runner], marker, marker + LOOKUP_PROTOCOL)
    after = {n: b.encode() for n, b in after.items()}
    for name in ('InfinitySavedNavigation.h', 'InfinitySavedNavigationState.h'):
        target = 'xbmc/guilib/' + name
        if (source/target).exists():
            raise RuntimeError('Unexpected existing navigation observation header')
        after[target] = (HERE/name).read_bytes()
    ledger = {}
    for n, b in after.items():
        path = overlay/n
        if path.exists():
            raise RuntimeError('Overlapping native navigation edit: ' + n)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b)
        ledger[n] = dict(original_sha256=BEFORE.get(n), final_sha256=hashlib.sha256(b).hexdigest(),
            defect='Save for Later original-route failure observation',
            justification='Observe actual original directory/resolution return; only Infinity later clicks may offer recovery; no result, provider argument, lifecycle or persistence receipt changed')
    ledger[runner]['justification'] += ('; path-bound failure-recovery lookup gets a bounded 60-second consumer allowance '
        'after original admission and shared three-slot reservation; ordinary Search remains 20 seconds, '
        'actual script retirement and every cancellation/shutdown check remain unchanged')
    return ledger
