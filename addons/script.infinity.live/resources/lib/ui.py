from datetime import datetime, timezone
from urllib.parse import quote_plus

import xbmc
import xbmcgui

from .guide import GuideWindow

ACTION_BACK = {9, 10, 92, 216}
MOVE_ACTIONS = {1, 2, 3, 4, 5, 6, 7}


def detect_theme():
    home = xbmcgui.Window(10000)
    mode = (home.getProperty("Infinity.SystemTheme") or home.getProperty("Infinity.NativeSystemTheme") or "dark").strip().lower()
    if mode == "light":
        return {
            "name": "light",
            "text": "FF0B2030",
            "muted": "FF587083",
            "accent": "FF05A9E8",
            "danger": "FFD92D20",
        }
    return {
        "name": "oled" if mode == "oled" else "dark",
        "text": "FFF7FBFF",
        "muted": "FFABC0CF",
        "accent": "FF00B8FF",
        "danger": "FFFF625A",
    }


def textures_for(addon_path, theme):
    root = addon_path.rstrip("/") + "/resources/media/"
    light = theme["name"] == "light"
    return {
        "background": root + ("background_light.png" if light else "background_dark.png"),
        "panel": root + ("panel_light.png" if light else "panel_dark.png"),
        "soft": root + ("soft_light.png" if light else "soft_dark.png"),
        "focus": root + ("focus_light.png" if light else "focus_dark.png"),
        "accent": root + "accent.png",
    }


class InfinityLiveWindow(xbmcgui.WindowDialog):
    def __init__(self, addon_path, catalog, store, player, on_play):
        super().__init__()
        self.addon_path = addon_path
        self.catalog = catalog
        self.store = store
        self.player = player
        self.on_play = on_play
        self.theme = detect_theme()
        self.textures = textures_for(addon_path, self.theme)
        self.outcome = "exit"
        self.filtered = []
        self.group_name = "All"
        self._last_channel_index = -1
        self._last_group_index = -1
        self._build()

    def _layout(self, w, h, margin, header_h, footer_h):
        body_top = margin + header_h
        body_h = h - body_top - footer_h - margin * 2
        gap = max(10, int(margin * 0.55))
        aspect = w / float(max(1, h))
        if aspect >= 1.35:
            group_w = int(w * 0.16)
            channel_w = int(w * 0.27)
            preview_x = margin + group_w + gap + channel_w + gap
            return {
                "groups": (margin, body_top, group_w, body_h),
                "channels": (margin + group_w + gap, body_top, channel_w, body_h),
                "preview": (preview_x, body_top, w - preview_x - margin, int(body_h * 0.64)),
                "info": (preview_x, body_top + int(body_h * 0.64) + gap, w - preview_x - margin, body_h - int(body_h * 0.64) - gap),
            }
        if aspect <= 0.82:
            preview_h = int(body_h * 0.30)
            list_top = body_top + preview_h + gap
            list_h = body_h - preview_h - gap
            group_w = int((w - margin * 2 - gap) * 0.32)
            return {
                "preview": (margin, body_top, w - margin * 2, preview_h),
                "groups": (margin, list_top, group_w, list_h),
                "channels": (margin + group_w + gap, list_top, w - margin * 2 - group_w - gap, int(list_h * 0.66)),
                "info": (margin + group_w + gap, list_top + int(list_h * 0.66) + gap, w - margin * 2 - group_w - gap, list_h - int(list_h * 0.66) - gap),
            }
        group_w = int(w * 0.22)
        channel_w = int(w * 0.34)
        preview_x = margin + group_w + gap + channel_w + gap
        return {
            "groups": (margin, body_top, group_w, body_h),
            "channels": (margin + group_w + gap, body_top, channel_w, body_h),
            "preview": (preview_x, body_top, w - preview_x - margin, int(body_h * 0.52)),
            "info": (preview_x, body_top + int(body_h * 0.52) + gap, w - preview_x - margin, body_h - int(body_h * 0.52) - gap),
        }

    def _build(self):
        w, h = xbmcgui.getScreenWidth(), xbmcgui.getScreenHeight()
        margin = max(18, int(min(w, h) * 0.025))
        header_h = max(54, int(h * 0.075))
        footer_h = max(54, int(h * 0.072))
        layout = self._layout(w, h, margin, header_h, footer_h)

        self.addControl(xbmcgui.ControlImage(0, 0, w, h, self.textures["background"]))
        icon_size = int(header_h * 0.58)
        self.addControl(xbmcgui.ControlImage(margin, margin + int((header_h - icon_size) / 2), icon_size, icon_size, self.addon_path.rstrip("/") + "/resources/icon.png", 2))
        self.addControl(xbmcgui.ControlLabel(margin + icon_size + 14, margin, int(w * 0.38), header_h, "INFINITY  •  LIVE", font="font16", textColor=self.theme["text"], alignment=4))
        self.source_label = xbmcgui.ControlLabel(int(w * 0.52), margin, w - int(w * 0.52) - margin, header_h, self.catalog.source_name, font="font13", textColor=self.theme["muted"], alignment=6)
        self.addControl(self.source_label)

        gx, gy, gw, gh = layout["groups"]
        cx, cy, cw, ch = layout["channels"]
        px, py, pw, ph = layout["preview"]
        ix, iy, iw, ih = layout["info"]
        item_h = max(44, int(min(h * 0.06, 72)))

        self.groups = xbmcgui.ControlList(gx, gy, gw, gh, "font13", self.theme["text"], self.textures["panel"], self.textures["focus"], self.theme["accent"], 0, 0, 14, 0, item_h, 4)
        logo_size = max(28, item_h - 12)
        self.channels = xbmcgui.ControlList(cx, cy, cw, ch, "font13", self.theme["text"], self.textures["panel"], self.textures["focus"], self.theme["accent"], logo_size, logo_size, logo_size + 18, 0, item_h, 4)
        self.addControls([self.groups, self.channels])

        self.addControl(xbmcgui.ControlImage(px, py, pw, ph, self.textures["panel"]))
        inset = max(3, int(min(w, h) * 0.004))
        self.video = xbmcgui.ControlVideoWindow(px + inset, py + inset, pw - inset * 2, ph - inset * 2)
        self.addControl(self.video)

        self.addControl(xbmcgui.ControlImage(ix, iy, iw, ih, self.textures["soft"]))
        info_pad = max(12, int(margin * 0.65))
        self.channel_title = xbmcgui.ControlLabel(ix + info_pad, iy + info_pad, iw - info_pad * 2, max(28, int(ih * 0.24)), "Select a channel", font="font14", textColor=self.theme["text"])
        self.now_label = xbmcgui.ControlLabel(ix + info_pad, iy + info_pad + max(30, int(ih * 0.25)), iw - info_pad * 2, max(24, int(ih * 0.20)), "", font="font13", textColor=self.theme["text"])
        self.next_label = xbmcgui.ControlLabel(ix + info_pad, iy + info_pad + max(58, int(ih * 0.48)), iw - info_pad * 2, max(22, int(ih * 0.18)), "", font="font13", textColor=self.theme["muted"])
        self.status_label = xbmcgui.ControlLabel(ix + info_pad, iy + ih - max(38, int(ih * 0.22)), iw - info_pad * 2, max(22, int(ih * 0.18)), self.catalog.warning or "", font="font13", textColor=self.theme["muted"])
        self.addControls([self.channel_title, self.now_label, self.next_label, self.status_label])

        labels = ["GUIDE", "FAVORITE", "FULL SCREEN", "SOURCES", "REFRESH", "EXIT"]
        available = w - margin * 2
        gap = max(6, int(margin * 0.35))
        button_w = int((available - gap * (len(labels) - 1)) / len(labels))
        button_h = footer_h
        y = h - margin - button_h
        self.buttons = {}
        for index, label in enumerate(labels):
            x = margin + index * (button_w + gap)
            control = xbmcgui.ControlButton(x, y, button_w, button_h, label, self.textures["focus"], self.textures["panel"], alignment=6, font="font13", textColor=self.theme["text"], focusedColor="FFFFFFFF")
            self.addControl(control)
            self.buttons[label] = control

        self._populate_groups()
        self._select_initial_channel()
        self.setFocus(self.channels if self.filtered else self.groups)

    def _populate_groups(self):
        self.groups.reset()
        favs = self.store.favorites(self.catalog.source_id)
        names = ["All"]
        if favs:
            names.append("★ Favorites")
        names.extend(self.catalog.groups)
        self.group_options = names
        for name in names:
            self.groups.addItem(xbmcgui.ListItem(label=name))
        self.groups.selectItem(0)
        self._apply_group(0)

    def _apply_group(self, index):
        if index < 0 or index >= len(self.group_options):
            return
        self._last_group_index = index
        self.group_name = self.group_options[index]
        favs = self.store.favorites(self.catalog.source_id)
        if self.group_name == "All":
            self.filtered = list(self.catalog.channels)
        elif self.group_name == "★ Favorites":
            self.filtered = [c for c in self.catalog.channels if c.stable_key() in favs]
        else:
            self.filtered = [c for c in self.catalog.channels if (c.group or "Other") == self.group_name]
        self.channels.reset()
        for channel in self.filtered:
            guide = self.catalog.guides.get(channel.stable_key())
            now = guide.current.title if guide and guide.current else (channel.group or "Live")
            item = xbmcgui.ListItem(label=channel.name, label2=now)
            if channel.logo:
                item.setArt({"thumb": channel.logo, "icon": channel.logo})
            self.channels.addItem(item)
        if self.filtered:
            self.channels.selectItem(0)
            self._last_channel_index = 0
            self._show_channel(self.filtered[0])
        else:
            self._last_channel_index = -1
            self.channel_title.setLabel("No channels in this group")
            self.now_label.setLabel("")
            self.next_label.setLabel("")

    def _select_initial_channel(self):
        wanted = self.store.last_channel(self.catalog.source_id)
        if not wanted:
            return
        for index, channel in enumerate(self.filtered):
            if channel.stable_key() == wanted:
                self.channels.selectItem(index)
                self._last_channel_index = index
                self._show_channel(channel)
                return

    def _show_channel(self, channel):
        guide = self.catalog.guides.get(channel.stable_key())
        self.channel_title.setLabel(channel.name)
        if guide and guide.current:
            now = guide.current
            local = datetime.now().astimezone().tzinfo
            start = now.start.astimezone(local).strftime("%I:%M %p").lstrip("0")
            stop = now.stop.astimezone(local).strftime("%I:%M %p").lstrip("0")
            duration = max(1.0, (now.stop - now.start).total_seconds())
            elapsed = max(0.0, (datetime.now(timezone.utc) - now.start).total_seconds())
            pct = min(100, max(0, int(100 * elapsed / duration)))
            self.now_label.setLabel(f"NOW  •  {now.title}  •  {start} – {stop}  •  {pct}%")
        else:
            self.now_label.setLabel("NOW  •  Live")
        if guide and guide.next:
            local = datetime.now().astimezone().tzinfo
            start = guide.next.start.astimezone(local).strftime("%I:%M %p").lstrip("0")
            self.next_label.setLabel(f"NEXT  •  {start}  •  {guide.next.title}")
        else:
            self.next_label.setLabel("")

    def _selected_channel(self):
        index = self.channels.getSelectedPosition()
        if 0 <= index < len(self.filtered):
            return self.filtered[index]
        return None

    def _play_selected(self):
        channel = self._selected_channel()
        if channel:
            self.on_play(channel)
            self.store.set_last_channel(self.catalog.source_id, channel.stable_key())
            self._show_channel(channel)

    def _toggle_favorite(self):
        channel = self._selected_channel()
        if not channel:
            return
        enabled = self.store.toggle_favorite(self.catalog.source_id, channel.stable_key())
        xbmcgui.Dialog().notification("Infinity Live", ("Added to" if enabled else "Removed from") + " favorites", self.addon_path.rstrip("/") + "/resources/icon.png", 1800, False)
        if self.group_name == "★ Favorites" and not enabled:
            self._populate_groups()

    def _open_guide(self):
        channels = self.filtered or self.catalog.channels
        guide = GuideWindow(self.catalog, channels, self.theme, self.textures, self.on_play)
        guide.doModal()
        del guide

    def onControl(self, control):
        if control == self.channels:
            self._play_selected()
            return
        if control == self.groups:
            self._apply_group(self.groups.getSelectedPosition())
            if self.filtered:
                self.setFocus(self.channels)
            return
        for label, button in self.buttons.items():
            if control != button:
                continue
            if label == "GUIDE":
                self._open_guide()
            elif label == "FAVORITE":
                self._toggle_favorite()
            elif label == "FULL SCREEN":
                if self._selected_channel() and not self.player.isPlayingVideo():
                    self._play_selected()
                if self.player.isPlayingVideo():
                    self.outcome = "fullscreen"
                    self.close()
            elif label == "SOURCES":
                self.outcome = "sources"
                self.close()
            elif label == "REFRESH":
                self.outcome = "refresh"
                self.close()
            elif label == "EXIT":
                self.outcome = "exit"
                self.close()
            return

    def onAction(self, action):
        action_id = action.getId()
        if action_id in ACTION_BACK:
            self.outcome = "exit"
            self.close()
            return
        if action_id in MOVE_ACTIONS:
            try:
                if self.getFocus() == self.channels:
                    index = self.channels.getSelectedPosition()
                    if index != self._last_channel_index and 0 <= index < len(self.filtered):
                        self._last_channel_index = index
                        self._show_channel(self.filtered[index])
                elif self.getFocus() == self.groups:
                    index = self.groups.getSelectedPosition()
                    if index != self._last_group_index:
                        self._apply_group(index)
            except Exception:
                pass
