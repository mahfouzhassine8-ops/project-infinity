#!/usr/bin/env python3
"""Emit the bounded scrolling-row hit-test delta; leave all other native files alone."""
from pathlib import Path
from difflib import unified_diff
import argparse, hashlib

PATH='xbmc/guilib/GUIControlGroupList.cpp'
BASE_SHA='09fd3c6b806d7b1db91c7b2bf9de24a7da41c79bc9e03edf4e44931781de33be'

def transform(source):
    start=source.index('EVENT_RESULT CGUIControlGroupList::SendMouseEvent(')
    end=source.index('\nvoid CGUIControlGroupList::UnfocusFromPoint(',start)
    before=source[start:end]
    old='''        if (IsControlOnScreen(pos, child))
        { // we're on screen'''
    assert before.count(old)==1
    after=before.replace(old,'''        // Rendering clips partially visible rows to the viewport. Touch must
        // accept that same visible part, without accepting the clipped portion
        // outside the viewport (e.g. the drawer header/close button).
        const bool insideViewport = childPoint.x >= m_posX && childPoint.x < m_posX + m_width &&
                                    childPoint.y >= m_posY && childPoint.y < m_posY + m_height;
        const float visibleStart = alignOffset + pos - m_scroller.GetValue();
        const bool intersectsViewport = visibleStart < Size() && visibleStart + Size(child) > 0;
        if (insideViewport && intersectsViewport)
        { // dispatch in the same translated coordinates used by Render()''')
    return source[:start]+after+source[end:]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    path=a.source/PATH;data=path.read_bytes()
    assert hashlib.sha256(data).hexdigest()==BASE_SHA, 'Unexpected native preimage; do not apply blindly'
    before=data.decode();after=transform(before)
    print('*** Begin Patch\n*** Update File: '+str(path))
    for line in list(unified_diff(before.splitlines(),after.splitlines(),n=3))[2:]:
        print('@@' if line.startswith('@@') else line)
    print('*** End Patch')
