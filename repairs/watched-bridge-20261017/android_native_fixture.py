"""Real native row lookup on an isolated signed-APK emulator fixture."""
import hashlib
import json
from pathlib import Path
import traceback
import threading
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = 'script.infinity.watchednative.test'
profile = Path(xbmcvfs.translatePath('special://profile/'))
root = Path(xbmcvfs.translatePath(xbmcaddon.Addon(ADDON).getAddonInfo('path')))
result = dict(passed=False, real_android_native_index=True, real_provider_addons_tested=False,
              physical_fold_verified=False, tests=[])
home = xbmcgui.Window(10000)
PROP = 'Infinity.ResumeHub.PresentationSnapshot'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def identity(kind='movie', scope='movie', ids=None, season=1, episode=2):
    value = dict(kind=kind, scope=scope, ids=ids or {'tmdb': '123'})
    if kind == 'episode': value.update(season=season, episode=episode)
    return value


def publish(rows, providers=None, path=None):
    payload = dict(schema=1, profile=str(path or profile).rstrip('/\\'), revision='a' * 64,
                   records=rows, providers=providers or {})
    home.setProperty(PROP, json.dumps(payload, separators=(',', ':')))
    xbmc.executebuiltin('InfinityResumeHubUpdate()', True)
    xbmc.sleep(120)


def row(kind='movie', ids=None, path='plugin://plugin.video.fixture/?item=123', season=1, episode=2, count=0):
    item = xbmcgui.ListItem(label='Offline native row fixture', path=path)
    tag = item.getVideoInfoTag()
    tag.setMediaType(kind); tag.setUniqueIDs(ids or {'tmdb': '123'}); tag.setPlaycount(count)
    if kind == 'episode': tag.setSeason(season); tag.setEpisode(episode)
    return item


class NativeRows(xbmcgui.WindowXMLDialog):
    def onInit(self):
        threading.Thread(target=self.verify, name="native-row-check").start()

    def verify(self):
        try:
            require(xbmc.getInfoLabel('Window(Home).Property(Infinity.ResumeHub.BridgeVersion)') == '1', 'Compiled bridge capability missing')
            control = self.getControl(50)
            def check(name, item, expected):
                control.reset(); control.addItem(item); control.selectItem(0); self.setFocusId(50)
                xbmc.sleep(120)
                observed = xbmc.getInfoLabel('Container(50).ListItem.Property(Infinity.ResumeHub.Watched)')
                require(observed == expected, name + ': expected ' + repr(expected) + ', got ' + repr(observed))
                result['tests'].append(dict(name=name, observed=observed, expected=expected))
            movie = identity(ids={'tmdb': '123', 'imdb': 'tt00123'})
            publish([dict(identity=movie, watched=True)])
            check('unmodified plugin row reads native index', row(), 'true')
            check('cross-provider movie alias', row(ids={'imdb': 'tt00123'}, path='plugin://plugin.video.other/?item=123'), 'true')
            check('equal foreign namespace does not match', row(ids={'tvdb': '123'}), '')
            check('contradictory namespaces withheld', row(ids={'tmdb': '123', 'imdb': 'tt00999'}), '')
            check('unplayed title remains unknown', row(ids={'tmdb': '456'}), '')
            check('show folder never becomes watched movie', row(kind='tvshow'), '')
            publish([dict(identity=movie, watched=False)])
            check('explicit Unwatched over native playcount', row(count=1), 'false')
            show = identity('episode', 'show_episode')
            publish([dict(identity=show, watched=True)], {'plugin.video.pov': 'show_episode', 'plugin.video.umbrella': 'show_episode'})
            for addon in ('pov', 'umbrella'):
                check('series scope ' + addon, row(kind='episode', path='plugin://plugin.video.' + addon + '/?play=123'), 'true')
            check('unknown anime numbering withheld', row(kind='episode', path='plugin://plugin.video.otaku/?play=123'), '')
            check('absolute episode number not guessed', row(kind='episode', path='plugin://plugin.video.pov/?play=123', episode=102), '')
            publish([dict(identity=identity('episode', 'episode'), watched=True)], {'plugin.video.pov': 'show_episode'})
            check('same numeric episode ID never aliases series ID', row(kind='episode', path='plugin://plugin.video.pov/?play=123'), '')
            publish([dict(identity=movie, watched=True)], path=str(profile) + '-wrong-profile')
            check('wrong profile clears derived index', row(), '')
            publish([dict(identity=movie, watched=True), dict(identity=movie, watched=False)])
            check('conflicting records withheld', row(), '')
            # The integration stage enables the actual read-only helper service
            # only after deterministic raw-index cases finish. No row property
            # is set; both states must travel through CC's existing writer.
            response = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method='Addons.SetAddonEnabled', params=dict(addonid='script.infinity.watchedbridge', enabled=True)))))
            require(response.get('result') == 'OK', 'Read-only watched helper enable failed')
            helper = xbmcaddon.Addon('script.infinity.watchedbridge')
            sys.path.insert(0, xbmcvfs.translatePath(helper.getAddonInfo('path')))
            import controller
            cc = xbmcaddon.Addon('script.infinity.commandcenter')
            modules = controller.load(xbmcvfs.translatePath(cc.getAddonInfo('path')))
            cc_profile = Path(xbmcvfs.translatePath(cc.getAddonInfo('profile')))
            item = row()
            selected = modules['context'].selected_entry(item)
            require(selected is not None, 'Actual typed Kodi selection unavailable')
            for action in ('toggle-watchlist', 'toggle-collection', 'mark-watched'):
                require(controller.apply(modules, cc_profile, selected, action), 'Existing checkpointed writer refused ' + action)
            control.reset(); control.addItem(row()); control.selectItem(0); self.setFocusId(50)
            monitor = xbmc.Monitor()
            def await_state(expected, attempts=60):
                for attempt in range(attempts):
                    value = xbmc.getInfoLabel('Container(50).ListItem.Property(Infinity.ResumeHub.Watched)')
                    if value == expected: return
                    monitor.waitForAbort(.1)
                raise RuntimeError('Read-only helper did not publish native state ' + expected)
            await_state('true')
            require(controller.apply(modules, cc_profile, selected, 'mark-unwatched'), 'Unwatched writer action failed')
            await_state('false')
            stored = (cc_profile / 'continue-watching.json').read_bytes()
            payload = home.getProperty(PROP)
            invalid = json.loads(payload); invalid['profile'] += '-cleared-profile-control'
            home.setProperty(PROP, json.dumps(invalid))
            xbmc.executebuiltin('InfinityResumeHubUpdate()', True)
            home.setProperty(PROP, payload)
            await_state('false', attempts=400)
            require((cc_profile / 'continue-watching.json').read_bytes() == stored, 'Read-only republishing changed saved progress')
            result['derived_index_recovery_without_data_write'] = True
            result['helper_pipeline_verified'] = True
            result['helper_pipeline_key'] = selected['key']
            result['passed'] = True
            result['kodi_version'] = xbmc.getInfoLabel('System.BuildVersion')
        except Exception:
            result['failure'] = traceback.format_exc()
        finally:
            publish([])
            home.clearProperty(PROP)
            (profile / 'watched-native-runtime-result.json').write_text(json.dumps(result, indent=2) + '\n')
            self.close()


window = NativeRows('NativeWatchedFixture.xml', str(root), 'Default', '1080i')
window.doModal()
