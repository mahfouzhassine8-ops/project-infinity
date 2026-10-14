"""On-demand, read-only rail evidence. Never infer load failure from empty labels."""
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

CONTROLS = (9200, 8820, 8720, 19600, 19601)
SECTIONS = ('movies', 'tvshows')


def classify(home_active, visible, failed, ready, count, dynamic):
    if not home_active:
        return 'HOME_INACTIVE_NOT_SAMPLED'
    if not visible:
        return 'CONTROL_INACTIVE_NOT_SAMPLED'
    if dynamic == 'true':
        return 'DYNAMIC_ITEM_OBSERVED'
    if failed == 'true':
        return 'HELPER_REPORTED_FAILURE'
    if count is None:
        return 'CONTROL_DATA_UNAVAILABLE'
    if count == 0:
        return 'EMPTY_UNCONFIRMED' if ready != 'true' else 'READY_BUT_EMPTY_UNCONFIRMED'
    return 'NON_DYNAMIC_ITEM_OBSERVED'


def keymaps(vfs):
    """Inventory relevant raw mappings; deliberately not an effective-map resolver."""
    results = []
    for base in ('special://xbmc/system/keymaps', 'special://masterprofile/keymaps',
                 'special://profile/keymaps'):
        try:
            root = Path(vfs.translatePath(base))
            if not root.is_dir():
                results.append({'directory': base, 'state': 'UNAVAILABLE'})
                continue
            for path in sorted(root.glob('*.xml')):
                entry = {'file': base + '/' + path.name}
                try:
                    raw = path.read_bytes()
                    entry['sha256'] = hashlib.sha256(raw).hexdigest()
                    xml = ET.fromstring(raw)
                    mappings = []
                    for window in xml:
                        if window.tag.lower() not in ('global', 'home', '10000'):
                            continue
                        for device in window:
                            for action in device:
                                if (device.tag.lower() == 'touch' and action.tag.lower() in ('longpress', 'tap', 'pan')) or (device.tag.lower() == 'mouse' and action.tag.lower() in ('rightclick', 'mousemove')):
                                    mappings.append({'window': window.tag, 'device': device.tag,
                                                     'gesture': action.tag, 'attributes': dict(action.attrib),
                                                     'action': (action.text or '').strip()})
                    entry['mappings'] = mappings
                except (OSError, ET.ParseError) as exc:
                    entry['state'] = type(exc).__name__
                results.append(entry)
        except (OSError, RuntimeError) as exc:
            results.append({'directory': base, 'state': type(exc).__name__})
    return results


def collect(xbmc, xa, gui, vfs):
    report = {'schema': 1, 'read_only': True, 'physical_acceptance': False}
    for addon_id, field in (('skin.infinity.diggz', 'skin'), ('script.infinity.rails', 'helper')):
        try:
            addon = xa.Addon(addon_id)
            report[field] = {key: addon.getAddonInfo(key) for key in ('id', 'version', 'path')}
        except RuntimeError:
            report[field] = {'state': 'UNAVAILABLE'}
    active_window = gui.getCurrentWindowId()
    active_dialog = gui.getCurrentWindowDialogId()
    report.update(window=active_window, dialog=active_dialog)
    # Info labels without an explicit window evaluate in current context. Sample
    # only with Home active and no modal dialog; otherwise empty is not evidence.
    home_active = active_window == 10000 and active_dialog in (0, -1)
    report['sampling'] = 'HOME_ACTIVE' if home_active else 'HOME_INACTIVE_NOT_SAMPLED'
    home = gui.Window(10000)
    report['sections'] = {
        section: {field: home.getProperty('Infinity.Rails.' + section + '.' + field)
                  for field in ('Ready', 'Failed', 'Revision', 'LoadedRevision')}
        for section in SECTIONS}
    report['controls'] = []
    if home_active:
        try:
            report['focus'] = home.getFocusId()
        except RuntimeError:
            report['focus'] = None
        section = xbmc.getInfoLabel('Container(9000).ListItem.Property(section)')
        report['section'] = section
        state = report['sections'].get(section, {})
        for control in CONTROLS:
            row = {'id': control, 'visible': bool(xbmc.getCondVisibility('Control.IsVisible(%d)' % control))}
            if row['visible']:
                prefix = 'Container(%d).' % control
                raw_count = xbmc.getInfoLabel(prefix + 'NumItems')
                row['count'] = int(raw_count) if raw_count.isdigit() else None
                row['directory'] = xbmc.getInfoLabel(prefix + 'FolderPath')
                row['label'] = xbmc.getInfoLabel(prefix + 'ListItem.Label')
                row['item_path'] = xbmc.getInfoLabel(prefix + 'ListItem.FolderPath')
                row['properties'] = {p: xbmc.getInfoLabel(prefix + 'ListItem.Property(' + p + ')')
                                     for p in ('Infinity.Rails.Item', 'Infinity.Rails.Key', 'Infinity.Rails.Section', 'Addon.ID')}
                row['context_actions'] = [
                    {'label': xbmc.getInfoLabel(prefix + 'ListItem.Property(contextmenulabel(%d))' % i),
                     'action': xbmc.getInfoLabel(prefix + 'ListItem.Property(contextmenuaction(%d))' % i)}
                    for i in range(8)]
                row['context_actions'] = [c for c in row['context_actions'] if c['label'] or c['action']]
            row['state'] = classify(home_active, row['visible'], state.get('Failed'), state.get('Ready'),
                                    row.get('count'), row.get('properties', {}).get('Infinity.Rails.Item'))
            report['controls'].append(row)
    report['keymap_inventory'] = keymaps(vfs)
    report['limits'] = [
        'Raw keymap entries are not proof of the effective dispatch mapping.',
        'Home properties can be historical; unset values do not prove loading failure.',
        'This snapshot does not observe Android touch recognition or native dispatch.',
        'Empty native context properties can mean unavailable API exposure; not proof of absent actions.']
    return report
