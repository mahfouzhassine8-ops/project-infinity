from datetime import datetime

import xbmcgui


ACTION_BACK = {9, 10, 92, 216}


class GuideWindow(xbmcgui.WindowDialog):
    def __init__(self, catalog, channels, theme, textures, play_callback):
        super().__init__()
        self.catalog = catalog
        self.channels = list(channels)
        self.theme = theme
        self.textures = textures
        self.play_callback = play_callback
        self._last_index = -1
        self._build()

    def _build(self):
        w, h = xbmcgui.getScreenWidth(), xbmcgui.getScreenHeight()
        margin = max(18, int(min(w, h) * 0.025))
        header_h = max(54, int(h * 0.075))
        gap = max(10, int(margin * 0.6))
        left_w = int(w * (0.34 if w > h else 0.43))
        self.addControl(xbmcgui.ControlImage(0, 0, w, h, self.textures["background"]))
        self.addControl(xbmcgui.ControlLabel(margin, margin, w - margin * 2, header_h, "INFINITY  •  GUIDE", font="font16", textColor=self.theme["text"]))
        top = margin + header_h
        body_h = h - top - margin
        self.channels_list = xbmcgui.ControlList(margin, top, left_w - margin, body_h, "font13", self.theme["text"], self.textures["panel"], self.textures["focus"], self.theme["accent"], 0, 0, 16, 0, max(46, int(body_h * 0.08)), 4)
        self.programs_list = xbmcgui.ControlList(left_w + gap, top, w - left_w - gap - margin, body_h, "font13", self.theme["text"], self.textures["panel"], self.textures["focus"], self.theme["accent"], 0, 0, 16, 0, max(46, int(body_h * 0.08)), 4)
        self.addControls([self.channels_list, self.programs_list])
        for channel in self.channels:
            guide = self.catalog.guides.get(channel.stable_key())
            now = guide.current.title if guide and guide.current else "No guide data"
            self.channels_list.addItem(xbmcgui.ListItem(label=channel.name, label2=now))
        if self.channels:
            self.channels_list.selectItem(0)
            self._fill_programs(0)
        self.setFocus(self.channels_list)

    def _fill_programs(self, index):
        if index < 0 or index >= len(self.channels):
            return
        self._last_index = index
        self.programs_list.reset()
        guide = self.catalog.guides.get(self.channels[index].stable_key())
        schedule = guide.schedule if guide else []
        if not schedule:
            self.programs_list.addItem(xbmcgui.ListItem(label="No guide data", label2=""))
            return
        local_now = datetime.now().astimezone()
        for program in schedule:
            start = program.start.astimezone(local_now.tzinfo).strftime("%I:%M %p").lstrip("0")
            stop = program.stop.astimezone(local_now.tzinfo).strftime("%I:%M %p").lstrip("0")
            self.programs_list.addItem(xbmcgui.ListItem(label=program.title, label2=f"{start} – {stop}"))

    def onAction(self, action):
        if action.getId() in ACTION_BACK:
            self.close()
            return
        if self.getFocus() == self.channels_list:
            index = self.channels_list.getSelectedPosition()
            if index != self._last_index:
                self._fill_programs(index)

    def onControl(self, control):
        if control == self.channels_list:
            index = self.channels_list.getSelectedPosition()
            if 0 <= index < len(self.channels):
                self.play_callback(self.channels[index])
                self._fill_programs(index)
