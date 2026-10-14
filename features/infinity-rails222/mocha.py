"""On-demand Infinity Rail Options WindowXMLDialog (no background services).

The active Infinity skin owns the visual XML; this helper only supplies the
selected add-on identity, supported actions and safe close/choice handling.
Fallback to Kodi's ordinary Dialog.select if the custom XML fails to load.
"""


def rail_options(row, section, has_settings, helper_path):
    import xbmc
    import xbmcgui
    import xbmcaddon
    import xbmcvfs
    from pathlib import Path

    actions = [('Open Add-on', 'open'), ('Move / Reorder', 'move')]
    if row.get('custom'):
        actions.append(('Remove from ' + ('TV Show Add-ons' if section == 'tvshows' else 'Movie Add-ons'), 'remove'))
    if has_settings:
        actions.append(('Add-on Settings', 'settings'))
    actions.append(('Cancel', 'cancel'))
    allowed = {action for _, action in actions}

    class RailOptionsDialog(xbmcgui.WindowXMLDialog):
        def onInit(self):
            self.setProperty('Infinity.Rails.Menu.Title', str(row.get('label', 'Add-on')))
            self.setProperty('Infinity.Rails.Menu.Subtitle',
                             'TV Show Add-ons' if section == 'tvshows' else 'Movie Add-ons')
            self.setProperty('Infinity.Rails.Menu.Thumb',
                             str(row.get('thumb') or row.get('icon') or 'DefaultAddon.png'))
            self.setProperty('Infinity.Rails.Menu.Remove', 'true' if row.get('custom') else 'false')
            self.setProperty('Infinity.Rails.Menu.RemoveLabel',
                             'Remove from TV Show Add-ons' if section == 'tvshows' else 'Remove from Movie Add-ons')
            self.setProperty('Infinity.Rails.Menu.Settings', 'true' if has_settings else 'false')
            try:
                self.setFocusId(91002)
            except (RuntimeError, TypeError):
                pass

        def onClick(self, control_id):
            command = {91001: 'open', 91002: 'move', 91003: 'remove',
                       91004: 'settings', 91005: 'cancel', 91006: 'cancel'}.get(control_id)
            if command not in allowed:
                return
            self.result = command
            self.close()

        def onAction(self, action):
            if action.getId() in (10, 92, 110, 117):
                self.result = 'cancel'
                self.close()

    window = None
    try:
        skin = xbmcaddon.Addon('skin.infinity.diggz')
        version = tuple(int(v) for v in skin.getAddonInfo('version').split('.'))
        base = Path(xbmcvfs.translatePath(skin.getAddonInfo('path')))
        if version < (1, 0, 5, 222) or not (base / 'unified' / 'InfinityRailsOptions.xml').is_file():
            raise FileNotFoundError('Mocha Rail Options profile not installed')
        window = RailOptionsDialog('InfinityRailsOptions.xml', str(helper_path), 'Default', '720p')
        window.result = 'cancel'
        window.doModal()
        result = window.result
        return result if result in allowed else 'cancel'
    except Exception as exc:
        xbmc.log('Infinity Rails: custom options dialog unavailable, Kodi chooser fallback: '
                 + str(exc), xbmc.LOGWARNING)
        chosen = xbmcgui.Dialog().select('INFINITY / RAIL OPTIONS — ' + str(row.get('label', 'Add-on')),
                                          [label for label, _ in actions])
        if chosen is None or not 0 <= chosen < len(actions):
            return 'cancel'
        return actions[chosen][1]
    finally:
        if window is not None:
            try:
                window.close()
            except Exception:
                pass
            del window
