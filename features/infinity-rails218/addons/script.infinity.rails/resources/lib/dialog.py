"""One modal, on-demand skin-owned chooser. No worker, timer or refresh loop."""
def choose(title, labels, subtitle=''):
    import xbmcgui
    import xbmcaddon
    import xbmcvfs

    class RailChooser(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.choice = -1

        def onInit(self):
            self.setProperty('Infinity.Rails.Title', title)
            self.setProperty('Infinity.Rails.Subtitle', subtitle)
            control = self.getControl(6)
            control.reset()
            control.addItems([xbmcgui.ListItem(label=label) for label in labels])
            self.setFocusId(6)

        def onClick(self, control_id):
            if control_id == 6:
                position = self.getControl(6).getSelectedPosition()
                if 0 <= position < len(labels):
                    self.choice = position
                self.close()
            elif control_id == 7:
                self.close()

        def onAction(self, action):
            # Previous Menu, Parent Directory, Nav Back and context/menu dismiss.
            if action.getId() in (9, 10, 92, 117):
                self.close()

    root = xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.rails').getAddonInfo('path'))
    window = RailChooser('script-infinity-rails-select.xml', root, 'Default', '1080i')
    try:
        window.doModal()
        return window.choice
    finally:
        window.close()
        del window
