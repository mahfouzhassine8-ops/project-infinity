"""Synthetic visual cases only, never real provider/media/user data."""
import json,sys
from pathlib import Path
from urllib.parse import parse_qs
import xbmcgui,xbmcplugin
BASE=Path(QA_PATH);kind=parse_qs(sys.argv[2].lstrip('?')).get('kind',['movies'])[0]
mediatype={'movies':'movie','tvshows':'tvshow','seasons':'season','episodes':'episode'}[kind]
handle=int(sys.argv[1]);xbmcplugin.setContent(handle,kind);xbmcplugin.setPluginCategory(handle,'Synthetic '+kind)
for i in range(1,5):
 label='Media %02d — %s fixture with a readable long title'%(i,kind)
 item=xbmcgui.ListItem(label)
 info={'title':label,'mediatype':mediatype,'year':2024,'genre':'Drama / Adventure','rating':7.8,'mpaa':'PG-13','plot':('Synthetic '+kind+' synopsis. All supplied details remain available. ')*12+'End of supplied synopsis.','director':['Fixture Director'],'writer':['Fixture Writer'],'studio':['Fixture Studio'],'premiered':'2024-01-02'}
 if kind in ('movies','episodes'):info['duration']=5880 if kind=='movies' else 1440
 if kind in ('seasons','episodes'):info.update(tvshowtitle='Fixture Show',season=2)
 if kind=='episodes':info['episode']=i
 item.setInfo('video',info)
 item.setCast([{'name':'Fixture Actor %d'%j,'role':'Role %d'%j,'thumbnail':str(BASE/'poster.png'),'order':j} for j in range(1,4)])
 if kind=='episodes':item.setArt({'thumb':str(BASE/'fanart.png')})
 elif kind=='seasons':item.setArt({'season.poster':str(BASE/'poster.png')})
 else:item.setArt({'poster':str(BASE/'poster.png')})
 item.setArt({'icon':str(BASE/'fanart.png')})
 folder=kind in ('tvshows','seasons');item.setProperty('IsPlayable','false' if folder else 'true')
 nextkind='seasons' if kind=='tvshows' else 'episodes'
 xbmcplugin.addDirectoryItem(handle,'plugin://plugin.video.infinitybrowserqa/?kind='+nextkind,item,folder)
xbmcplugin.endOfDirectory(handle,succeeded=True,cacheToDisc=False)
