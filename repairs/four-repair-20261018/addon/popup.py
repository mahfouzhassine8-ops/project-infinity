"""An item-specific Infinity popup. Native input owns select-then-activate touch."""
from pathlib import Path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

def choose(title, rows):
    if not rows:
        return None
    class ItemOptions(xbmcgui.WindowXMLDialog):
        result = None
        ready = False
        def onInit(self):
            self.setProperty('Infinity.UI.Popup', '1')
            self.setProperty('Infinity.UI.Title', title)
            control = self.getControl(50)
            control.reset()
            for index, (label, _) in enumerate(rows):
                item = xbmcgui.ListItem(label=label)
                item.setProperty('Infinity.UI.Version', '1')
                item.setProperty('Infinity.UI.Kind', 'action')
                item.setProperty('Infinity.UI.Token', str(index))
                control.addItem(item)
            self.setFocusId(50)
            self.ready = True
        def onClick(self, control_id):
            if control_id == 50:
                selected = self.getControl(50).getSelectedPosition()
                if 0 <= selected < len(rows):
                    self.result = rows[selected][1]
                    self.close()
            elif control_id in (2, 9):
                self.close()
        def onAction(self, action):
            if action.getId() in (10, 92, 110):
                self.close()
    root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))
    win = ItemOptions('InfinityItemOptions.xml', str(root), 'Default', '1080i')
    try:
        win.doModal()
        if not win.ready:
            raise RuntimeError('The Infinity item menu could not load. No action was performed.')
        return win.result
    finally:
        win.close()
        del win
