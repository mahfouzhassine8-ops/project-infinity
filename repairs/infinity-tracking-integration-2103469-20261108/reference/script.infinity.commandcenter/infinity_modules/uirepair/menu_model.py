"""Pure context decisions. No side effects on selection or menu construction."""
import re

ADDON = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,199}\Z')

def addon_rows(has_settings, rails_supported, favourite_supported=True, manageable=True):
    rows = [('Open', 'open'), ('Add-on Information', 'info')]
    if has_settings:
        rows.append(('Add-on Settings', 'settings'))
    if favourite_supported:
        rows.append(('Add to Favourites', 'favourite'))
    if rails_supported:
        rows.append(('Add to Infinity Rails', 'rails'))
    if manageable:
        rows += [('Hide from This View', 'hide'), ('More / Manage Add-on', 'manage')]
    return rows

def valid_id(value):
    return isinstance(value, str) and bool(ADDON.fullmatch(value))

def hidden_setting(addon_id):
    if not valid_id(addon_id):
        raise ValueError('Invalid video add-on identity')
    return 'Infinity.VideoSources.Hidden.' + addon_id
