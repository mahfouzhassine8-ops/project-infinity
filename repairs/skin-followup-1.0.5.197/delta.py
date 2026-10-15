#!/usr/bin/env python3
"""One active XML refinement over exact locked skin 196; preserve its routes."""
import hashlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASELINE_ZIP_SHA256='4bd2483376819089d4fe1ec29a15720fd6ff50dce816bcbba367f3a1312dbc6e'
TARGET='unified/AddonBrowser.xml'
PREIMAGE='2d4ac50b8f92dcc1b5cc8dd7e39eacb58d01a810cf6847be49156177d4ebd16c'


def sha(data):return hashlib.sha256(data).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def once(text,old,new):
    require(text.count(old)==1,'Ambiguous skin preimage: '+old[:90])
    return text.replace(old,new,1)


def repair(original):
    require(sha(original[TARGET])==PREIMAGE,'Skin 196 AddonBrowser preimage mismatch')
    result=dict(original)
    text=original[TARGET].decode()
    start=text.index('      <focusedlayout ')
    end=text.index('      </focusedlayout>',start)+len('      </focusedlayout>')
    focus=text[start:end]
    focus=once(focus,'<font>InfinityBodyBold</font>','<font>InfinitySmall</font>')
    focus=once(focus,'<textcolor>FFFFFFFF</textcolor>',
               '<textcolor>$VAR[InfinityDiggzPrimaryText]</textcolor>')
    focus=once(focus,'          <texture border="18">infinity_ui/focus_trim.png</texture>',
               '          <texture border="18" colordiffuse="$VAR[InfinityPaletteSurfaceElevated]">$VAR[InfinityCardTexture]</texture>')
    rim='''        <control type="image">
          <left>1.4141%</left>
          <top>3.6842%</top>
          <width>97.1717%</width>
          <height>92.6316%</height>
          <texture border="18">infinity_polish/focus_rim.png</texture>
        </control>
'''
    focus=once(focus,'      </focusedlayout>',rim+'      </focusedlayout>')
    text=text[:start]+focus+text[end:]
    text=once(text,'<texturefocus border="16">infinity_ui/focus_trim.png</texturefocus>',
              '<texturefocus border="16">infinity_polish/focus_rim.png</texturefocus>')
    text=once(text,'<focusedcolor>FFFFFFFF</focusedcolor>',
              '<focusedcolor>$VAR[InfinityDiggzPrimaryText]</focusedcolor>')
    result[TARGET]=text.encode()
    require({n for n in original if original[n]!=result[n]}=={TARGET},'Unexpected skin delta')
    return result
