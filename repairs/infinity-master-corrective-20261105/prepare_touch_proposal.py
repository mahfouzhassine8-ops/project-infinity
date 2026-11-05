"""Generate a review-only patch; never write native source/build inputs."""
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
NATIVE=Path('/tmp/kodi451-restored-native')
SOURCE_MAP=Path('/tmp/kodi451-restored-proof/BASELINE-NATIVE-SOURCE-MAP.json')
SOURCE_MAP_SHA='20f901cf5780aebff6eff45e4f21248904f8a8ff72d4acdcd5ea72e783c829c3'


def proposed_sources():
    names=['xbmc/input/InputManager.cpp','xbmc/guilib/GUIBaseContainer.cpp']
    assert hashlib.sha256(SOURCE_MAP.read_bytes()).hexdigest()==SOURCE_MAP_SHA
    manifest=json.loads(SOURCE_MAP.read_text())
    for n in names:assert hashlib.sha256((NATIVE/n).read_bytes()).hexdigest()==manifest[n]
    before={n:(NATIVE/n).read_text() for n in names};after=dict(before)
    n=names[0]
    old='if (wm.GetActiveWindow() == WINDOW_VIDEO_NAV) ids.push_back(owner->GetViewContainerID());'
    assert after[n].count(old)==1
    after[n]=after[n].replace(old,'if (wm.GetActiveWindow() == WINDOW_VIDEO_NAV || wm.GetActiveWindow() == WINDOW_FAVOURITES)\n            ids.push_back(owner->GetViewContainerID());',1)
    old='ids = {8101,8102,8601,8602,8701,8702,8801,8802,8830,8831,8103,8104,8603,8604,8703,8704,8803,8804,8721,8722,8821,8822,9201,9202};'
    assert after[n].count(old)==1
    after[n]=after[n].replace(old,old.replace('9201,9202','9201,9202,8109,8609,8709,8809'),1)
    n=names[1];original=after[n]
    start=original.index('bool CGUIBaseContainer::OnInfinityMediaTouch(')
    end=original.index('\nbool CGUIBaseContainer::OnInfinityAddonBrowserTouch(',start)
    body=original[start:end]
    body=body.replace('GetParentID() == WINDOW_VIDEO_NAV && window &&','(GetParentID() == WINDOW_VIDEO_NAV || GetParentID() == WINDOW_FAVOURITES) && window &&',1)
    marker='  const bool featured = '
    addition='''  const bool homeFavourites = GetParentID() == WINDOW_HOME &&
      (GetID() == 8109 || GetID() == 8609 || GetID() == 8709 || GetID() == 8809);
'''
    body=body.replace(marker,addition+marker,1)
    body=body.replace('(!video && !featured && !resume && !sharedHome && !sharedBrowse)','(!video && !featured && !resume && !sharedHome && !sharedBrowse && !homeFavourites)',1)
    old='''  if (!item->HasVideoInfoTag()) return reject();
  const std::string type = item->GetVideoInfoTag()->m_type;
  if (type != "movie" && type != "tvshow" && type != "season" && type != "episode")
    return reject(); // search/history/command entries are not media records
'''
    new='''  const std::string type = item->HasVideoInfoTag() ? item->GetVideoInfoTag()->m_type : "";
  const bool media = type == "movie" || type == "tvshow" || type == "season" || type == "episode";
  if (!media && !video && !homeFavourites) return reject();
  if (homeFavourites && !item->IsFavourite()) return reject();
'''
    assert old in body;body=body.replace(old,new,1)
    body=body.replace('  const auto item = std::static_pointer_cast<CFileItem>(m_items[selected]);',
        '  const auto item = std::static_pointer_cast<CFileItem>(m_items[selected]);\n  if (item->IsParentFolder()) return reject(); // retain original one-tap Back navigation\n  if (!HasFocus() || window->GetFocusedControlID() != GetID())\n    InfinityTouchClearForAction(this); // a newly focused view starts unarmed',1)
    body=body.replace('const bool owned = (controllerDirectory || latest ||','const bool owned = media && (controllerDirectory || latest ||',1)
    old='''    if (hold)
    {
      m_infinityMediaTapKey.clear();
      m_infinityMediaSuppressUntil = now + std::chrono::milliseconds(600);
      InfinityOpenTitlePopup(item);
      return true;
    }
    if (now < m_infinityMediaSuppressUntil) return true;
    const auto elapsed = now - m_infinityMediaTappedAt;
    const bool open = previous == selected && m_infinityMediaTapKey == key &&
        elapsed >= std::chrono::milliseconds(120) && elapsed <= std::chrono::seconds(5);
    m_infinityMediaTapKey = key;
    m_infinityMediaTappedAt = now;
    if (open)
    {
      m_infinityMediaTapKey.clear();
      OnClick(ACTION_SELECT_ITEM); // exact original item route, once
    }
'''
    new='''    const auto decision = InfinityTouchPress(this, key, previous == selected, hold, now);
    if (decision == InfinityTouchDecision::Context)
      InfinityOpenTitlePopup(item); // retain the authenticated title context owner
    else if (decision == InfinityTouchDecision::Activate)
      OnClick(ACTION_SELECT_ITEM); // exact original item route, once
'''
    assert old in body;body=body.replace(old,new,1)
    old='  if ((!provider && !library && !local) || path.size() > 8192 || item->IsParentFolder()) return reject();'
    new='''  const bool nativeDirectory = video || homeFavourites;
  if ((!nativeDirectory && !provider && !library && !local) || path.empty() ||
      path.size() > (nativeDirectory ? 32768U : 8192U) ||
      (item->IsParentFolder() && !nativeDirectory)) return reject();'''
    assert old in body;body=body.replace(old,new,1)
    old='''  const std::string key = type + "\\n" + path + "\\n" + std::to_string(selected) + "\\n" +
      std::to_string(reinterpret_cast<std::uintptr_t>(item.get()));
  if (hold)
  {
    m_infinityMediaTapKey.clear();
    m_infinityMediaSuppressUntil = now + std::chrono::milliseconds(600);
    OnClick(ACTION_CONTEXT_MENU); // original exact-item provider/native context, no Select
    return true;
  }
  if (now < m_infinityMediaSuppressUntil) return true;
  const auto elapsed = now-m_infinityMediaTappedAt;
  const bool open = previous == selected && m_infinityMediaTapKey == key &&
      elapsed >= std::chrono::milliseconds(120) && elapsed <= std::chrono::seconds(5);
  m_infinityMediaTapKey = key;
  m_infinityMediaTappedAt = now;
  if (open)
  {
    m_infinityMediaTapKey.clear();
    OnClick(ACTION_SELECT_ITEM); // existing action once; no route construction
  }
'''
    new='''  std::string key = "infinity-native-media-touch-v1";
  for (const auto& field : {type, path, directory, std::to_string(GetParentID()),
       std::to_string(GetID()), std::to_string(selected),
       std::to_string(reinterpret_cast<std::uintptr_t>(item.get())),
       item->m_bIsFolder ? std::string("folder") : std::string("item")})
    InfinitySelectionField(key, field);
  const auto decision = InfinityTouchPress(this, key, previous == selected, hold, now);
  if (decision == InfinityTouchDecision::Context)
    OnClick(ACTION_CONTEXT_MENU); // preserve exact native/provider context ownership
  else if (decision == InfinityTouchDecision::Activate)
    OnClick(ACTION_SELECT_ITEM); // existing action once; no route construction
'''
    assert old in body;body=body.replace(old,new,1)
    after[n]=original[:start]+body+original[end:]
    # All additions reuse the existing sidecar. Clearing has no allocation and
    # no effect on controls which never acquired an Infinity touch pair.
    old='''  m_infinityMediaTapKey.clear();
  m_infinityMediaSuppressUntil = std::chrono::steady_clock::now() + std::chrono::milliseconds(600);
  // Keep original favourites:// row'''
    new='''  InfinityTouchPress(this, "", false, true, std::chrono::steady_clock::now());
  m_infinityMediaTapKey.clear();
  m_infinityMediaSuppressUntil = std::chrono::steady_clock::now() + std::chrono::milliseconds(600);
  // Keep original favourites:// row'''
    assert old in after[n];after[n]=after[n].replace(old,new,1)
    # Legacy Option B and Resume holds run before OnInfinityMediaTouch when
    # the existing title owner is unavailable. Keep their context handlers,
    # but disarm a media tap and suppress the release in the same sidecar.
    old='''  m_waitForScrollEnd = false;

  CServiceBroker::GetAppMessenger()->PostMsg(
      TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,
      "RunScript(script.infinity.uirepair,option-b,"'''
    new=old.replace('  m_waitForScrollEnd = false;','''  m_waitForScrollEnd = false;
  InfinityTouchPress(this, "", false, true, std::chrono::steady_clock::now());''',1)
    assert old in after[n];after[n]=after[n].replace(old,new,1)
    old='''  if (hold)
  {
    m_infinityUiTapKey = token;'''
    new='''  if (hold)
  {
    if (resume)
      InfinityTouchPress(this, "", false, true, std::chrono::steady_clock::now());
    m_infinityUiTapKey = token;'''
    assert old in after[n];after[n]=after[n].replace(old,new,1)
    after[n]=after[n].replace('void CGUIBaseContainer::Reset()\n{','void CGUIBaseContainer::Reset()\n{\n  InfinityTouchClearForAction(this); // rebind/reset must not arm a replacement row',1)
    after[n]=after[n].replace('bool CGUIBaseContainer::OnMessage(CGUIMessage& message)\n{',
        'bool CGUIBaseContainer::OnMessage(CGUIMessage& message)\n{\n  if (message.GetControlId() == GetID() && message.GetMessage() == GUI_MSG_LOSTFOCUS &&\n      message.GetParam1() != GetID())\n    InfinityTouchClearForAction(this); // preserve same-control refocus; clear real transfers',1)
    return before,after


def main():
    before,after=proposed_sources()
    patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n,n=0)) for n in before)
    (HERE/'TOUCH-NATIVE-PROPOSAL.patch').write_text(patch)
    records={n:dict(native_input_sha256=hashlib.sha256(before[n].encode()).hexdigest(),proposal_sha256=hashlib.sha256(after[n].encode()).hexdigest()) for n in before}
    (HERE/'TOUCH-PROPOSAL-INPUTS.json').write_text(json.dumps(dict(applied=False,native_files_unchanged=True,
        frozen_reference=2103451,native_source_map_sha256=SOURCE_MAP_SHA,
        native_producer_commit='89300fa6690015f17378657f96230040bb4766ea',
        frozen_native_engine_sha256='151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e',files=records),indent=2)+'\n')
    for n in before:assert (NATIVE/n).read_text()==before[n]
    print('Prepared unapplied two-file touch proposal; native/build inputs unchanged.')


if __name__=='__main__':main()
