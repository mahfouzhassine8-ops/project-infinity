"""Actual ADB taps/holds against the full signed candidate in a disposable emulator."""
import json
from pathlib import Path
import struct
import time

def exercise(probe, out, report):
    records = report['ui_interactions'] = []
    def require(ok, reason):
        if not ok: raise RuntimeError('Actual UI integration: ' + reason)
    def save():
        (out / 'UI-INTERACTIONS.json').write_text(json.dumps(dict(records=records,
            passed=False, physical_fold_verified=False, crash_fixed=False), indent=2))
    def observe(operation='state', *params):
        nonce = str(time.monotonic_ns())
        require(probe.rpc('Addons.ExecuteAddon', dict(addonid='script.infinity.uitest',
            params=[operation, *params, nonce], wait=False)) == 'OK', 'observer could not run')
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            row = probe.read_json(probe.PROFILE + '/infinity-ui-observation.json')
            if row.get('request') == nonce:
                require(not row.get('error'), row.get('error', ''))
                return row
            time.sleep(.2)
        raise RuntimeError('UI observer did not complete')
    def capture(name, state=None):
        png = probe.adb('exec-out', 'screencap', '-p', binary=True)
        require(png.startswith(b'\x89PNG\r\n\x1a\n'), 'No actual Android screenshot')
        (out / (name + '.png')).write_bytes(png)
        row = dict(name=name, state=state or observe(), physical_size=struct.unpack('>II', png[16:24]))
        records.append(row); save(); return row
    def wait_for(predicate, label, seconds=30):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            state = observe()
            if predicate(state): return state
            time.sleep(.25)
        raise RuntimeError('UI did not reach ' + label + ': ' + json.dumps(state))
    def point(state, x, y):
        png = probe.adb('exec-out', 'screencap', '-p', binary=True)
        width, height = struct.unpack('>II', png[16:24])
        vw, vh = state['viewport']
        return round(x * width / vw), round(y * height / vh)
    def tap(state, xy, hold=False):
        x, y = point(state, *xy)
        if hold: probe.shell('input', 'swipe', x, y, x, y, 1100)
        else: probe.shell('input', 'tap', x, y)
        time.sleep(.6)
    def token(state, ident=50):
        return state['labels'].get('Container(' + str(ident) + ').ListItem.Property(Infinity.UI.Token)', '')
    def popup(state): return state.get('popup') == '1'
    def rowpoint(state, label):
        card, listing = state['controls']['100'], state['controls']['50']
        labels = [x['label'] for x in listing['items']]
        require(label in labels, 'Missing row ' + label + ': ' + repr(labels))
        index = labels.index(label)
        return (card['position'][0] + listing['position'][0] + 120,
                card['position'][1] + listing['position'][1] + index * 78 + 35)
    def invoke(state, label):
        xy = rowpoint(state, label)
        tap(state, xy)
        focused = observe()
        require(popup(focused), 'Focusing a popup row performed its action')
        tap(focused, xy)
    def back():
        probe.rpc('Input.Back'); time.sleep(.6)
    def browse():
        observe('browse')
        return wait_for(lambda s: s['window'] == 11193 and
            int(s['labels'].get('Container(50).NumItems') or 0) >= 12, 'complete Video Sources grid')

    # This is an isolated emulator media fixture, never user playback content.
    movie = Path('infinity-ui-fixture.mp4')
    require(movie.is_file(), 'generated sample missing')
    probe.adb('push', movie, probe.PROFILE + '/' + movie.name)
    probe.shell('chmod', '644', probe.PROFILE + '/' + movie.name)
    observe('seed')
    for viewport, size in (('cover', '1080x2400'), ('inner', '1800x1440')):
        probe.shell('wm', 'size', size); probe.shell('wm', 'density', '320'); time.sleep(3)
        for theme in ('light', 'dark', 'OLED'):
            observe('theme', theme)
            state = browse()
            grid = state['controls']['50']
            require(grid.get('width', 0) > 0 and grid.get('height', 0) > 0, 'grid geometry unavailable')
            item_height = grid['height'] * .21809829
            item_width = item_height * .668085106
            columns = int(grid['width'] // item_width)
            require(columns >= 2, 'both grid columns unavailable')
            for side, col in (('left', 0), ('right', columns - 1)):
                xy = (grid['position'][0] + (col + .5) * item_width,
                      grid['position'][1] + item_height * .5)
                # First tap must only select, including the initially focused item.
                tap(state, xy)
                first = observe()
                require(first['window'] == 11193 and not popup(first), 'first tap launched or opened popup')
                selected = token(first)
                require(bool(selected), 'tapped tile identity missing')
                tap(first, xy, hold=True)
                menu = wait_for(popup, 'item-specific add-on menu')
                require(menu['title'].startswith('Add-on Options — '), 'wrong popup')
                labels = [x['label'] for x in menu['controls']['50']['items']]
                required = ['Open','Add-on Information','Add-on Settings','Add to Favourites',
                            'Add to Infinity Rails','Hide from This View','More / Manage Add-on']
                mandatory = ['Open','Add-on Information','Add to Favourites']
                if not selected.startswith(('script.infinity.', 'service.infinity.', 'skin.infinity.')):
                    mandatory += ['Hide from This View','More / Manage Add-on']
                require(labels == [x for x in required if x in labels] and all(x in labels for x in mandatory),
                        'menu ordering/capabilities wrong')
                capture(viewport + '-' + theme.lower() + '-' + side + '-menu', menu)
                tap(menu, rowpoint(menu, 'Open'))
                require(popup(observe()), 'Open activated when merely selected')
                back()
                restored = observe()
                require(restored['window'] == 11193 and token(restored) == selected and
                        restored['labels'].get('Container(50).CurrentPage') == first['labels'].get('Container(50).CurrentPage'),
                        'dismissal changed selection or scroll')
                # The original first tap is still armed after harmless dismissal.
                tap(restored, xy)
                opened = wait_for(lambda s: s['window'] == 10025, 'second-tap add-on open')
                capture(viewport + '-' + theme.lower() + '-' + side + '-opened', opened)
                back(); state = wait_for(lambda s: s['window'] == 11193, 'return to exact grid')
            # Scroll through the real native panel; hold must follow the new item.
            x, y = point(state, grid['position'][0] + grid['width'] * .75, grid['position'][1] + grid['height'] * .8)
            endx, endy = point(state, grid['position'][0] + grid['width'] * .75, grid['position'][1] + grid['height'] * .3)
            probe.shell('input','swipe',x,y,endx,endy,500); time.sleep(1)
            xy = (grid['position'][0] + (columns - .5) * item_width, grid['position'][1] + item_height * .5)
            tap(state, xy); scrolled = observe(); tap(scrolled, xy, hold=True)
            menu = wait_for(popup, 'scrolled item menu'); capture(viewport+'-'+theme.lower()+'-scrolled', menu)
            back(); restored = observe()
            require(token(restored) == token(scrolled), 'scrolled popup dismissed to wrong item')

    # Exercise actual view-local hiding and restoration without disabling.
    selected = token(restored)
    require(selected.startswith('plugin.video.infinityuitest'), 'mutation requires a harmless fixture')
    probe.rpc('Input.ContextMenu')
    menu = wait_for(popup, 'fixture context through native D-pad route')
    invoke(menu, 'Add to Favourites')
    wait_for(lambda s:not popup(s), 'favourite action completed')
    favourites = probe.rpc('Favourites.GetFavourites', dict(properties=['windowparameter']))
    require(any(f.get('windowparameter') == 'plugin://'+selected+'/' for f in favourites['favourites']),
            'favourite destination not saved')
    report['ui_expected_favourite'] = 'plugin://'+selected+'/'
    probe.rpc('Input.ContextMenu'); menu=wait_for(popup,'hide menu')
    invoke(menu,'Hide from This View')
    wait_for(lambda s:not popup(s) and all(r.get('token') != selected for r in s['controls']['50'].get('items',[])),
             'hidden tile removed only from grid')
    require(probe.rpc('Addons.GetAddonDetails',dict(addonid=selected,properties=['enabled']))['addon']['enabled'],
            'Hide disabled the add-on')
    observe('restore'); restore=wait_for(popup,'hidden tile recovery')
    label=restore['controls']['50']['items'][0]['label']
    invoke(restore,label)
    wait_for(lambda s:not popup(s) and any(r.get('token') == selected for r in s['controls']['50'].get('items',[])),
             'hidden tile restored')
    capture('hidden-fixture-restored')

    # Resume Home items retain their original movie and episode identity.
    report['ui_expected_watchlist'] = []
    for media, section, ident in (('movie', 'movies', 8830), ('tv','tvshows',8831)):
        observe('home', section)
        home = wait_for(lambda s: s['window'] == 10000 and
            int(s['labels'].get('Container('+str(ident)+').NumItems') or 0) > 0,
            'Home Continue ' + media)
        rail = home['controls'][str(ident)]; group = home['controls']['40001']
        xy = (group['position'][0] + rail['position'][0] + rail['height'] * .561219512 * .4,
              group['position'][1] + rail['position'][1] + rail['height'] * .4)
        tap(home, xy, hold=True)
        menu = wait_for(popup, 'original Resume context for ' + media)
        labels = [x['label'] for x in menu['controls']['50']['items']]
        require(labels == ['Mark Watched','Reset Progress','Add to Watchlist','Add to Collection','Rate',
                           'Add to Custom List','Remove from Continue Playing'], 'Resume actions not original item menu')
        capture('continue-'+media+'-context', menu)
        tap(menu, rowpoint(menu, 'Mark Watched'))
        require(popup(observe()), 'Mark Watched ran on focus')
        back()
        require(observe()['window'] == 10000, 'Resume dismissal left Home')
        # Cross the real helper -> original controller writer boundary, then
        # verify the same movie/episode memberships after actual process restart.
        key=token(home,ident)
        require(len(key)==64,'Continue identity unavailable')
        tap(observe(),xy,hold=True)
        menu=wait_for(popup,'Watchlist mutation for '+media)
        invoke(menu,'Add to Watchlist')
        data_path=probe.PROFILE+'/addon_data/script.infinity.commandcenter/continue-watching.json'
        wait_for(lambda s:not popup(s) and key in probe.read_json(data_path).get('watchlist',{}),
                 'original controller durable Watchlist mutation')
        report['ui_expected_watchlist'].append(key)
        capture('continue-'+media+'-watchlist-saved')

    # Exercise the exact player teardown and both navigation paths with public
    # local media. This cannot diagnose or rule out the physical Fold failure.
    for path in ('A', 'B'):
        observe('choices')
        wait_for(lambda s:s['window']==10025, 'provider movie choices')
        probe.rpc('Player.Open', dict(item=dict(file=probe.PROFILE+'/'+movie.name)))
        deadline = time.monotonic()+35
        while time.monotonic()<deadline:
            players=probe.rpc('Player.GetActivePlayers')
            if any(p.get('type')=='video' for p in players):break
            time.sleep(.3)
        else:raise RuntimeError('Native video fixture did not start')
        player=next(p['playerid'] for p in players if p.get('type')=='video')
        time.sleep(2)
        if path == 'A':
            repeat = probe.rpc('Player.GetProperties',dict(playerid=player,properties=['repeat']))['repeat']
            osd=observe('osd'); original=osd['rotation']
            rotated=observe('rotate')
            require(rotated['rotation'] != original,'Rotate did not change its actual state')
            capture('rotate-first-state',rotated)
            returned=observe('rotate')
            require(returned['rotation'] == original,'Rotate did not restore Follow Device state')
            require(probe.rpc('Player.GetProperties',dict(playerid=player,properties=['repeat']))['repeat']==repeat,
                    'Rotate changed Repeat')
            capture('rotate-returned-state',returned)
            drawer=observe('drawer')
            require('error' in drawer['controls']['280'],'Display Mode still exists in Playback')
            capture('playback-without-display-mode',drawer)
        probe.rpc('Player.Stop', dict(playerid=player)); time.sleep(2)
        choices=observe(); require(choices['window']==10025, 'Stop did not restore movie choices')
        if path=='B':
            observe('home','movies')
            require(observe()['window']==10000, 'Stop then Home did not return Home')
        time.sleep(5)
        require(probe.rpc('JSONRPC.Ping')=='pong', 'engine unavailable after Stop path '+path)
        require(any(p['pid']==report['native_owner']['pid'] for p in probe.processes()), 'native process changed after Stop')
        capture('stop-path-'+path)
    report['ui_emulator_smoke_passed'] = True
    (out/'UI-INTERACTIONS.json').write_text(json.dumps(dict(records=records, passed=True,
        physical_fold_verified=False, crash_fixed=False, actual_signed_apk_sha256=report['apk_sha256']),indent=2))
