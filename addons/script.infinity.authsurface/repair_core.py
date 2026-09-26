# -*- coding: utf-8 -*-
"""Pure source-transform helpers for Infinity Authorization & Accounts.

No Kodi imports and no credential access. The functions only transform known
Account Manager Lite source shapes and refuse unknown/ambiguous preimages.
"""
import re

FIXED_REFRESH='your_refresh = acctmgr.getSetting("trakt.refresh")'
OLD_REFRESH_RE=re.compile(r'(?m)^(?P<i>[ \t]*)your_refresh\s*=\s*([\'"])1\2\s*(?:#.*)?$')

def patch_sync(text):
    if FIXED_REFRESH in text:
        return text, False
    hits=list(OLD_REFRESH_RE.finditer(text))
    if len(hits)!=1:
        raise RuntimeError("Unexpected AM Lite trakt_sync.py refresh-token preimage")
    m=hits[0]
    replacement=m.group("i")+FIXED_REFRESH
    return text[:m.start()]+replacement+text[m.end():], True

def _all_method(indent):
    b=indent+"    "
    bb=b+"    "
    lines=[
        indent+"def create_all_list(self):",
        b+'"""Save every installed Trakt target supported by this AM Lite build."""',
        b+"addon_list = []",
        b+"targets = (",
        bb+"('chk_nxtflixlt', 'NXTFlix Light'),",
        bb+"('chk_gears', 'The Gears'),",
        bb+"('chk_red', 'Red Light'),",
        bb+"('chk_umb', 'Umbrella'),",
        bb+"('chk_pov', 'POV'),",
        bb+"('chk_coal', 'The Coalition'),",
        bb+"('chk_genocide', 'Genocide'),",
        bb+"('chk_shadow', 'Shadow'),",
        bb+"('chk_ghost', 'Ghost'),",
        bb+"('chk_chains', 'The Chains'),",
        bb+"('chk_home', 'Homelander'),",
        bb+"('chk_night', 'Nightwing'),",
        bb+"('chk_absol', 'Jokers Absolution'),",
        bb+"('chk_scrubs', 'Scrubs V2'),",
        bb+"('chk_redg', 'Gratis Red'),",
        bb+"('chk_crew', 'The Crew'),",
        bb+"('chk_salts', 'SALTS'),",
        bb+"('chk_tmdbh', 'TMDb Helper'),",
        bb+"('chk_trakt', 'Trakt Addon'),",
        b+")",
        b+"for attr, name in targets:",
        bb+"path = getattr(var, attr, None)",
        bb+"if path and xbmcvfs.exists(path) and name not in addon_list:",
        bb+"    addon_list.append(name)",
        b+"if not addon_list:",
        bb+"control.notification('Account Manager Lite', 'No supported Trakt add-ons found!', icon=trakt_icon)",
        bb+"return []",
        b+"if not xbmcvfs.exists(var.acctmgr_datapath):",
        bb+"xbmcvfs.mkdirs(var.acctmgr_datapath)",
        b+"try:",
        bb+"with open(var.tk_sync_list, 'w') as synclist:",
        bb+"    json.dump({'addon_list': addon_list}, synclist, indent=4)",
        b+"except Exception as e:",
        bb+'log_utils.error(f"Failed to save all-installed Trakt sync list: {e}")',
        bb+"return []",
        b+"control.notification('Account Manager Lite', 'All installed supported Trakt targets selected!', icon=trakt_icon)",
        b+"return addon_list",
        "",
    ]
    return "\n".join(lines)+"\n"

def patch_select(text):
    if "def create_all_list(self):" in text:
        return text, False
    class_m=re.search(r'(?m)^class\s+tk_list\s*\(\s*\)\s*:\s*\r?$', text)
    if not class_m:
        raise RuntimeError("Unexpected AM Lite trakt_select.py class preimage")
    after=text[class_m.end():]
    def_m=re.search(r'(?m)^(?P<i>[ \t]+)def\s+create_list\s*\(\s*self\s*\)\s*:', after)
    if not def_m:
        raise RuntimeError("Unexpected AM Lite trakt_select.py create_list preimage")
    indent=def_m.group("i")
    insert_at=class_m.end()
    newline="\r\n" if "\r\n" in text else "\n"
    method=_all_method(indent).replace("\n",newline)
    return text[:insert_at]+newline+method+text[insert_at+len(newline) if text[insert_at:insert_at+len(newline)]==newline else insert_at:], True

ACTION_BLOCK=r'''
elif action == 'traktAuthAll':
        # Infinity: authorize once, select every installed AM Lite-supported target,
        # propagate the real access + rotating refresh token, and return without
        # force-killing Kodi.
        from acctmgr.modules.sync import trakt_select
        installed = trakt_select.tk_list().create_all_list()
        if not installed:
                control.notification('Account Manager Lite', 'No supported Trakt targets found!', icon=trakt_icon)
                raise SystemExit

        from acctmgr.modules.auth import trakt
        ok = trakt.Trakt().auth()
        if not ok:
                control.notification('Account Manager Lite', 'Trakt authorization did not complete.', icon=trakt_icon)
                raise SystemExit

        get_acctmgr().setSetting("api.service", "true")
        control.setSetting('api.stop', 'false')
        xbmc.sleep(500)
        from acctmgr.modules.sync import trakt_sync
        trakt_sync.Auth().trakt_auth(mode="auth")
        control.notification('Account Manager Lite', 'Trakt synced to all installed supported add-ons.', icon=trakt_icon)
        xbmc.sleep(500)
        control.updates_off()
        dialog.ok('Infinity Authorization & Accounts',
                  'Trakt authorization and sync completed. Restart Infinity once, then run Kodi Health Center Authorization Health.')

elif action == 'traktReSyncAll':
        # Infinity: re-sync the current AM Lite Trakt authorization everywhere
        # without the upstream force-close path.
        if not control.setting('trakt.token') or not control.setting('trakt.refresh'):
                dialog.ok('Infinity Authorization & Accounts',
                          'Trakt is not fully authorized in Account Manager Lite. Use Authorize / Reauthorize first.')
                raise SystemExit
        from acctmgr.modules.sync import trakt_select
        installed = trakt_select.tk_list().create_all_list()
        if not installed:
                control.notification('Account Manager Lite', 'No supported Trakt targets found!', icon=trakt_icon)
                raise SystemExit
        from acctmgr.modules.sync import trakt_sync
        trakt_sync.Auth().trakt_auth(mode="auth")
        control.notification('Account Manager Lite', 'Trakt re-synced to all installed supported add-ons.', icon=trakt_icon)
        xbmc.sleep(500)
        dialog.ok('Infinity Authorization & Accounts',
                  'Trakt re-sync completed. Run Kodi Health Center Authorization Health to verify refresh-token alignment.')

'''

def patch_default(text):
    if "action == 'traktAuthAll'" in text and "action == 'traktReSyncAll'" in text:
        return text, False
    anchor=re.search(r"(?m)^elif\s+action\s*==\s*(['\"])traktAuth\1\s*:", text)
    if not anchor:
        raise RuntimeError("Unexpected AM Lite default.py Trakt action preimage")
    if "action == 'traktAuthAll'" in text or "action == 'traktReSyncAll'" in text:
        raise RuntimeError("Partial Infinity Trakt action patch detected")
    return text[:anchor.start()]+ACTION_BLOCK+text[anchor.start():], True

def source_status(sync_text, select_text, default_text):
    fixed_refresh=FIXED_REFRESH in sync_text
    old_refresh=bool(OLD_REFRESH_RE.search(sync_text))
    all_list="def create_all_list(self):" in select_text
    auth_all="action == 'traktAuthAll'" in default_text
    resync_all="action == 'traktReSyncAll'" in default_text
    if fixed_refresh and all_list and auth_all and resync_all:
        return "APPLIED"
    if old_refresh and not any((all_list,auth_all,resync_all)):
        return "READY"
    if any((fixed_refresh,all_list,auth_all,resync_all)):
        return "PARTIAL"
    return "UNSUPPORTED"
