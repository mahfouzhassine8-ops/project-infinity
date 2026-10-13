"""Pure compact-preview geometry; no Kodi, files, threads or display mutation.

The XML is authored at two logical units per design dp. Kodi window coordinates
are NOT Android dp; callers supply the live WindowXML coordinates and the native
Android view's published dp dimensions. The same transform covers glyphs and
hit testing, instead of independently resizing text or controls.
"""
import math

DESIGN_WIDTH = 680.0
DESIGN_HEIGHT = 440.0
TARGET_WIDTH_DP = 340.0
TARGET_HEIGHT_DP = 220.0
OUTER_MARGIN_DP = 12.0


def _positive(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def layout(logical_width, logical_height, native_width_dp=None, native_height_dp=None):
    """Return a centered, bounded rectangle and Kodi group-animation attributes.

Without native dp facts, a conservative 2:1 logical-unit fallback is explicitly
marked approximate. It does not pretend to know a device's physical density.
Native dimensions over 2047 are rejected because the current bridge encodes
each dimension in 11 bits. The caller should retry when NativeReady is true.
"""
    width = _positive(logical_width)
    height = _positive(logical_height)
    if width is None or height is None:
        raise ValueError('Preview requires positive, finite window coordinates')
    dp_width = _positive(native_width_dp)
    dp_height = _positive(native_height_dp)
    exact = bool(dp_width and dp_height and dp_width <= 2047 and dp_height <= 2047)
    if not exact:
        dp_width, dp_height = width / 2.0, height / 2.0
    margin = min(OUTER_MARGIN_DP, dp_width / 8.0, dp_height / 8.0)
    fit = min(1.0, (dp_width - 2.0 * margin) / TARGET_WIDTH_DP,
              (dp_height - 2.0 * margin) / TARGET_HEIGHT_DP)
    scale_x = (width / dp_width) * fit / 2.0
    scale_y = (height / dp_height) * fit / 2.0
    panel_width = DESIGN_WIDTH * scale_x
    panel_height = DESIGN_HEIGHT * scale_y
    left, top = (width - panel_width) / 2.0, (height - panel_height) / 2.0
    # Conditional transforms have the same start/end: no motion, no frame delay,
    # and no dependence on the user's optional-animation preference.
    # Kodi postmultiplies its animation matrices. T * S gives zoom about origin
    # followed by centering, so the list MUST put translation before scaling.
    animations = [
        ('Conditional', 'effect=slide start={0:.8f},{1:.8f} end={0:.8f},{1:.8f} '
         'time=0 condition=true'.format(left, top)),
        ('Conditional', 'effect=zoom start={0:.8f},{1:.8f} end={0:.8f},{1:.8f} '
         'center=0,0 time=0 condition=true'.format(scale_x * 100, scale_y * 100)),
    ]
    return {
        'logical_width': width, 'logical_height': height,
        'native_width_dp': dp_width, 'native_height_dp': dp_height,
        'dp_verified': exact, 'fit': fit, 'margin_dp': margin,
        'left': left, 'top': top, 'width': panel_width, 'height': panel_height,
        'width_dp': TARGET_WIDTH_DP * fit, 'height_dp': TARGET_HEIGHT_DP * fit,
        'scale_x': scale_x, 'scale_y': scale_y, 'animations': animations,
    }
