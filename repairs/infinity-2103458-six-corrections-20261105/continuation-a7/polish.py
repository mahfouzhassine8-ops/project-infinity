"""Exact, bounded visual substitutions; no navigation or native changes."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified'
LABELS=['$INFO[ListItem.Title]','$INFO[ListItem.Year]  •  $INFO[ListItem.Duration]  •  $INFO[ListItem.MPAA]','$INFO[ListItem.Genre]','$INFO[ListItem.Label]','$INFO[ListItem.Director]','$INFO[ListItem.Writer]','$INFO[ListItem.Studio]']
def info(s):
 for label in LABELS:
  old='<label>'+label+'</label>'
  expected=2 if label=='$INFO[ListItem.Label]' else 1
  assert s.count(old)==expected,(label,s.count(old))
  s=s.replace(old,old+'\n      <scroll>true</scroll>')
 assert s.count('aspectratio="1.034482759"')==2
 s=s.replace('aspectratio="1.034482759"','aspectratio="1.6"')
 old='<height>150</height>';assert s.count(old)==1
 s=s.replace(old,'<height>14%</height>')
 return s
def listing(s):
 old='<control type="textbox" id="98064">\n        <width>100%</width>\n        <height min="40" max="30%">auto</height>'
 new='<control type="textbox" id="98064">\n        <width>100%</width>\n        <top>0</top>\n        <height min="40" max="0">auto</height>'
 assert s.count(old)==1
 return s.replace(old,new)
