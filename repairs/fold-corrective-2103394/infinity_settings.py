"""Approved Infinity appearance, motion and Ambient routes, on demand only."""
from __future__ import annotations
import xbmc
import xbmcaddon
import xbmcgui
from common import addon, addon_set_setting, persistence_scope


def choose(title, labels, current=0):
    home=xbmcgui.Window(10000)
    home.setProperty('Infinity.Select.Compact','true')
    try:
        return xbmcgui.Dialog().select(title,labels,preselect=current)
    finally:
        home.clearProperty('Infinity.Select.Compact')


def setting_choice(title, owner, key, values, labels, default):
    actual=xbmcaddon.Addon(owner)
    current=actual.getSetting(key) or default
    pick=choose(title,labels,values.index(current) if current in values else 0)
    if not 0 <= pick < len(values):
        return
    if not addon_set_setting(owner,key,values[pick]) or actual.getSetting(key)!=values[pick]:
        xbmcgui.Dialog().ok('Infinity settings','Kodi did not confirm this setting. Its previous saved value was retained.')
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
        selected=choose('Infinity Theme',['Follow System','Light Pearl','Dark','Dark Mode Appearance'])
        if selected==3:
            open_settings('dark-appearance')
        elif selected in (0,1,2):
            value=('system','light','dark')[selected]
            owner=xbmcaddon.Addon('service.infinity.compat')
            if not addon_set_setting('service.infinity.compat','theme_mode',value) or owner.getSetting('theme_mode')!=value:
                xbmcgui.Dialog().ok('Infinity Theme','The existing theme owner did not confirm the selection.')
    else:
        if choose('Infinity Appearance',['Theme'])==0:
            open_settings('theme')
