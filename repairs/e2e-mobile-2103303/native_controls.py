#!/usr/bin/env python3
"""Guarded native control fixes. Apply after the exact 2103295 engine lineage.

This does not claim ownership of historical crashes or modify video framing.
"""
import argparse
import hashlib
import json
from pathlib import Path


def once(s, old, new):
    if s.count(old) != 1:
        raise ValueError('Native preimage mismatch: '+old[:100])
    return s.replace(old, new, 1)


def apply(root):
    changes = []
    def change(name, transform):
        p=root/name; before=p.read_bytes(); after=transform(before.decode()).encode()
        p.write_bytes(after)
        changes.append({'path':name,'before':hashlib.sha256(before).hexdigest(),
                        'after':hashlib.sha256(after).hexdigest()})

    def radio_h(s):
        return once(s,'protected:\n','protected:\n  void ProcessText(unsigned int currentTime) override;\n')
    def radio_cpp(s):
        s=once(s,'#include "GUIRadioButtonControl.h"','#include "GUIRadioButtonControl.h"\n\n#include <algorithm>')
        return once(s,'void CGUIRadioButtonControl::Render()','''// Keep both native labels out of the actual switch rectangle, including after
// retained reflow. The entire original button remains the single touch target.
void CGUIRadioButtonControl::ProcessText(unsigned int currentTime)
{
  const float originalMax = m_labelMaxWidth;
  if (!m_useLabel2)
  {
    const float switchLeft = m_radioPosX != 0.0f
                                 ? m_radioPosX
                                 : GetWidth() - 8.0f - m_imgRadioOnFocus->GetWidth();
    const float available = std::max(1.0f, switchLeft - 16.0f);
    m_labelMaxWidth = originalMax > 0.0f ? std::min(originalMax, available) : available;
  }
  CGUIButtonControl::ProcessText(currentTime);
  m_labelMaxWidth = originalMax;
}

void CGUIRadioButtonControl::Render()''')
    change('xbmc/guilib/GUIRadioButtonControl.h',radio_h)
    change('xbmc/guilib/GUIRadioButtonControl.cpp',radio_cpp)

    def touch_h(s):
        return once(s,'  CCriticalSection m_critical;',
                    '  std::chrono::steady_clock::time_point m_holdDeadline{};\n  CCriticalSection m_critical;')
    def touch_cpp(s):
        s=once(s,'''  std::unique_lock<CCriticalSection> lock(m_critical);

  bool result = true;''','''  // Join the previous timer BEFORE taking the gesture lock. Stop(true) under
  // this lock can deadlock against its queued OnTimeout callback. Starting a
  // new CTimer while the cancelled one still runs can also drop the new hold.
  if (event == TouchInputDown)
    m_holdTimer->Stop(true);

  std::unique_lock<CCriticalSection> lock(m_critical);

  bool result = true;''')
        s=once(s,'''    case TouchInputAbort:
    {
      triggerDetectors(event, pointer);''','''    case TouchInputAbort:
    {
      m_holdTimer->Stop(false);
      m_holdDeadline = {};
      triggerDetectors(event, pointer);''')
        s=once(s,'''    case TouchInputDown:
    {
      m_pointers[pointer].down.x = x;''','''    case TouchInputDown:
    {
      m_holdDeadline = std::chrono::steady_clock::now() + TOUCH_HOLD_TIMEOUT;
      if (pointer == 0)
        m_detectors.clear();
      m_pointers[pointer].down.x = x;''')
        s=once(s,'          m_holdTimer->Stop(true);','          // Previous timer was joined before the gesture lock.')
        s=once(s,'''void CGenericTouchInputHandler::OnTimeout()
{
  std::unique_lock<CCriticalSection> lock(m_critical);

  switch (m_gestureState)''','''void CGenericTouchInputHandler::OnTimeout()
{
  std::unique_lock<CCriticalSection> lock(m_critical);

  // A queued timeout is evidence only of its timer, not of a current hold.
  // Validate the current pointer and movement, including updates received
  // immediately before HandleTouchInput(Move/Up) obtains the same lock.
  if (!m_pointers[0].valid() || m_pointers[0].moving ||
      std::chrono::steady_clock::now() < m_holdDeadline)
    return;

  switch (m_gestureState)''')
        s=once(s,'      if (!m_pointers[0].moving && !m_pointers[1].moving)',
                    '      if (m_pointers[1].valid() && !m_pointers[1].moving)')
        s=once(s,'        if (m_gestureState == TouchGestureSingleTouch)\n          OnTap(x, y, 1);',
                    '        if (m_gestureState == TouchGestureSingleTouch && !m_pointers[pointer].moving)\n          OnTap(x, y, 1);')
        return s
    change('xbmc/input/touch/generic/GenericTouchInputHandler.h',touch_h)
    change('xbmc/input/touch/generic/GenericTouchInputHandler.cpp',touch_cpp)
    change('xbmc/application/ApplicationSkinHandling.cpp',lambda s:once(s,
        'HELPERS::ShowYesNoDialogText(CVariant{13123}, CVariant{13111}, CVariant{""}, CVariant{""},',
        'HELPERS::ShowYesNoDialogText(CVariant{13123}, CVariant{13111}, CVariant{"Revert"}, CVariant{"Keep"},'))
    def dimensions(s):
        old='''  value = ParsePosition(pNode->FirstChild()->Value(), parentSize);
  return true;
}

bool CGUIControlFactory::GetDimensions'''
        new='''  value = ParsePosition(pNode->FirstChild()->Value(), parentSize);
  // Optional responsive cap. Existing dimensions without max are unchanged.
  // Retained reflow uses this same resolver, so window resize recomputes both
  // the visual bounds and the actual control hit rectangle.
  if (pNode->Attribute("max"))
  {
    const float maximum = ParsePosition(pNode->Attribute("max"), parentSize);
    if (maximum > 0.0f)
      value = std::min(value, maximum);
  }
  return true;
}

bool CGUIControlFactory::GetDimensions'''
        return once(s,old,new)
    change('xbmc/guilib/GUIControlFactory.cpp',dimensions)
    return changes


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    changes=apply(a.source)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps({'changes':changes,'crash_ownership_proven':False},indent=2)+'\n')
