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

def fit_popup(view_width, view_height, row_count, anchor=None):
    """Fit the existing 760-unit card; preserve row geometry and native hit mapping."""
    view_width, view_height = max(1, view_width), max(1, view_height)
    margin = min(18.0, view_width / 8, view_height / 8)
    available_w, available_h = view_width - 2 * margin, view_height - 2 * margin
    width = 760
    # Keep one complete row in very small popup windows. Short normal windows
    # scroll the list rather than shrinking every row to fit all menu entries.
    scale = min(1.0, available_w / width, available_h / 196.0)
    height = min(690, 118 + 78 * max(1, row_count), int(available_h / scale))
    visible_w, visible_h = width * scale, height * scale
    if anchor is None:
        left, top = (view_width - visible_w) / 2, (view_height - visible_h) / 2
    else:
        x, y = anchor
        left = x + margin if x + margin + visible_w <= view_width - margin else x - visible_w - margin
        top = y + margin if y + margin + visible_h <= view_height - margin else y - visible_h - margin
        left = max(margin, min(left, view_width - visible_w - margin))
        top = max(margin, min(top, view_height - visible_h - margin))
    return dict(left=round(left), top=round(top), width=width, height=height,
                scale=scale, rows_height=max(1, height - 116))


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
        def reflow(self):
            backdrop, card = self.getControl(190), self.getControl(100)
            bounds = fit_popup(backdrop.getWidth(), backdrop.getHeight(), len(rows), anchor)
            card.setHeight(bounds['height'])
            surface = self.getControl(101)
            surface.setHeight(bounds['height'] - 2 * surface.getPosition()[1])
            card.setPosition(bounds['left'], bounds['top'])
            percent = bounds['scale'] * 100
            card.setAnimations([('conditional',
                'effect=zoom start=%s,%s end=%s,%s center=%s,%s time=0 condition=true' %
                (percent, percent, percent, percent, bounds['left'], bounds['top']))])
            self.getControl(50).setHeight(bounds['rows_height'])

        def onInit(self):
            if self.ready:
                # Exact owned resize callback: keep the selected row and scroll.
                self.reflow()
                return
            self.setProperty('Infinity.UI.Popup', '1')
            self.setProperty('Infinity.UI.Title', title)
            self.reflow()
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
            elif control_id in (190, 9):
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
