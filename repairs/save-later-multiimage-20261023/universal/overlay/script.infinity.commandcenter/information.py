# SPDX-License-Identifier: GPL-2.0-or-later
"""Infinity's explicit Information action; no generic Kodi/Cobra interception.

The popup supplies the exact verified selected entry and ListItem. This page
only displays that snapshot and returns an explicit action to the same owner.
It neither discovers providers nor writes progress, lists or provider memory.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from title_metadata import from_entry, trailer_route


CANCEL_ACTIONS = (10, 92, 110)


def duration_text(seconds):
    """Use actual seconds, including the original seconds after full minutes."""
    if type(seconds) is not int or seconds <= 0:
        return ''
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return '%d:%02d:%02d' % (hours, minutes, seconds) if hours else '%d:%02d' % (minutes, seconds)


def presentation(entry):
    """Original available facts only. Plot has no strip, slice or line limit."""
    data = from_entry(entry)
    title = entry.get('title') or entry.get('label') or ''
    poster = entry.get('poster') or ''
    synopsis = data.get('plot', '')
    meta = '  •  '.join(str(value) for value in (
        data.get('year'), duration_text(data.get('duration')), data.get('mpaa')) if value)
    fields = []
    for label, field in (('Genre', 'genre'), ('Director', 'director'),
                         ('Writer', 'writer'), ('Studio', 'studio'),
                         ('Country', 'country'), ('Release', 'premiered'),
                         ('Rating', 'rating'), ('Cast', 'cast')):
        value = data.get(field)
        if isinstance(value, (list, tuple)):
            value = ' • '.join(value)
        if value:
            fields.append(label + ': ' + str(value))
    return dict(title=title if isinstance(title, str) else '',
                poster=poster if isinstance(poster, str) else '',
                synopsis=synopsis, metadata=meta, details='\n\n'.join(fields),
                trailer=trailer_route(data.get('trailer')))


def geometry(width, height, physical_width='', physical_height='', details=True):
    """Measure in horizontal physical units before mapping to Kodi's viewport.

    This prevents a 16:9 XML coordinate system from stretching a poster or
    collapsing nested percentage buttons on a tall Fold display. Textboxes
    keep their complete text and independently page vertically.
    """
    width, height = max(1, int(width)), max(1, int(height))
    try:
        pw, ph = int(physical_width), int(physical_height)
        if min(pw, ph) < 100:
            raise ValueError()
    except (TypeError, ValueError):
        pw, ph = width, height
    ratio = height * pw / (width * ph)
    screen_h = height / ratio
    scale = width / 1080.0
    card_w, available_h = width * .94, screen_h * .94
    pad = min(26 * scale, available_h * .035)
    gap = min(20 * scale, available_h * .022)
    header_h = min(66 * scale, available_h * .09)
    button_h = min(76 * scale, available_h * .13)
    details_h = min(210 * scale, available_h * .14) if details else 0
    details_title_h = min(46 * scale, available_h * .07) if details else 0
    # Reserve the entire action and details area before sizing the synopsis.
    reserve = 2 * pad + header_h + 4 * gap + button_h + details_h + details_title_h
    summary_h = min(650 * scale, max(1, available_h - reserve))
    title_h = min(88 * scale, summary_h * .23)
    meta_h = min(44 * scale, summary_h * .15)
    poster_w = min(card_w * .235, summary_h / 1.5)
    poster_h = poster_w * 1.5
    text_x, text_w = pad + poster_w + gap, card_w - 2 * pad - poster_w - gap
    plot_h = max(1, summary_h - title_h - meta_h - gap)
    content_y = pad + header_h + gap
    action_y = content_y + summary_h + gap
    details_y = action_y + button_h + gap
    card_h = details_y + details_title_h + details_h + pad
    # Very short popup windows retain the synopsis/actions and page details.
    if card_h > available_h:
        extra = card_h - available_h
        details_h = max(0, details_h - extra)
        card_h = min(available_h, details_y + details_title_h + details_h + pad)
    def rect(x, y, w, h):
        return tuple(round(v) for v in (x, y * ratio, w, h * ratio))
    bar_w = 22 * scale
    plot_x, plot_y = text_x, content_y + title_h + meta_h + gap
    body_w = max(1, text_w - bar_w - gap / 2)
    button_w = (card_w - 2 * pad - gap) / 2
    positions = {
        110: rect(0, 0, card_w, card_h), 111: rect(0, 0, card_w, card_h),
        9: rect(pad, pad, 144 * scale, header_h),
        119: rect(pad + 164 * scale, pad, card_w - 2 * pad - 164 * scale, header_h),
        118: rect(pad, pad + header_h + gap / 2, card_w - 2 * pad, 1 * scale),
        112: rect(pad, content_y, poster_w, poster_h),
        120: rect(text_x, content_y, text_w, title_h),
        121: rect(text_x, content_y + title_h, text_w, meta_h),
        126: rect(plot_x, plot_y, body_w, plot_h),
        101: rect(pad, action_y, button_w, button_h),
        102: rect(pad + button_w + gap, action_y, button_w, button_h),
        130: rect(pad, details_y, card_w - 2 * pad, details_title_h),
        131: rect(pad, details_y + details_title_h, card_w - 2 * pad - bar_w - gap / 2, details_h),
    }
    bars = {127: rect(plot_x + text_w - bar_w, plot_y, bar_w, plot_h),
            132: rect(card_w - pad - bar_w, details_y + details_title_h, bar_w, details_h)}
    return dict(x=round((width-card_w)/2), y=round((height-card_h*ratio)/2),
                width=round(card_w), height=round(card_h*ratio), controls=positions, bars=bars)


def show_information(item, entry, play_available=True, resume=False):
    """Return only play/trailer/empty after the single dialog has closed."""
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
    if xbmc.getSkinDir() != 'skin.infinity.diggz' or item is None:
        return ''
    view = presentation(entry)
    if not view['title']:
        return ''
    trailer = bool(view['trailer'])
    if trailer and view['trailer'].startswith('plugin://'):
        host = urlsplit(view['trailer']).netloc
        trailer = bool(xbmc.getCondVisibility('System.AddonIsEnabled(%s)' % host))
    addon_root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('path')))

    class Information(xbmcgui.WindowXMLDialog):
        choice = ''
        ready = False
        viewport = None

        def reflow(self):
            background = self.getControl(190)
            dimensions = (background.getWidth(), background.getHeight(),
                          xbmc.getInfoLabel('System.ScreenWidth'), xbmc.getInfoLabel('System.ScreenHeight'))
            if self.viewport == dimensions:
                return
            bounds = geometry(*dimensions, details=bool(view['details']))
            card = self.getControl(100)
            card.setPosition(bounds['x'], bounds['y'])
            card.setWidth(bounds['width']); card.setHeight(bounds['height'])
            for ident, (x, y, width, height) in bounds['controls'].items():
                control = self.getControl(ident)
                control.setPosition(x, y); control.setWidth(width); control.setHeight(max(1, height))
            # Kodi has no Python ControlScrollBar wrapper. Reposition supported
            # groups; their native 1000-unit bars use a static layout transform.
            for ident, (x, y, width, height) in bounds['bars'].items():
                group = self.getControl(ident)
                group.setPosition(x, y)
                sx, sy = width / 32.0 * 100, max(1, height) / 1000.0 * 100
                group.setAnimations([('conditional',
                    'effect=zoom start=%s,%s end=%s,%s center=%s,%s time=0 condition=true' %
                    (sx, sy, sx, sy, x, y))])
            self.viewport = dimensions

        def onInit(self):
            if self.ready:
                # The exact native owner sends this existing callback on resize.
                # Keep synopsis/details scroll offsets and the current focus.
                self.reflow()
                return
            self.viewport = None
            self.setProperty('Infinity.Information.HasDetails', 'true' if view['details'] else 'false')
            self.reflow()
            self.getControl(120).setText(view['title'])
            self.getControl(121).setLabel(view['metadata'])
            self.getControl(126).setText(view['synopsis'] if view['synopsis'] else 'No synopsis is available for this title.')
            self.getControl(131).setText(view['details'])
            self.getControl(112).setVisible(bool(view['poster']))
            if view['poster']:
                self.getControl(112).setImage(view['poster'])
            self.getControl(101).setLabel('Resume' if resume else 'Play')
            self.getControl(101).setEnabled(bool(play_available))
            self.getControl(102).setEnabled(trailer)
            for ident in (130, 131, 132):
                self.getControl(ident).setVisible(bool(view['details']))
            self.setFocusId(101 if play_available else 102 if trailer else 9)
            self.ready = True

        def onClick(self, ident):
            self.reflow()
            if ident in (190, 9):
                self.close()
            elif ident == 101 and play_available:
                self.choice = 'play'; self.close()
            elif ident == 102 and trailer:
                self.choice = 'trailer'; self.close()

        def onAction(self, action):
            self.reflow()
            if action.getId() in CANCEL_ACTIONS:
                self.close()

        def onFocus(self, control_id):
            if self.ready:
                self.reflow()

    window = Information('InfinityInformation.xml', str(addon_root), 'Default', '1080i')
    try:
        window.doModal()
        return window.choice if window.ready else ''
    finally:
        window.close()
        del window
