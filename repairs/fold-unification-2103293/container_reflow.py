#!/usr/bin/env python3
"""Narrow follow-up to locked 2103291: retain container identity across reflow.

Only native GUI container and item-layout implementation files are changed. No provider,
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
    if (previousPageSize == m_itemsPerPage && previousItemSize == m_layout->Size(m_orientation))
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

# Responsive item dimensions are opt-in; existing numeric layouts are unchanged.
ITEM_METHOD = r'''bool CGUIListItemLayout::ReflowResponsiveSize(float parentWidth, float parentHeight)
{
  if (m_responsiveWidth.empty() && m_responsiveHeight.empty())
    return false;
  float width = m_width;
  float height = m_height;
  if (!m_responsiveHeight.empty())
    height = std::max(1.0f, parentHeight * static_cast<float>(std::atof(m_responsiveHeight.c_str())) / 100.0f);
  if (m_responsiveWidth == "auto" && m_responsiveAspect > 0.0f)
  {
    width = std::max(1.0f, std::min(parentWidth, height * m_responsiveAspect));
    height = width / m_responsiveAspect;
  }
  else if (!m_responsiveWidth.empty())
    width = std::max(1.0f, parentWidth * static_cast<float>(std::atof(m_responsiveWidth.c_str())) / 100.0f);
  if (width == m_width && height == m_height)
    return false;
  m_width = width;
  m_height = height;
  m_group.SetWidth(width);
  m_group.SetHeight(height);
  // Use 2103291's existing recursive resolver for the existing item controls.
  m_group.ReflowResponsiveLayout(width, height);
  SetInvalid();
  return true;
}

'''
PATCHES['xbmc/guilib/GUIBaseContainer.cpp'].insert(0,(
 '  CGUIListItemLayout *oldFocusedLayout = m_focusedLayout;\n',
 '  const float previousItemSize = m_layout ? m_layout->Size(m_orientation) : 0.0f;\n  CGUIListItemLayout *oldFocusedLayout = m_focusedLayout;\n'))
PATCHES['xbmc/guilib/GUIBaseContainer.cpp'].append((
 '    m_focusedLayout = &m_focusedLayouts.front(); // failsafe\n}',
 '    m_focusedLayout = &m_focusedLayouts.front(); // failsafe\n\n  if (m_layout)\n    m_layout->ReflowResponsiveSize(m_width, m_height);\n  if (m_focusedLayout)\n    m_focusedLayout->ReflowResponsiveSize(m_width, m_height);\n}'))
PATCHES['xbmc/guilib/GUIListItemLayout.h']=[
 ('  void SetWidth(float width);','  // INFINITY_CONTAINER_REFLOW_V1: opt-in parent-relative item dimensions.\n  bool ReflowResponsiveSize(float parentWidth, float parentHeight);\n  void SetWidth(float width);'),
 ('  float m_height{0};','  float m_height{0};\n  std::string m_responsiveWidth;\n  std::string m_responsiveHeight;\n  float m_responsiveAspect{0};')]
PATCHES['xbmc/guilib/GUIListItemLayout.cpp']=[
 ('#include "utils/XBMCTinyXML.h"','#include "utils/XBMCTinyXML.h"\n\n#include <cstdlib>'),
 ('    m_height(from.m_height),','    m_height(from.m_height),\n    m_responsiveWidth(from.m_responsiveWidth),\n    m_responsiveHeight(from.m_responsiveHeight),\n    m_responsiveAspect(from.m_responsiveAspect),'),
 ('  if (m_invalidated)\n  { // need to update our item','  // INFINITY_CONTAINER_REFLOW_V1: retain each cloned item and its focus state.\n  if (const auto* parent = m_group.GetParentControl())\n    ReflowResponsiveSize(parent->GetWidth(), parent->GetHeight());\n  if (m_invalidated)\n  { // need to update our item'),
 ('void CGUIListItemLayout::SetWidth(float width)',ITEM_METHOD+'void CGUIListItemLayout::SetWidth(float width)'),
 ('  layout->QueryFloatAttribute("height", &m_height);','  layout->QueryFloatAttribute("height", &m_height);\n  const char* responsiveWidth = layout->Attribute("width");\n  const char* responsiveHeight = layout->Attribute("height");\n  m_responsiveWidth.clear();\n  m_responsiveHeight.clear();\n  if (responsiveWidth && (std::string(responsiveWidth) == "auto" || std::string(responsiveWidth).find(\'%\') != std::string::npos))\n    m_responsiveWidth = responsiveWidth;\n  if (responsiveHeight && std::string(responsiveHeight).find(\'%\') != std::string::npos)\n    m_responsiveHeight = responsiveHeight;\n  layout->QueryFloatAttribute("aspectratio", &m_responsiveAspect);'),
 ('  m_group.SetWidth(m_width);\n  m_group.SetHeight(m_height);\n\n  TiXmlElement *child', '  ReflowResponsiveSize(maxWidth, maxHeight);\n  m_group.SetWidth(m_width);\n  m_group.SetHeight(m_height);\n\n  TiXmlElement *child')]

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
