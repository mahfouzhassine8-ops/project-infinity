"""Rail dialog geometry in Kodi coordinates, using published app-window dp bounds."""
import math


def positive(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value > 0 else None


def layout(width, height, native_width=None, native_height=None, count=5):
    width, height = positive(width), positive(height)
    if not width or not height:
        raise ValueError('Rail dialog requires valid window coordinates.')
    dw, dh = positive(native_width), positive(native_height)
    exact = bool(dw and dh and dw <= 2047 and dh <= 2047)
    if not exact:
        dw, dh = width / 2, height / 2
    # Keep full-size touch rows whenever the viewport permits. Short windows page
    # the action list instead of clipping controls or making the panel taller.
    capacity = min(5, max(1, int((dh - 24 - 80 - 10) / 50)))
    if count > capacity:
        capacity = min(5, max(1, int((dh - 24 - 80 - 56) / 50)))
    rows = min(count, capacity)
    paged = count > capacity
    design_height = 160 + rows * 100 + (112 if paged else 20)
    design_width = 760
    margin = min(12, dw / 8, dh / 8)
    fit = min(1, (dw - 2 * margin) / (design_width / 2),
              (dh - 2 * margin) / (design_height / 2))
    sx, sy = width / dw * fit / 2, height / dh * fit / 2
    pw, ph = design_width * sx, design_height * sy
    x, y = (width - pw) / 2, (height - ph) / 2
    return dict(width=pw, height=ph, left=x, top=y, capacity=capacity,
                rows=rows, paged=paged, design_height=design_height,
                width_dp=design_width / 2 * fit, height_dp=design_height / 2 * fit,
                dp_verified=exact, fit=fit, animations=[
                    ('Conditional', 'effect=slide start={0:.8f},{1:.8f} end={0:.8f},{1:.8f} time=0 condition=true'.format(x, y)),
                    ('Conditional', 'effect=zoom start={0:.8f},{1:.8f} end={0:.8f},{1:.8f} center=0,0 time=0 condition=true'.format(sx * 100, sy * 100))])
