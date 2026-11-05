"""Finite host renderer/actions; never invoke an application shutdown path."""
import json
from pathlib import Path
import time
import traceback
import xbmc
import xbmcgui
from candidate_media_view import publish_browser_genres

BASE = Path(__file__).resolve().parents[1]
C = json.loads((BASE / 'config.json').read_text())
OUT = Path(C['output'])
result = {'platform':'upstream Linux Kodi 21.2 + explicit responsive fixture projection',
          'Android':'NOT_RUN', 'physical_Fold':'NOT_RUN', 'viewport':C['viewport'],
          'source_sha256':C['source_sha256'], 'presentation_sha256':C.get('presentation_sha256'),
          'checks':[], 'observations':[]}


def check(name, ok):
    result['checks'].append({'name':name, 'passed':bool(ok)})
    (OUT/'PARTIAL.json').write_text(json.dumps(result,indent=2)+'\n')
    if not ok:
        raise RuntimeError(name)


def wait(predicate, seconds=18):
    until = time.monotonic()+seconds
    while time.monotonic()<until:
        if predicate():
            return True
        xbmc.sleep(100)
    return False


def shot(name):
    xbmc.sleep(400)
    xbmc.executebuiltin('TakeScreenshot(%s)' % (OUT/(name+'.png')))
    check('screenshot:'+name,wait(lambda:(OUT/(name+'.png')).exists(),5))


def selected(index):
    xbmc.executebuiltin('SetFocus(50,%d,absolute)' % index)
    check('selected-item:%s'%index, wait(lambda:xbmc.getInfoLabel('Container(50).ListItem.Label').startswith('Media %02d'%index)))
    check('selected-genre-presentation:%s'%index,publish_browser_genres(xbmc,xbmcgui) in ('published','unchanged'))


try:
    check('skin-running',wait(lambda:xbmc.getInfoLabel('Skin.CurrentTheme')!='' and xbmcgui.getCurrentWindowId()!=10099,35))
    home=xbmcgui.Window(10000)
    home.setProperty('Infinity.SystemTheme','dark')
    home.setProperty('Infinity.OptionalMotionAllowed','false')
    xbmc.executebuiltin('Skin.SetString(Infinity.HomeView,auto)')
    xbmc.executebuiltin('Skin.SetBool(List.MovieCases)')
    xbmc.executebuiltin('Skin.SetBool(Enable.SlimList)' if C.get('slim') else 'Skin.Reset(Enable.SlimList)')
    xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinitybrowserqa/?kind=movies)')
    check('synthetic-movies-ready',wait(lambda:xbmcgui.getCurrentWindowId()==10025 and
        xbmc.getInfoLabel('Container.Content')=='movies' and not xbmc.getCondVisibility('Container.IsUpdating')))
    xbmc.executebuiltin('Container.SetViewMode(50)')
    check('original-view50',wait(lambda:xbmc.getCondVisibility('Control.IsVisible(50)')))
    selected(1)
    window=xbmcgui.Window(10025)
    panel=window.getControl(50)
    result['observations'].append({'container_width':panel.getWidth(),'container_height':panel.getHeight(),
                                  'position':panel.getPosition(),'title':xbmc.getInfoLabel('Container(50).ListItem.Label')})
    check('selected-metadata', 'Synthetic metadata for selected item 01' in xbmc.getInfoLabel('Container(50).ListItem.Plot'))
    check('case-regression-flag-enabled',xbmc.getCondVisibility('Skin.HasSetting(List.MovieCases)'))
    check('case-regression-resolution-absent',xbmc.getInfoLabel('Container(50).ListItem.VideoResolution')=='')
    check('play-affordance-valid',xbmc.getCondVisibility('Control.IsVisible(98070)'))
    check('trailer-affordance-valid',xbmc.getCondVisibility('Control.IsVisible(98071)'))
    check('info-affordance-valid',xbmc.getCondVisibility('Control.IsVisible(98072)'))
    check('real-genre-chip-1',wait(lambda:xbmc.getCondVisibility('Control.IsVisible(98090)')))
    check('real-genre-chip-2',xbmc.getCondVisibility('Control.IsVisible(98091)'))
    shot('movies-dark')
    home.setProperty('Infinity.SystemTheme','light')
    shot('movies-light-live-switch')
    selected(2)
    check('missing-poster-not-directory-icon',xbmc.getInfoLabel('Container(50).ListItem.Art(poster)')=='')
    # Kodi does not refresh child visibility after its ancestor collapses.
    # Inspect the actual action group that is rendered/removed by the stack.
    check('missing-trailer-action-hidden',wait(lambda:not xbmc.getCondVisibility('Control.IsVisible(98081)')))
    shot('missing-art-light')
    home.setProperty('Infinity.SystemTheme','dark')
    xbmc.sleep(1500)
    selected(1)
    shot('movies-dark-return')
    if C.get('actions'):
        # Send clicks through the actual skin buttons; observe the original APIs.
        xbmc.executebuiltin('SetFocus(98072)')
        check('info-real-control-focus',wait(lambda:window.getFocusId()==98072))
        xbmc.executebuiltin('Action(Select)')
        check('native-info-opened',wait(lambda:xbmcgui.getCurrentWindowDialogId()==12003))
        shot('native-info')
        xbmc.executebuiltin('Action(Back)')
        check('info-return-keeps-browser',wait(lambda:xbmcgui.getCurrentWindowDialogId()==9999 and xbmcgui.getCurrentWindowId()==10025))
        for cid, name in [(98070,'play'),(98071,'trailer')]:
            xbmc.executebuiltin('SetFocus(%d)'%cid)
            check('native-'+name+'-real-control-focus',wait(lambda:window.getFocusId()==cid))
            shot('native-'+name+'-control-focused')
            xbmc.executebuiltin('Action(Select)')
            player=xbmc.Player()
            check('native-'+name+'-decoded',wait(lambda:player.isPlayingVideo()))
            check('native-'+name+'-progress',wait(lambda:player.isPlayingVideo() and player.getTime()>.4,8))
            xbmc.executebuiltin('PlayerControl(Stop)')
            check('native-'+name+'-returned',wait(lambda:not player.isPlaying()))
            xbmc.executebuiltin('ActivateWindow(Videos)')
            check('native-'+name+'-same-browser',wait(lambda:xbmcgui.getCurrentWindowId()==10025))
            selected(1)
    xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.infinitybrowserqa/?kind=tvshows)')
    check('synthetic-shows-ready',wait(lambda:xbmc.getInfoLabel('Container.Content')=='tvshows' and not xbmc.getCondVisibility('Container.IsUpdating')))
    xbmc.executebuiltin('Container.SetViewMode(50)');selected(1)
    check('folder-has-no-play-button',wait(lambda:not xbmc.getCondVisibility('Control.IsVisible(98080)')))
    check('show-info-available',xbmc.getCondVisibility('Control.IsVisible(98072)'))
    shot('shows-dark')
    result['status']='PASS_SELECTED_HOST_RENDERER_ACTION_CHECKS'
except Exception:
    result['status']='FAIL'
    result['error']=traceback.format_exc()
    try:
        shot('failure')
    except Exception:
        pass
finally:
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
