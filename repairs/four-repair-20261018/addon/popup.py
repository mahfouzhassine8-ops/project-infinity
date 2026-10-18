"""An item-specific Infinity popup. Native input owns select-then-activate touch."""
from pathlib import Path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

def position(view_width, view_height, width, height, anchor=None):
    """Keep the compact card adjacent to the chosen point and inside the view."""
    margin = 18
    if anchor is None:
        return (max(margin, (view_width - width) // 2),
                max(margin, (view_height - height) // 2))
    x, y = anchor
    left = x + 18 if x + 18 + width <= view_width - margin else x - width - 18
    top = y + 18 if y + 18 + height <= view_height - margin else y - height - 18
    return (round(max(margin, min(left, view_width - width - margin))),
            round(max(margin, min(top, view_height - height - margin))))

def choose(title, rows):
    if not rows:
        return None
    parent = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    anchor = None
    try:
        if parent.getProperty('Infinity.UI.Anchor.Token'):
            anchor = (float(parent.getProperty('Infinity.UI.Anchor.X')),
                      float(parent.getProperty('Infinity.UI.Anchor.Y')))
    except (ValueError, TypeError):
        pass
    finally:
        for key in ('X', 'Y', 'Token'):
            parent.clearProperty('Infinity.UI.Anchor.' + key)
    class ItemOptions(xbmcgui.WindowXMLDialog):
        result = None
        ready = False
        def onInit(self):
            self.setProperty('Infinity.UI.Popup', '1')
            self.setProperty('Infinity.UI.Title', title)
            backdrop, card = self.getControl(2), self.getControl(100)
            # Use the live native viewport, not Android display dimensions or
            # cached portrait pixels. Reopening after a fold remeasures it.
            card.setHeight(min(690, 118 + 78 * len(rows)))
            card.setPosition(*position(backdrop.getWidth(), backdrop.getHeight(),
                                       card.getWidth(), card.getHeight(), anchor))
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
