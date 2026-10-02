#!/usr/bin/env python3
"""Repair retained text caches, layering ONLY over the locked 2103293 engine.

User authorized a narrowly scoped native candidate after source evidence.
The 2103291 resolver and 2103293 container identity/state code remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

LABEL_REFLOW = r'''bool CGUIListLabel::ReflowResponsiveLayout(float parentWidth, float parentHeight)
{
  if (!m_responsiveLayoutSpec.enabled)
    return false;

  // INFINITY_TEXT_REFLOW_V1: the factory's resolved coordinates describe the
  // left/top rectangle. SetWidth's legacy center/right adjustment must not
  // become the final drawing rectangle for retained, anchored list labels.
  const bool changed = CGUIControl::ReflowResponsiveLayout(parentWidth, parentHeight);
  m_label.SetMaxRect(m_posX, m_posY, m_width, m_height);
  if (!m_responsiveLayoutSpec.hitRect.enabled)
    SetHitRect(CRect(m_posX, m_posY, m_posX + m_width, m_posY + m_height), m_hitColor);
  if (changed)
  {
    m_label.SetInvalid();
    MarkDirtyRegion();
  }
  return changed;
}

'''

TEXTBOX_REFLOW = r'''bool CGUITextBox::ReflowResponsiveLayout(float parentWidth, float parentHeight)
{
  const float oldWidth = m_width;
  const float oldHeight = m_height;
  const bool changed = CGUIControl::ReflowResponsiveLayout(parentWidth, parentHeight);
  if (oldWidth != m_width || oldHeight != m_height)
  {
    // INFINITY_TEXT_REFLOW_V1: unchanged content still needs a new wrap width
    // and rendered height. UpdateInfo retains the existing item/data owner.
    m_infinityResponsiveTextLayoutDirty = true;
    SetInvalid();
  }
  return changed;
}

'''

TEXTBOX_UPDATE = r'''void CGUITextBox::UpdateInfo(const CGUIListItem *item)
{
  m_textColor = m_label.textColor;
  const std::string text = item ? m_info.GetItemLabel(item) : m_info.GetLabel(m_parentID);
  const bool preserveViewport = m_infinityResponsiveTextLayoutDirty &&
                                !m_lastUpdateW && text == m_lastUtf8Text;
  const unsigned int previousOffset = m_offset;
  const float previousRowPosition = m_itemHeight > 0.0f ? m_scrollOffset / m_itemHeight : 0.0f;
  if (!CGUITextLayout::Update(text, m_width, m_infinityResponsiveTextLayoutDirty))
    return; // nothing changed
  m_infinityResponsiveTextLayoutDirty = false;

  SetInvalid();
  if (!preserveViewport)
  {
    // Genuine new content keeps the established reset-to-top behavior.
    m_offset = 0;
    m_scrollOffset = 0;
    ResetAutoScrolling();
  }

  m_itemHeight = m_font ? m_font->GetLineHeight() : 10;
  float textHeight = m_font ? m_font->GetTextHeight(m_lines.size()) : m_itemHeight * m_lines.size();
  float maxHeight = m_height ? m_height : textHeight;
  m_renderHeight = m_minHeight ? CLAMP(textHeight, m_minHeight, maxHeight) : m_height;
  m_itemsPerPage = static_cast<unsigned int>(m_renderHeight / m_itemHeight);

  if (preserveViewport)
  {
    const unsigned int rows = static_cast<unsigned int>(m_lines.size());
    const unsigned int maxOffset = rows > m_itemsPerPage ? rows - m_itemsPerPage : 0;
    m_offset = std::min(previousOffset, maxOffset);
    m_scrollOffset = std::clamp(previousRowPosition * m_itemHeight, 0.0f,
                              static_cast<float>(maxOffset) * m_itemHeight);
    m_scrollSpeed = 0;
  }
  UpdatePageControl();
}'''

PATCHES = {
    'xbmc/guilib/GUIListLabel.h': [
        ('  void SetWidth(float width) override;',
         '  void SetWidth(float width) override;\n  // INFINITY_TEXT_REFLOW_V1: synchronize drawing bounds after the final geometry.\n  bool ReflowResponsiveLayout(float parentWidth, float parentHeight) override;')],
    'xbmc/guilib/GUIListLabel.cpp': [
        ('void CGUIListLabel::SetWidth(float width)', LABEL_REFLOW + 'void CGUIListLabel::SetWidth(float width)')],
    'xbmc/guilib/GUITextBox.h': [
        ('  float GetHeight() const override;',
         '  float GetHeight() const override;\n  bool ReflowResponsiveLayout(float parentWidth, float parentHeight) override;'),
        ('  float m_renderHeight;',
         '  float m_renderHeight;\n  // INFINITY_TEXT_REFLOW_V1: size invalidation is independent of content changes.\n  bool m_infinityResponsiveTextLayoutDirty{false};')],
    'xbmc/guilib/GUITextBox.cpp': [
        ('  m_renderHeight = from.m_renderHeight;',
         '  m_renderHeight = from.m_renderHeight;\n  m_infinityResponsiveTextLayoutDirty = from.m_infinityResponsiveTextLayoutDirty;'),
        ('void CGUITextBox::DoProcess(', TEXTBOX_REFLOW + 'void CGUITextBox::DoProcess(')],
}

def method_span(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return start, end

def transform(name, source):
    if 'INFINITY_TEXT_REFLOW_V1' in source:
        return source
    for old, new in PATCHES[name]:
        if source.count(old) != 1:
            raise ValueError('Pinned source anchor mismatch: ' + name)
        source = source.replace(old, new, 1)
    if name.endswith('GUITextBox.cpp'):
        start, end = method_span(source, 'void CGUITextBox::UpdateInfo(')
        original = source[start:end]
        assert 'CGUITextLayout::Update(item ? m_info.GetItemLabel(item)' in original
        source = source[:start] + TEXTBOX_UPDATE + source[end:]
    return source

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('apply', 'verify'))
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    digest = lambda b: hashlib.sha256(b).hexdigest()
    if args.command == 'apply':
        control = (args.source / 'xbmc/guilib/GUIControl.cpp').read_text()
        assert 'SetWidth(nextWidth);\n  SetHeight(nextHeight);\n  SetPosition(nextX, nextY);' in control
        container = (args.source / 'xbmc/guilib/GUIListItemLayout.cpp').read_text()
        assert 'INFINITY_CONTAINER_REFLOW_V1' in container
        def snapshot():
            return {p.relative_to(args.source).as_posix(): digest(p.read_bytes())
                    for p in args.source.rglob('*')
                    if p.is_file() and '.git' not in p.relative_to(args.source).parts}
        all_before = snapshot()
        entries = []
        for name in PATCHES:
            file = args.source / name
            before = file.read_bytes()
            after = transform(name, before.decode()).encode()
            assert after != before, 'Fresh application required: ' + name
            file.write_bytes(after)
            entries.append(dict(path=name, before=digest(before), after=digest(after)))
        all_after = snapshot()
        changed = {name for name in all_before.keys() | all_after.keys()
                   if all_before.get(name) != all_after.get(name)}
        assert changed == set(PATCHES), sorted(changed)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.with_name('TEXT-REFLOW-BYTE-MANIFEST.json').write_text(json.dumps(dict(
            schema=1, before=all_before, after=all_after,
            changed_files=sorted(changed), unexpected_changes=[]), indent=2, sort_keys=True) + '\n')
        args.receipt.write_text(json.dumps(dict(
            schema=1, candidate=2103294, locked_parent=2103293,
            changed_files=entries, unexpected_native_source_changes=0,
            resolver_2103291_changed=False, container_2103293_changed=False,
            window_reload=False, providers_changed=False, playback_changed=False,
            cobra_changed=False, physical_verified=False, locked=False,
            protected_parent_sources={name: sha for name, sha in all_before.items()
                if name in {'xbmc/guilib/GUIControl.cpp','xbmc/guilib/GUIControl.h',
                    'xbmc/guilib/GUIControlGroup.cpp','xbmc/guilib/GUIControlGroup.h',
                    'xbmc/guilib/GUIControlFactory.cpp','xbmc/guilib/GUIWindow.cpp','xbmc/guilib/GUIWindow.h',
                    'xbmc/guilib/GUIListItemLayout.cpp','xbmc/guilib/GUIListItemLayout.h',
                    'xbmc/guilib/GUIBaseContainer.cpp','xbmc/guilib/GUIPanelContainer.cpp'}}), indent=2) + '\n')
    else:
        receipt = json.loads(args.receipt.read_text())
        assert {e['path'] for e in receipt['changed_files']} == set(PATCHES)
        for entry in receipt['changed_files']:
            data = (args.source / entry['path']).read_bytes()
            assert digest(data) == entry['after'], entry['path']
            assert b'INFINITY_TEXT_REFLOW_V1' in data, entry['path']
        assert len(receipt['protected_parent_sources']) == 11
        for name, sha in receipt['protected_parent_sources'].items():
            assert digest((args.source / name).read_bytes()) == sha, name
    print('PASS 2103294 text cache', args.command)

if __name__ == '__main__':
    main()
