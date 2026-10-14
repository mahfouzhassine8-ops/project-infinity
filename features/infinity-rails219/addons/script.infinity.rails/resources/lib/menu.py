"""A bounded, content-sized Rails dialog. No timer, listener, worker or polling."""
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class Geometry:
    x: int
    y: int
    width: int
    height: int
    list_height: int


def geometry(width, height, count):
    # Use Kodi's actual window coordinate dimensions. The active Infinity
    # renderer uses a 1080-unit short axis, independent of physical screen size.
    # Quantized XML shapes keep native in-place reflow authoritative: Python
    # must not override controls whose XML specs the renderer will reapply.
    width, height = int(width), int(height)
    if width < 220 or height < 252:
        return None
    w = max(v for v in (192, 320, 480, 720, 900) if v <= width * .92)
    rows = min(8, max(1, count), max(1, int((height * .9 - 144) // 82)))
    list_height = rows * 82
    h = 144 + list_height
    return Geometry((width-w)//2, (height-h)//2, w, h, list_height)


def choose(gui, title, options, subtitle='', root=None):
    import xbmc
    import xbmcaddon
    import xbmcvfs
    if root is None:
        root = xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.rails').getAddonInfo('path'))

    class RailsDialog(gui.WindowXMLDialog):
        result = -1
        viewport = None

        def onInit(self):
            try:
                self.viewport = (self.getWidth(), self.getHeight())
                box = geometry(*self.viewport, len(options))
                if box is None:
                    self.close()
                    return
                self.setProperty('Infinity.Rails.Title', title)
                self.setProperty('Infinity.Rails.Subtitle', subtitle)
                if self.shape != '%dx%d' % (box.width, box.list_height // 82):
                    self.close()
                    return
                listing = self.getControl(6)
                listing.reset()
                listing.addItems([gui.ListItem(label=text) for text in options])
                listing.selectItem(0)
                self.setFocusId(6)
                xbmc.log('Infinity Rails: menu ready %.1f ms; %dx%d coordinates' %
                         ((time.monotonic()-started)*1000, *self.viewport), xbmc.LOGDEBUG)
            except Exception as exc:
                xbmc.log('Infinity Rails: dialog initialization failed: '+str(exc), xbmc.LOGERROR)
                self.close()

        def onAction(self, action):
            # On reconfiguration Kodi can reload XML (onInit reflows). If a
            # viewport changes without that callback, dismiss on next input;
            # no operation is saved until a choice is accepted.
            if self.viewport != (self.getWidth(), self.getHeight()) or action.getId() in (9, 10, 92, 117):
                self.result = -1
                self.close()

        def onClick(self, control_id):
            if self.viewport != (self.getWidth(), self.getHeight()):
                self.result = -1
                self.close()
            elif control_id == 2:
                self.result = -1
                self.close()
            elif control_id == 6:
                self.result = self.getControl(6).getSelectedPosition()
                self.close()

    started = time.monotonic()
    dialog = RailsDialog('InfinityRailsOptions.xml', str(root), 'Default', '1080i')
    home = gui.Window(10000)
    key = 'Infinity.Rails.DialogShape'
    previous_shape = home.getProperty(key)
    box = geometry(dialog.getWidth(), dialog.getHeight(), len(options))
    if box is None:
        dialog.close()
        del dialog
        return -1
    dialog.shape = '%dx%d' % (box.width, box.list_height // 82)
    home.setProperty(key, dialog.shape)
    try:
        dialog.doModal()
        result = dialog.result
    finally:
        dialog.close()
        if previous_shape:
            home.setProperty(key, previous_shape)
        else:
            home.clearProperty(key)
        del dialog
    xbmc.log('Infinity Rails: menu session %.1f ms (includes user dwell)' %
             ((time.monotonic()-started)*1000), xbmc.LOGDEBUG)
    return result
