"""Four reviewed ARM64 native source changes: Home Favourites input + exact CC owner pins.

Run after existing native_ownership_qa/restore_reviewed_engine.py. Keeps all
original 2103401 and existing 2103402 ownership contracts byte-for-byte.
Nothing is modified in the Cobra source, skin, user keymaps, or databases.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re

CPP='xbmc/guilib/GUIBaseContainer.cpp'
HEADER='xbmc/guilib/GUIBaseContainer.h'
INPUT='xbmc/input/InputManager.cpp'
OWNERS='xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
FILES=(CPP,HEADER,INPUT,OWNERS)
CC='script.infinity.commandcenter/'
RELEASE36='1b0b2ae9da31cd4772463799d4a3d44d0fce0639ef514221d506f25d09efc10b'
OLD_CONTEXT='b0bcd0f64b7883b1d05878ac23eafe439b7aa3b397e60453bf5f8dcfddbfa2bb'
CONTRACT=re.compile(r'    \{"(script\.infinity\.commandcenter/(?:service|plugin|context)\.py)", "script\.infinity\.commandcenter", "(command_center(?:_client)?)", \{\n(.*?)\n    \}\},\n',re.S)
PIN=re.compile(r'\{"(script\.infinity\.commandcenter/[^"]+)", "([0-9a-f]{64})"\}')
END='  };\n  return *contracts;\n}'

def sha(blob):return hashlib.sha256(blob).hexdigest()
def replace_one(raw,old,new,name):
    if raw.count(old)!=1:raise ValueError('Missing/nonunique guarded anchor: '+name)
    result=raw.replace(old,new,1)
    if result.replace(new,old,1)!=raw:raise ValueError('Unexpected change: '+name)
    return result

FAV_METHOD='''bool CGUIBaseContainer::OnInfinityFavouritesLongPress(float x, float y)
{
#if defined(TARGET_ANDROID)
  // Pre-keymap Home favourite context dispatch using exact transformed hit.
  // It never rewrites profile keymaps or the third-party Super Favourites addon.
  if (GetParentID() != WINDOW_HOME ||
      (GetID() != 8109 && GetID() != 8609 && GetID() != 8709 && GetID() != 8809) ||
      !HasProcessed() || m_gestureActive)
    return false;
  auto& windows = CServiceBroker::GetGUI()->GetWindowManager();
  if (windows.GetActiveWindow() != WINDOW_HOME ||
      windows.GetTopmostModalDialog() != WINDOW_INVALID ||
      CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") != "skin.infinity.diggz")
    return false;
  for (const CGUIControl* owner = this; owner; owner = owner->GetParentControl())
    if (!owner->IsVisible() || owner->IsDisabled())
      return false;
  CPoint point(x, y);
  m_cachedTransform.InverseTransformPosition(point.x, point.y);
  if (!CanFocusFromPoint(point))
    return false;
  const int previous = GetSelectedItem();
  if (!SelectItemFromPoint(point - CPoint(m_posX, m_posY)))
    return false;
  const int selected = GetSelectedItem();
  const auto reject = [this, previous]() { SelectItem(previous); return false; };
  if (selected < 0 || selected >= static_cast<int>(m_items.size()) ||
      !m_items[selected] || !m_items[selected]->IsFileItem())
    return reject();
  const auto item = std::static_pointer_cast<CFileItem>(m_items[selected]);
  if (!item->IsFavourite() || item->GetLabel().empty())
    return reject();
  auto* home = windows.GetWindow(WINDOW_HOME);
  if (!home)
    return reject();
  CGUIMessage focus(GUI_MSG_SETFOCUS, WINDOW_HOME, GetID());
  home->OnMessage(focus);
  if (home->GetFocusedControlID() != GetID() || GetSelectedItem() != selected)
    return reject();
  m_waitForScrollEnd = false;
  m_infinityMediaTapKey.clear();
  m_infinityMediaSuppressUntil = std::chrono::steady_clock::now() + std::chrono::milliseconds(600);
  // Keep original favourites:// row and native provider menu exactly intact.
  return OnContextMenu();
#else
  return false;
#endif
}

'''

FAV_DISPATCH='''            if (!handled)
            {
              // Exactly four existing Home favourites panels; before global
              // Super Favourites touch keymap, leaving all other holds unchanged.
              for (const int favouritesID : {8109, 8609, 8709, 8809})
              {
                auto* favourites = dynamic_cast<CGUIBaseContainer*>(home->GetControl(favouritesID));
                if (favourites && favourites->OnInfinityFavouritesLongPress(
                        newEvent.touch.x, newEvent.touch.y))
                {
                  handled = true;
                  break;
                }
              }
            }
'''

def add_favourites(raw,path):
    src=raw.decode('utf-8')
    if path==CPP:
        marker='bool CGUIBaseContainer::OnInfinityRailLongPress(float x, float y)\n'
        after=replace_one(src,marker,FAV_METHOD+marker,path)
    elif path==HEADER:
        marker='  bool OnInfinityRailLongPress(float x, float y);\n'
        after=replace_one(src,marker,
            '  bool OnInfinityFavouritesLongPress(float x, float y);\n'+marker,path)
    elif path==INPUT:
        beg=src.index('// INFINITY_RAIL_HOLD_V2:')
        end=src.index('// INFINITY_2103398_BROWSER_TOUCH:',beg)
        snippet=src[beg:end]
        marker='            if (handled)\n              break;\n'
        new=replace_one(snippet,marker,FAV_DISPATCH+marker,path)
        after=src[:beg]+new+src[end:]
        if after.replace(new,snippet,1)!=src:
            raise ValueError('Input patch changed non-Home touch handling')
    else:raise ValueError(path)
    return after.encode('utf-8')

def owner_contracts(raw,apk,updated_context):
    original=raw.decode('utf-8')
    candidates=[]
    with ZipFile(apk) as z:
        hashes={}
        for name in z.namelist():
            if name.startswith('assets/addons/'+CC) and not name.endswith('/'):
                hashes[name[len('assets/addons/'):]]=sha(z.read(name))
        hashes[CC+'context.py']=sha(updated_context)
        for m in CONTRACT.finditer(original):
            fields=PIN.findall(m.group(3))
            if len(fields)!=25 or len({k for k,_ in fields})!=25:continue
            source=dict(fields)
            if source.get(CC+'addon.xml')!=RELEASE36 or source.get(CC+'context.py')!=OLD_CONTEXT:continue
            if not set(source).issubset(hashes):raise ValueError('Incomplete signed owner source set')
            mismatched={k for k,h in fields if hashes[k]!=h}
            if mismatched!={CC+'addon.xml',CC+'context.py'}:
                raise ValueError('Extra native command-center owner mismatch: '+repr(mismatched))
            entry=m.group()
            for field in sorted(mismatched):
                old=source[field];new=hashes[field]
                entry=replace_one(entry,'{"'+field+'", "'+old+'"}',
                    '{"'+field+'", "'+new+'"}',field)
            if dict(PIN.findall(entry))!={k:hashes[k] for k in source}:
                raise ValueError('Generated CC owner digest disagrees with installed source')
            candidates.append((m.group(1),m.group(2),entry))
    expected=[(CC+'service.py','command_center'),
              (CC+'plugin.py','command_center_client'),
              (CC+'context.py','command_center_client')]
    if [(path,owner) for path,owner,_ in candidates]!=expected:
        raise ValueError('Expected 3 additive exact source ownership contracts')
    addition=''.join(entry for _,_,entry in candidates)
    result=replace_one(original,END,addition+END,'owner table')
    if result.replace(addition+END,END,1)!=original:
        raise ValueError('Original source contracts were modified')
    return result.encode('utf-8')

def apply(root,source_map,apk,context_bytes,output):
    expected=json.loads(source_map.read_text())
    if len(expected)!=9407:raise ValueError('Wrong complete source count')
    changed={}
    for name in FILES:
        original=(root/name).read_bytes()
        if sha(original)!=expected[name]:raise ValueError('Protected source does not match map '+name)
        data=owner_contracts(original,apk,context_bytes) if name==OWNERS else add_favourites(original,name)
        if data==original:raise ValueError('No reviewed change '+name)
        changed[name]={'before':expected[name],'after':sha(data)}
        (root/name).write_bytes(data)
        expected[name]=sha(data)
    # Keep 9,403 other source fingerprints identical by map membership.
    source_map.write_text(json.dumps(expected,sort_keys=True,indent=2)+'\n')
    output.mkdir(parents=True,exist_ok=True)
    (output/'FAVOURITES-NATIVE-RECEIPT.json').write_text(json.dumps({
        'changed_native_sources':changed,'reviewed_native_count':9407,
        'original_contracts_modified':False,'remaining_native_files_unchanged':9403,
        'Cobra':'UNTOUCHED','user_keymaps':'UNTOUCHED',
        'Kodi_favourites_destinations':'UNTOUCHED',
        'Android17':'NOT_TESTED','physical_Fold':'NOT_TESTED'
    },indent=2)+'\n')
    return expected

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--map',type=Path,required=True)
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--context',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    apply(a.native,a.map,a.apk,a.context.read_bytes(),a.out)
    print('PASS: exact 4 native source deltas, all old contracts and Favourites routes preserved')
