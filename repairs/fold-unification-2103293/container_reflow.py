#!/usr/bin/env python3
"""Narrow follow-up to locked 2103291: retain container identity across reflow.

Only GUIBaseContainer.cpp and GUIPanelContainer.cpp are changed. No provider,
player, window lifecycle, Java, account, or Resume Hub code is modified.
"""
from pathlib import Path
import argparse, hashlib, json

BASE_OLD = '''  if (oldLayout == m_layout && oldFocusedLayout == m_focusedLayout)
    return; // nothing has changed, so don't update stuff

  m_itemsPerPage = std::max((int)((Size() - m_focusedLayout->Size(m_orientation)) / m_layout->Size(m_orientation)) + 1, 1);
'''
BASE_NEW = '''  // INFINITY_CONTAINER_REFLOW_V1: viewport changes do not replace templates.
  const int selectedItem = GetSelectedItem();
  const int previousPageSize = m_itemsPerPage;
  m_itemsPerPage = std::max((int)((Size() - m_focusedLayout->Size(m_orientation)) / m_layout->Size(m_orientation)) + 1, 1);

  if (oldLayout == m_layout && oldFocusedLayout == m_focusedLayout)
  {
    if (previousPageSize == m_itemsPerPage)
      return;
    // Validate the new page bounds without allowing offset clamping to select
    // another item. Derived list/fixedlist/wraplist retain their own rules.
    SelectItem(selectedItem);
  }
'''
PANEL_START = '''void CGUIPanelContainer::CalculateLayout()
{
  GetCurrentLayouts();'''
PANEL_NEW_START = '''void CGUIPanelContainer::CalculateLayout()
{
  // Capture absolute identities BEFORE changing the row stride.
  const int selectedItem = GetSelectedItem();
  const int topItem = GetOffset() * m_itemsPerRow;
  const int previousColumns = m_itemsPerRow;
  const int previousPageSize = m_itemsPerPage;
  const bool hadLayout = m_layout && m_focusedLayout;
  GetCurrentLayouts();'''
PANEL_END = '''  if (m_itemsPerPage < 1) m_itemsPerPage = 1;

  // ensure that the scroll offset is a multiple of our size'''
PANEL_NEW_END = '''  if (m_itemsPerPage < 1) m_itemsPerPage = 1;

  // INFINITY_CONTAINER_REFLOW_V1: preserve the selected object and keep the
  // previous leading item in the leading row whenever the new bounds permit.
  if (hadLayout && (previousColumns != m_itemsPerRow || previousPageSize != m_itemsPerPage))
  {
    int offset = std::max(0, topItem / m_itemsPerRow);
    const int maxOffset = std::max(0, static_cast<int>(GetRows()) - m_itemsPerPage);
    offset = std::min(offset, maxOffset);
    if (selectedItem >= 0 && selectedItem < static_cast<int>(m_items.size()))
    {
      const int selectedRow = selectedItem / m_itemsPerRow;
      offset = std::max(offset, selectedRow - m_itemsPerPage + 1);
      offset = std::min(offset, selectedRow);
      SetOffset(offset);
      // A reflow is not a user navigation event: do not emit moving/focus actions.
      CGUIBaseContainer::SetCursor(selectedItem - offset * m_itemsPerRow);
    }
    else
    {
      SetOffset(offset);
      CGUIBaseContainer::SetCursor(0);
    }
  }

  // ensure that the scroll offset is a multiple of our size'''

PATCHES = {
 'xbmc/guilib/GUIBaseContainer.cpp': [(BASE_OLD, BASE_NEW)],
 'xbmc/guilib/GUIPanelContainer.cpp': [(PANEL_START,PANEL_NEW_START),(PANEL_END,PANEL_NEW_END)],
}

def transform(name, source):
    for old,new in PATCHES[name]:
        if new in source: continue
        if source.count(old) != 1: raise ValueError('source anchor mismatch: '+name)
        source=source.replace(old,new,1)
    return source

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['apply','verify']);p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    H=lambda b:hashlib.sha256(b).hexdigest()
    if a.command=='apply':
        entries=[]
        for name in PATCHES:
            f=a.source/name;old=f.read_bytes();new=transform(name,old.decode()).encode();f.write_bytes(new)
            entries.append({'path':name,'before':H(old),'after':H(new)})
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        a.receipt.write_text(json.dumps({'schema':1,'changed_files':entries,'locked_parent':'2103292/2103291','candidate':2103293,'window_reload':False,'provider_changes':False,'physical_verified':False},indent=2)+'\n')
    else:
        r=json.loads(a.receipt.read_text());assert {x['path'] for x in r['changed_files']}==set(PATCHES)
        for x in r['changed_files']:
            b=(a.source/x['path']).read_bytes();assert H(b)==x['after'],x['path'];assert b'INFINITY_CONTAINER_REFLOW_V1' in b
    print('PASS container reflow',a.command)
if __name__=='__main__':main()
