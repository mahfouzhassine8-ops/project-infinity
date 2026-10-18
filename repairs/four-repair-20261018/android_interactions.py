"""Actual ADB taps/holds against the full signed candidate in a disposable emulator."""
import json
from pathlib import Path
import re
import struct
import subprocess
import time
import xml.etree.ElementTree as ET

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
                (out / 'last-ui-observation.json').write_text(json.dumps(row,indent=2))
                require(not row.get('error'), row.get('error', ''))
                return row
            time.sleep(.2)
        raise RuntimeError('UI observer did not complete')
    def diagnostic_dump(name, service):
        # API35 run 39122376332 exited on one dumpsys input read, although
        # its immediately subsequent final dump succeeded. Keep failed stdout
        # (the original adb helper keeps only stderr) and retry this read once.
        # Never retry a gesture or waive a required application assertion.
        for attempt in (1, 2):
            if attempt == 2:
                # Run39123796362: adbd host-22 write failed/offline, then
                # host-23 reconnected 0.27s later. The immediate second read
                # raced that transport recovery. Wait only for ADB, then prove
                # no Android reboot or Infinity engine restart was hidden.
                waited = subprocess.run(['adb', 'wait-for-device'], capture_output=True,
                                        text=True, timeout=10)
                (out / (name + '-adb-recovery.json')).write_text(json.dumps(dict(
                    returncode=waited.returncode, stdout=waited.stdout,
                    stderr=waited.stderr), indent=2))
                require(waited.returncode == 0, 'ADB did not recover for diagnostic read')
                require(probe.shell('cat', '/proc/sys/kernel/random/boot_id').strip() == boot_id,
                        'Android rebooted during diagnostic read')
                owner = probe.read_json(probe.PRIVATE + '/files/infinity-kodi-process.json')
                require(all(owner.get(k) == report['native_owner'].get(k)
                            for k in ('pid', 'owner', 'launch')) and owner.get('live') is True and
                        any(p['pid'] == owner['pid'] for p in probe.processes()),
                        'Infinity engine changed or exited during diagnostic read')
            started = time.monotonic()
            try:
                result = subprocess.run(['adb', 'shell', 'dumpsys', '-t', '30', service],
                                        capture_output=True, text=True, timeout=40)
                stdout, stderr, code = result.stdout, result.stderr, result.returncode
            except subprocess.TimeoutExpired as exc:
                def decoded(value):
                    return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                stdout, stderr, code = decoded(exc.stdout), decoded(exc.stderr), None
            stem = name + '-' + service + '-attempt-' + str(attempt)
            (out / (stem + '-stdout.txt')).write_text(stdout)
            (out / (stem + '-stderr.txt')).write_text(stderr)
            valid = (code == 0 and 'DUMP TIMEOUT' not in stdout and
                     ('Input Dispatcher State:' in stdout if service == 'input'
                      else 'WINDOW MANAGER' in stdout))
            report.setdefault('diagnostic_reads', []).append(dict(
                name=name, service=service, attempt=attempt, returncode=code,
                seconds=round(time.monotonic()-started, 3), complete=valid))
            if valid:
                return stdout
            print('INFINITY diagnostic read incomplete:', stem, 'returncode', code, flush=True)
        require(False, 'required ' + service + ' dump unavailable after two recorded read attempts')

    def capture(name, state=None):
        png = probe.adb('exec-out', 'screencap', '-p', binary=True)
        require(png.startswith(b'\x89PNG\r\n\x1a\n'), 'No actual Android screenshot')
        (out / (name + '.png')).write_bytes(png)
        # Save the observed app state before secondary OS diagnostics so a
        # diagnostic collection failure cannot discard that gesture's result.
        row = dict(name=name, state=state or observe(), physical_size=struct.unpack('>II', png[16:24]))
        records.append(row); save()
        # Retain OS input ownership before/after gestures, not only at failure.
        # This distinguishes app selection changes from nav_input_consumer.
        (out / (name + '-windows.txt')).write_text(diagnostic_dump(name, 'window'))
        (out / (name + '-input.txt')).write_text(diagnostic_dump(name, 'input'))
        print('INFINITY UI OBSERVATION:', name, flush=True)
        return row
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
        if popup(state):
            backdrop=state['controls']['2']
            require([backdrop['width'],backdrop['height']]==[vw,vh],
                    'observer viewport differs from the actual popup backdrop')
        return round(x * width / vw), round(y * height / vh)
    def tap(state, xy, hold=False):
        x, y = point(state, *xy)
        # Run39124920134's Pixel Launcher ANR owned input. The first intended
        # Favourites tap actually hit its Close app button, leaving only one
        # app tap. Never dispatch through another app/system dialog or replay
        # that gesture. Preserve evidence and fail at its actual boundary.
        windows = diagnostic_dump('gesture-' + str(len(report.setdefault('gestures', []))), 'window')
        focus = re.search(r'(?m)^\s*mCurrentFocus=(.+)$', windows)
        current = focus.group(1) if focus else ''
        report['gestures'].append(dict(point=[x, y], hold=hold, focus=current))
        if ' ' + probe.PACKAGE + '/' not in current:
            capture('foreign-input-owner', state)
        require(' ' + probe.PACKAGE + '/' in current,
                'Android input is owned by another window: ' + current)
        if hold: probe.shell('input', 'swipe', x, y, x, y, 1100)
        else: probe.shell('input', 'tap', x, y)
        time.sleep(.6)
    def token(state, ident=50):
        return state['labels'].get('Container(' + str(ident) + ').ListItem.Property(Infinity.UI.Token)', '')
    def popup(state): return state.get('popup') == '1'
    def menu_ready(state):
        # onInit publishes Popup before adding rows. Its final SetFocusId(50)
        # follows every addItem, so wait for that actual completion boundary.
        return popup(state) and state.get('focus') == 50
    def rowpoint(state, label):
        card, listing = state['controls']['100'], state['controls']['50']
        surface = state['controls']['101']
        vw,vh=state['viewport'];left,top=card['position']
        require(left>=0 and top>=0 and left+card['width']<=vw and top+card['height']<=vh,
                'popup card is clipped by the active window')
        require(surface['height']+2*surface['position'][1]==card['height'] and
                surface['width']+2*surface['position'][0]==card['width'],
                'popup visible surface extends beyond compact card')
        require(listing['position'][1]+listing['height'] <= card['height'],
                'popup native hit rectangle extends outside compact card')
        labels = [x['label'] for x in listing['items']]
        require(label in labels, 'Missing row ' + label + ': ' + repr(labels))
        index = labels.index(label)
        return (card['position'][0] + listing['position'][0] + 120,
                card['position'][1] + listing['position'][1] + index * 78 + 35)
    def invoke(state, label):
        xy = rowpoint(state, label)
        tap(state, xy)
        focused = observe()
        capture('action-' + str(len(records)) + '-focused', focused)
        require(popup(focused), 'Focusing a popup row performed its action')
        require(focused['labels'].get('Container(50).ListItem.Label') == label,
                'First popup tap did not select the intended row: ' + label)
        tap(focused, xy)
    def restore_button(state):
        button, grid = state['controls']['13'], state['controls']['50']
        require(button['visible'] and button['position'][1] >= 120 and
                button['position'][1] + button['height'] < grid['position'][1],
                'Restore control overlaps content or Android navigation')
        tap(state, (button['position'][0] + button['width']/2,
                    button['position'][1] + button['height']/2))
    def back():
        probe.rpc('Input.Back'); time.sleep(.6)
    def browse():
        observe('browse')
        def ready(state):
            # DirectoryProvider can publish between the observer's control and
            # label reads. API 35 evidence showed an empty earlier vector with
            # NumItems=13 later in the SAME snapshot. Require both views to be
            # populated and agree; never proceed with vacuous all([]) checks.
            grid = state.get('controls', {}).get('50', {})
            items = grid.get('items', [])
            count = int(state['labels'].get('Container(50).NumItems') or 0)
            return (state['window'] == 11193 and state['dialog'] in (0, 9999) and
                    state.get('focus') == 50 and count >= 12 and
                    grid.get('size') == count == len(items) and
                    all(row.get('kind') == 'addon' and row.get('token') for row in items) and
                    token(state) in {row['token'] for row in items})
        return wait_for(ready, 'consistent complete Video Sources grid')
    def provider_ready(state, addon):
        # Window activation precedes the asynchronous directory load. Back
        # while dialog 10138 is active cancels that load and is a different
        # operation from returning from the successfully opened add-on.
        return (state['window'] == 10025 and state['dialog'] in (0, 9999) and
                state['labels'].get('Container.FolderPath', '').startswith('plugin://' + addon + '/') and
                any(row.get('label') == 'Infinity UI public movie'
                    for row in state['controls'].get('50', {}).get('items', [])))

    def acknowledge_system_tutorial():
        # API35 evidence contains Android's first-use fullscreen coachmark,
        # not an Infinity dialog. Acknowledge the observed system button before
        # app gestures; do not prime/retry app taps or change navigation policy.
        def visible_tutorial(windows):
            return any('ImmersiveModeConfirmation}:' in block and
                       'mOwnerUid=1000 ' in block and 'package=android ' in block and
                       'isVisible=true' in block
                       for block in re.split(r'(?m)^  Window #', windows))
        windows = probe.shell('dumpsys', 'window')
        if not visible_tutorial(windows):
            return
        (out / 'android-fullscreen-tutorial-before-windows.txt').write_text(windows)
        (out / 'android-fullscreen-tutorial-before.png').write_bytes(
            probe.adb('exec-out', 'screencap', '-p', binary=True))
        path = '/data/local/tmp/infinity-system-tutorial.xml'
        probe.shell('uiautomator', 'dump', path)
        xml = probe.shell('cat', path)
        (out / 'android-fullscreen-tutorial.xml').write_text(xml)
        nodes = [n for n in ET.fromstring(xml).iter('node')
                 if n.get('text') == 'Got it' and
                 n.get('package') in ('android', 'com.android.systemui') and
                 n.get('class') == 'android.widget.Button' and
                 n.get('clickable') == 'true' and n.get('enabled') == 'true']
        require(len(nodes) == 1, 'cannot identify Android fullscreen tutorial button')
        bounds = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', nodes[0].get('bounds', ''))
        require(bounds is not None, 'Android tutorial button has no observed bounds')
        x1, y1, x2, y2 = map(int, bounds.groups())
        require(x2 > x1 and y2 > y1, 'Android tutorial button is not visible')
        probe.shell('input', 'tap', (x1+x2)//2, (y1+y2)//2)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            windows = probe.shell('dumpsys', 'window')
            if not visible_tutorial(windows): break
            time.sleep(.25)
        require(not visible_tutorial(windows), 'Android fullscreen tutorial did not dismiss')
        (out / 'android-fullscreen-tutorial-after-windows.txt').write_text(windows)
        report['android_system_onboarding'] = dict(
            window='ImmersiveModeConfirmation', button='Got it',
            bounds=list(map(int, bounds.groups())), dismissed=True)
        print('INFINITY UI: acknowledged observed Android fullscreen tutorial', flush=True)

    # This is an isolated emulator media fixture, never user playback content.
    boot_id = probe.shell('cat', '/proc/sys/kernel/random/boot_id').strip()
    require(bool(boot_id), 'Android boot identity unavailable')
    report['android_boot_id'] = boot_id
    movie = Path('infinity-ui-fixture.mp4')
    require(movie.is_file(), 'generated sample missing')
    require(probe.shell('getprop','ro.kernel.qemu').strip()=='1' and
            str(probe.APP_UID).isdigit(), 'media staging requires the verified disposable emulator')
    probe.adb('push', movie, probe.PROFILE + '/' + movie.name)
    backing='/data/media/0/Android/data/'+probe.PACKAGE+'/files/.kodi/userdata/'+movie.name
    media_proof=dict(before=probe.shell('ls','-lZ',backing))
    # Match the original approved probe's fixture ownership/label restoration.
    # Root adbd gives this late-copied clip storage_file, denied to the app.
    # Restore only this disposable file; never change policy or enforcement.
    probe.shell('chown',str(probe.APP_UID)+':'+str(probe.APP_UID),backing)
    probe.shell('chmod','644',backing)
    probe.shell('restorecon','-F',backing)
    media_proof.update(after=probe.shell('ls','-lZ',backing),
                       selinux=probe.shell('getenforce').strip())
    require(media_proof['selinux']=='Enforcing','SELinux policy was weakened')
    seeded=observe('seed');media_proof['app_vfs']=seeded.get('sample')
    report['media_preflight']=media_proof
    (out/'MEDIA-PREFLIGHT.json').write_text(json.dumps(media_proof,indent=2))
    require(seeded.get('sample',{}).get('exists') is True,
            'generated clip is not visible to the actual app after platform label restoration')
    def grid_matrix():
        for viewport, size in (('cover', '1080x2400'), ('inner', '1800x1440')):
            probe.shell('wm', 'size', size); probe.shell('wm', 'density', '320'); time.sleep(3)
            for theme in ('light', 'dark', 'OLED'):
                observe('theme', theme)
                state = browse()
                capture(viewport + '-' + theme.lower() + '-grid-before-tap',state)
                grid = state['controls']['50']
                require(all(item.get('kind')=='addon' and item.get('token')
                            for item in grid.get('items',[])), 'grid contains raw or duplicate non-opt-in provider items')
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
                    capture(viewport + '-' + theme.lower() + '-' + side + '-first-tap', first)
                    tap(first, xy, hold=True)
                    menu = wait_for(menu_ready, 'item-specific add-on menu')
                    require(menu['title'].startswith('Add-on Options — '), 'wrong popup')
                    labels = [x['label'] for x in menu['controls']['50']['items']]
                    required = ['Open','Add-on Information','Add-on Settings','Add to Favourites',
                                'Add to Infinity Rails','Hide from This View','More / Manage Add-on']
                    mandatory = ['Open','Add-on Information','Add to Favourites']
                    if not selected.startswith(('script.infinity.', 'service.infinity.', 'skin.infinity.')):
                        mandatory += ['Hide from This View','More / Manage Add-on']
                    require(labels == [x for x in required if x in labels] and all(x in labels for x in mandatory),
                            'menu ordering/capabilities wrong for '+selected+': '+repr(labels))
                    capture(viewport + '-' + theme.lower() + '-' + side + '-menu', menu)
                    tap(menu, rowpoint(menu, 'Open'))
                    require(popup(observe()), 'Selecting Open did not keep the popup open')
                    back()
                    restored = observe()
                    capture(viewport + '-' + theme.lower() + '-' + side + '-dismissed', restored)
                    require(restored['window'] == 11193 and token(restored) == selected and
                            restored['labels'].get('Container(50).CurrentPage') == first['labels'].get('Container(50).CurrentPage'),
                            'dismissal changed selection or scroll: ' + json.dumps(dict(
                                expected_token=selected, actual_token=token(restored),
                                expected_page=first['labels'].get('Container(50).CurrentPage'),
                                actual_page=restored['labels'].get('Container(50).CurrentPage'))))
                    # The original first tap is still armed after harmless dismissal.
                    tap(restored, xy)
                    opened = wait_for(lambda s: provider_ready(s, selected),
                                      'second-tap completed correct add-on listing')
                    capture(viewport + '-' + theme.lower() + '-' + side + '-opened', opened)
                    back(); state = wait_for(lambda s: s['window'] == 11193, 'return to exact grid')
                # Scroll through the real native panel; hold must follow the new item.
                x, y = point(state, grid['position'][0] + grid['width'] * .75, grid['position'][1] + grid['height'] * .8)
                endx, endy = point(state, grid['position'][0] + grid['width'] * .75, grid['position'][1] + grid['height'] * .3)
                probe.shell('input','swipe',x,y,endx,endy,500); time.sleep(1)
                xy = (grid['position'][0] + (columns - .5) * item_width, grid['position'][1] + item_height * .5)
                tap(state, xy); scrolled = observe()
                capture(viewport+'-'+theme.lower()+'-scrolled-selected', scrolled)
                tap(scrolled, xy, hold=True)
                menu = wait_for(menu_ready, 'scrolled item menu'); capture(viewport+'-'+theme.lower()+'-scrolled', menu)
                back(); restored = observe()
                require(token(restored) == token(scrolled), 'scrolled popup dismissed to wrong item')
                capture(viewport+'-'+theme.lower()+'-scrolled-dismissed', restored)
                require(restored['labels'].get('Container(50).CurrentPage') ==
                        scrolled['labels'].get('Container(50).CurrentPage'),
                        'scrolled popup dismissal changed page')

    # Run the remaining state/Home/Stop gates first. The exact prior package
    # already passed the full grid matrix; retain and rerun that entire matrix
    # below, after these actions, rather than delaying feedback on new paths.
    probe.shell('wm', 'size', '1800x1440'); probe.shell('wm', 'density', '320'); time.sleep(3)
    observe('theme', 'OLED')
    state=browse(); acknowledge_system_tutorial()
    state=observe(); capture('actions-grid-before-tap', state); grid=state['controls']['50']
    item_height=grid['height']*.21809829; item_width=item_height*.668085106
    columns=int(grid['width']//item_width)
    index=next(i for i,r in enumerate(grid['items']) if r.get('token','').startswith('plugin.video.infinityuitest'))
    xy=(grid['position'][0]+(index%columns+.5)*item_width,
        grid['position'][1]+(index//columns+.5)*item_height)
    tap(state,xy); restored=observe()
    require(restored['window']==11193 and not popup(restored), 'fixture first tap launched')
    capture('actions-fixture-selected',restored)

    # Exercise actual view-local hiding and restoration without disabling.
    selected = token(restored)
    require(selected.startswith('plugin.video.infinityuitest'), 'mutation requires a harmless fixture')
    probe.rpc('Input.ContextMenu')
    menu = wait_for(menu_ready, 'fixture context through native D-pad route')
    invoke(menu, 'Add to Favourites')
    wait_for(lambda s:not popup(s) and s['dialog'] in (0,9999), 'favourite action completed without an error dialog')
    favourites = probe.rpc('Favourites.GetFavourites', dict(properties=['windowparameter']))
    require(any(f.get('windowparameter') == 'plugin://'+selected+'/' for f in (favourites.get('favourites') or [])),
            'favourite destination not saved')
    report['ui_expected_favourite'] = 'plugin://'+selected+'/'
    probe.rpc('Input.ContextMenu'); menu=wait_for(menu_ready,'hide menu')
    invoke(menu,'Hide from This View')
    hidden_state=wait_for(lambda s:not popup(s) and all(r.get('token') != selected for r in s['controls']['50'].get('items',[])),
             'hidden tile removed only from grid')
    require(probe.rpc('Addons.GetAddonDetails',dict(addonid=selected,properties=['enabled']))['addon']['enabled'],
            'Hide disabled the add-on')
    restore_button(hidden_state); restore=wait_for(menu_ready,'hidden tile recovery through visible control')
    card=restore['controls']['100']
    tap(restore,(card['position'][0]+card['width']/2,card['position'][1]+card['height']+40))
    dismissed=wait_for(lambda s:not popup(s),'outside dismissal of compact restore menu')
    require(all(r.get('token') != selected for r in dismissed['controls']['50'].get('items',[])),
            'outside dismissal activated Restore')
    restore_button(dismissed); restore=wait_for(menu_ready,'reopened hidden tile recovery through visible control')
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
        menu = wait_for(menu_ready, 'original Resume context for ' + media)
        labels = [x['label'] for x in menu['controls']['50']['items']]
        require(labels == ['Mark Watched','Reset Progress','Add to Watchlist','Add to Collection','Rate',
                           'Add to Custom List','Remove from Continue Playing'], 'Resume actions not original item menu')
        capture('continue-'+media+'-context', menu)
        tap(menu, rowpoint(menu, 'Mark Watched'))
        require(popup(observe()), 'Mark Watched ran on focus')
        back()
        dismissed=observe()
        require(dismissed['window']==10000 and token(dismissed,ident)==token(home,ident) and
                dismissed['labels'].get('Container('+str(ident)+').CurrentPage')==
                    home['labels'].get('Container('+str(ident)+').CurrentPage'),
                'Resume dismissal changed Home, selected item or rail scroll')
        # Cross the real helper -> original controller writer boundary, then
        # verify the same movie/episode memberships after actual process restart.
        key=token(home,ident)
        require(len(key)==64,'Continue identity unavailable')
        tap(observe(),xy,hold=True)
        menu=wait_for(menu_ready,'Watchlist mutation for '+media)
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
        wait_for(lambda s:provider_ready(s,'plugin.video.infinityuitest0'), 'completed provider movie choices')
        selected_choice=observe('focus-choice')
        require(selected_choice['labels'].get('Container(50).ListItem.Label')=='Infinity UI public movie',
                'provider choice did not receive native focus')
        # Use the actual provider item and setResolvedUrl path, not a raw
        # host-side /sdcard alias passed to Player.Open.
        probe.rpc('Input.Select')
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
        probe.rpc('Player.Stop', dict(playerid=player))
        choices=wait_for(lambda s:s['window']==10025 and s['dialog'] in (0,9999) and
                        not any(p.get('type')=='video' for p in probe.rpc('Player.GetActivePlayers')),
                        'completed Stop and restored movie choices')
        if path=='B':
            observe('home','movies')
            require(observe()['window']==10000, 'Stop then Home did not return Home')
        time.sleep(5)
        require(probe.rpc('JSONRPC.Ping')=='pong', 'engine unavailable after Stop path '+path)
        require(any(p['pid']==report['native_owner']['pid'] for p in probe.processes()), 'native process changed after Stop')
        capture('stop-path-'+path)
    grid_matrix()
    report['ui_emulator_smoke_passed'] = True
    (out/'UI-INTERACTIONS.json').write_text(json.dumps(dict(records=records, passed=True,
        physical_fold_verified=False, crash_fixed=False, actual_signed_apk_sha256=report['apk_sha256']),indent=2))
