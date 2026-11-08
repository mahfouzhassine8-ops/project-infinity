"""Approved Infinity appearance, motion and Ambient routes, on demand only."""
from __future__ import annotations
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from pathlib import Path
from common import addon, addon_set_setting, persistence_scope


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


def choose(title, labels, current=0):
    if not labels:return -1
    class Selector(xbmcgui.WindowXMLDialog):
        result=-1
        ready=False
        def reflow(self):
            backdrop,card=self.getControl(190),self.getControl(100)
            bounds=fit_popup(backdrop.getWidth(),backdrop.getHeight(),len(labels))
            card.setHeight(bounds['height'])
            surface=self.getControl(101)
            surface.setHeight(bounds['height']-2*surface.getPosition()[1])
            card.setPosition(bounds['left'],bounds['top'])
            percent=bounds['scale']*100
            card.setAnimations([('conditional',
                'effect=zoom start=%s,%s end=%s,%s center=%s,%s time=0 condition=true' %
                (percent,percent,percent,percent,bounds['left'],bounds['top']))])
            self.getControl(50).setHeight(bounds['rows_height'])

        def onInit(self):
            if self.ready:
                self.reflow()
                return
            self.setProperty('Infinity.UI.Popup','1')
            self.setProperty('Infinity.UI.Title',title)
            self.reflow()
            rows=self.getControl(50);rows.reset()
            for index,label in enumerate(labels):
                row=xbmcgui.ListItem(label=label)
                row.setProperty('Infinity.UI.Version','1');row.setProperty('Infinity.UI.Kind','action')
                row.setProperty('Infinity.UI.Token',str(index));rows.addItem(row)
            rows.selectItem(current if 0<=current<len(labels) else 0)
            self.setFocusId(50);self.ready=True
        def onClick(self,control_id):
            if control_id==50:
                index=self.getControl(50).getSelectedPosition()
                if 0<=index<len(labels):self.result=index;self.close()
            elif control_id in (190,9):self.close()
        def onAction(self,action):
            if action.getId() in (10,92,110):self.close()
    root=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('path')))
    window=Selector('InfinityItemOptions.xml',str(root),'Default','1080i')
    try:
        window.doModal()
        if not window.ready:raise RuntimeError('The compact Infinity selector could not load.')
        return window.result
    finally:
        window.close()


def setting_choice(title, owner, key, values, labels, default):
    actual=xbmcaddon.Addon(owner)
    current=actual.getSetting(key) or default
    pick=choose(title,labels,values.index(current) if current in values else 0)
    if not 0 <= pick < len(values):
        return
    if not addon_set_setting(owner,key,values[pick]):
        xbmcgui.Dialog().ok('Infinity settings','Kodi could not save this selection. No mode was applied.')
        return
    # CAddonMgr constructs separate setting trees. ReloadSettings updates only
    # the first registered tree, so the pre-menu instance is not authoritative.
    actual = xbmcaddon.Addon(owner)
    if actual.getSetting(key) != values[pick]:
        xbmcgui.Dialog().ok('Infinity settings','The saved value could not be confirmed. Reopen this menu to check it.')
        return
    home=xbmcgui.Window(10000)
    if key=='ambient_home':
        # Resolve directly from the saved owner, not an enum index or a stale
        # pre-created Addon instance in the resident experience publisher.
        home.setProperty('Infinity.AmbientHome.Mode',actual.getSetting(key))
    elif key=='motion_mode':
        home.setProperty('Infinity.MotionModeUser',actual.getSetting(key))
    # Existing compatibility/service notifications publish the complete theme
    # palette. There is no ReloadSkin, Container.Refresh or widget revision here.
    xbmc.executebuiltin('NotifyAll(script.infinity.commandcenter,settings.changed)')


def open_settings(action='appearance'):
    if xbmc.getSkinDir()!='skin.infinity.diggz':
        return
    if action=='motion-settings':
        setting_choice('Infinity Motion','script.infinity.commandcenter','motion_mode',
            ('full','reduced','off'),('Full','Reduced','Off'),'full')
    elif action=='ambient-home':
        setting_choice('Infinity Ambient Home','script.infinity.commandcenter','ambient_home',
            ('off','subtle','immersive'),('Off','Subtle','Immersive'),'subtle')
    elif action=='dark-appearance':
        current=xbmc.getInfoLabel('Skin.String(Infinity.DarkAppearance)')
        pick=choose('Dark Mode Appearance',['Original Infinity Dark','True OLED Black'],int(current=='oled'))
        if pick in (0,1):
            # Skin settings remain owned by Kodi's existing mandatory durable
            # owner; use the original command and writer gate.
            with persistence_scope():
                xbmc.executebuiltin('Skin.SetString(Infinity.DarkAppearance,'+('oled' if pick else 'original')+')',True)
    elif action=='theme':
        value=xbmcaddon.Addon('service.infinity.compat').getSetting('theme_mode') or 'system'
        selected=choose('Infinity Theme',['Follow System','Light Pearl','Dark','Dark Mode Appearance'],
                        ('system','light','dark').index(value) if value in ('system','light','dark') else 0)
        if selected==3:
            open_settings('dark-appearance')
        elif selected in (0,1,2):
            value=('system','light','dark')[selected]
            owner=xbmcaddon.Addon('service.infinity.compat')
            if not addon_set_setting('service.infinity.compat','theme_mode',value) or xbmcaddon.Addon('service.infinity.compat').getSetting('theme_mode')!=value:
                xbmcgui.Dialog().ok('Infinity Theme','The existing theme owner did not confirm the selection.')
    else:
        if choose('Infinity Appearance',['Theme'])==0:
            open_settings('theme')
