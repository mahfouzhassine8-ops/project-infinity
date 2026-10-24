"""Fail-closed Option B synopsis space correction, preserving full content and actions."""
from hashlib import sha256

PREIMAGE_SHA256='c388b83353bff8e7687a545d3a00ea16691a208bd34b3a0a0678ff6441abb54e'
INSERT_BEFORE=b"def geometry(width, height, physical_width='', physical_height='', details=True):"
HELPER=b'''def _estimated_synopsis_height(synopsis, available_text_width, scale):
    """Reserve readable room for short metadata without preallocating 650 units.

    This conservative estimate only adjusts available textbox height; Kodi's
    native textbox retains full text and provides vertical scrolling if needed.
    """
    text = synopsis if isinstance(synopsis, str) else ''
    columns = max(15, int(available_text_width / max(1, 13 * scale)))
    rows = sum(max(1, (len(line) + columns - 1) // columns)
               for line in text.splitlines() or [''])
    return min(650 * scale, max(136 * scale, (rows + 1) * 38 * scale))


'''
OLD_DECL=INSERT_BEFORE
NEW_DECL=b"def geometry(width, height, physical_width='', physical_height='', details=True, synopsis=''):"
OLD_SUMMARY=b'    summary_h = min(650 * scale, max(1, available_h - reserve))'
NEW_SUMMARY=(b'    # Compact short plots; long plots retain the original scrollable upper bound.\n'
             b'    available_plot_w = max(1, card_w - 2 * pad - card_w * .235 - gap - 25 * scale)\n'
             b'    preferred_plot_h = _estimated_synopsis_height(synopsis, available_plot_w, scale)\n'
             b'    summary_h = min(650 * scale, max(1, available_h - reserve),\n'
             b'                    max(268 * scale, 132 * scale + gap + preferred_plot_h))')
OLD_CALL=b"            bounds = geometry(*dimensions, details=bool(view['details']))"
NEW_CALL=b"            bounds = geometry(*dimensions, details=bool(view['details']), synopsis=view['synopsis'])"

def transform(original):
    if sha256(original).hexdigest()!=PREIMAGE_SHA256:
        raise ValueError('Exact signed CC35 information preimage required')
    for old in (OLD_DECL,OLD_SUMMARY,OLD_CALL):
        if original.count(old)!=1:raise ValueError('Scope or input text unexpected')
    out=original.replace(OLD_DECL,HELPER+NEW_DECL,1).replace(OLD_SUMMARY,NEW_SUMMARY,1).replace(OLD_CALL,NEW_CALL,1)
    reversed_=out.replace(HELPER+NEW_DECL,OLD_DECL,1).replace(NEW_SUMMARY,OLD_SUMMARY,1).replace(NEW_CALL,OLD_CALL,1)
    if reversed_!=original:raise ValueError('Unexpected out-of-scope change')
    compile(out,'information.py','exec')
    return out
