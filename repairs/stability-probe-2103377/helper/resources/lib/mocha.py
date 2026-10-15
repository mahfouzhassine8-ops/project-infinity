"""On-demand Infinity Mocha Rail Options dialog with Kodi-owned fallback.

No background service, writes, settings mutation, native hooks or keymaps.
"""

def rail_options(row, section, has_settings, helper_path):
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
    from pathlib import Path

    actions = [('Open Add-on','open'),('Move / Reorder','move')]
    if row.get('custom'):
        actions.append(('Remove from '+('TV Show Add-ons' if section=='tvshows' else 'Movie Add-ons'),'remove'))
    if has_settings:
        actions.append(('Add-on Settings','settings'))
    actions.append(('Cancel','cancel'))
    permitted={v for _,v in actions}

    class OptionsWindow(xbmcgui.WindowXMLDialog):
        result='cancel'
        ready=False
        def onInit(self):
            self.setProperty('Infinity.Rails.Menu.Title',str(row.get('label','Add-on')))
            self.setProperty('Infinity.Rails.Menu.Subtitle',
                             'TV Show Add-ons' if section=='tvshows' else 'Movie Add-ons')
            self.setProperty('Infinity.Rails.Menu.Thumb',str(row.get('thumb') or row.get('icon') or 'DefaultAddonVideo.png'))
            self.setProperty('Infinity.Rails.Menu.Remove','true' if row.get('custom') else 'false')
            self.setProperty('Infinity.Rails.Menu.RemoveLabel','Remove from '+
                             ('TV Show Add-ons' if section=='tvshows' else 'Movie Add-ons'))
            self.setProperty('Infinity.Rails.Menu.Settings','true' if has_settings else 'false')
            self.getControl(91001)  # guard: actual custom XML controls must exist
            self.getControl(91002)
            self.getControl(91005)
            self.ready=True
            self.setFocusId(91002)
        def onClick(self,control_id):
            command={91001:'open',91002:'move',91003:'remove',91004:'settings',91005:'cancel',91006:'cancel'}.get(control_id)
            if command in permitted:
                self.result=command
                self.close()
        def onAction(self,action):
            if action.getId() in (10,92,110,117):
                self.result='cancel'
                self.close()

    window=None
    try:
        skin=xbmcaddon.Addon('skin.infinity.diggz')
        version=tuple(int(p) for p in skin.getAddonInfo('version').split('.'))
        base=Path(xbmcvfs.translatePath(skin.getAddonInfo('path')))
        if version < (1,0,5,222) or not (base/'unified'/'InfinityRailsOptions.xml').is_file():
            raise RuntimeError('Mocha skin 1.0.5.222 is not installed')
        window=OptionsWindow('InfinityRailsOptions.xml',str(helper_path),'Default','720p')
        window.doModal()
        if not window.ready:
            raise RuntimeError('Mocha options window could not initialise its controls')
        return window.result if window.result in permitted else 'cancel'
    except Exception as exc:
        xbmc.log('Infinity Rails Mocha: custom dialog unavailable; safe chooser fallback: '+str(exc),xbmc.LOGWARNING)
        picked=xbmcgui.Dialog().select('INFINITY / RAIL OPTIONS — '+str(row.get('label','Add-on')),
                                        [label for label,_ in actions])
        if picked is None or not isinstance(picked,int) or not (0<=picked<len(actions)):
            return 'cancel'
        return actions[picked][1]
    finally:
        if window is not None:
            try:window.close()
            except Exception:pass
            del window
