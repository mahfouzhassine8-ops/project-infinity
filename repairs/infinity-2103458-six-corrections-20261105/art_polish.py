"""Selected existing-skin artwork fields only; all actions/native files frozen."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
PREFIX=R/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified'
EP='String.IsEqual(Container(50).ListItem.DBType,episode) + !String.IsEmpty(Container(50).ListItem.Art(thumb))'
INFO_VAR='''  <variable name="InfinityMedia_InfoArtwork">
    <value condition="String.IsEqual(ListItem.DBType,episode) + !String.IsEmpty(ListItem.Art(poster))">$INFO[ListItem.Art(poster)]</value>
    <value condition="String.IsEqual(ListItem.DBType,episode) + !String.IsEmpty(ListItem.Art(season.poster))">$INFO[ListItem.Art(season.poster)]</value>
    <value condition="String.IsEqual(ListItem.DBType,episode) + !String.IsEmpty(ListItem.Art(tvshow.poster))">$INFO[ListItem.Art(tvshow.poster)]</value>
    <value condition="String.IsEqual(ListItem.DBType,episode) + !String.IsEmpty(ListItem.Art(thumb))">$INFO[ListItem.Art(thumb)]</value>
    <value>$VAR[PosterThumb]</value>
  </variable>
'''
FRAME='''    <control type="image">
      <left>3.9583%</left>
      <top>13.5185%</top>
      <width>17.395687%</width>
      <height>43.425866%</height>
      <texture border="24" colordiffuse="$VAR[InfinityLegacyBorder]">infinity_glass/rim.png</texture>
    </control>
'''
OLD_IMAGE='''      <aspectratio>keep</aspectratio>
      <texture background="true">$VAR[PosterThumb]</texture>'''
NEW_IMAGE='''      <aspectratio align="left" aligny="top">keep</aspectratio>
      <texture background="true">$VAR[InfinityMedia_InfoArtwork]</texture>
      <bordertexture border="24" colordiffuse="$VAR[InfinityLegacyBorder]">infinity_glass/rim.png</bordertexture>
      <bordersize>2</bordersize>'''
def list_polish(s):
 start=s.index('  <variable name="InfinityMedia_SelectedPoster">');end=s.index('  </variable>',start)
 portion=s[start:end];assert portion.count('    <value />')==1
 portion=portion.replace('    <value />','    <value condition="'+EP+'">$INFO[Container(50).ListItem.Art(thumb)]</value>\n    <value />')
 s=s[:start]+portion+s[end:];s=s.replace('<includes>','<includes>\n'+INFO_VAR,1)
 old='<visible>!String.IsEmpty(Container(50).ListItem.Art(poster)) | !String.IsEmpty(Container(50).ListItem.Art(season.poster)) | !String.IsEmpty(Container(50).ListItem.Art(tvshow.poster))</visible>'
 assert s.count(old)==1
 pos=s.index(old);start=s.rfind('            <control type="image">',0,pos);end=s.index('            </control>',pos)+len('            </control>')
 original=s[start:end]
 no_posters='String.IsEmpty(Container(50).ListItem.Art(poster)) + String.IsEmpty(Container(50).ListItem.Art(season.poster)) + String.IsEmpty(Container(50).ListItem.Art(tvshow.poster))'
 thumb=original.replace('<height max="540">55%</height>','<height>216</height>').replace(old,'<visible>'+EP+' + '+no_posters+'</visible>')
 s=s[:end]+'\n'+thumb+s[end:]
 return s

def info_polish(s):
 assert s.count(OLD_IMAGE)==1 and s.count(FRAME)==1
 return s.replace(OLD_IMAGE,NEW_IMAGE).replace(FRAME,'')
if __name__=='__main__':
 for name,fn in [('Includes_InfinityMediaLists.xml',list_polish),('DialogVideoInfo.xml',info_polish)]:
  p=PREFIX/name;p.write_text(fn(p.read_text()))
