def geometry(width, height, physical_width='', physical_height=''):
    """One horizontal poster/details/actions layout in the real skin canvas.

    Convert both axes through the observed viewport to keep the poster and card
    proportions on the Fold cover and inner display. No playback geometry changes.
    """
    width, height = max(1, int(width)), max(1, int(height))
    try:
        pw, ph = int(physical_width), int(physical_height)
        if pw < 200 or ph < 200:
            raise ValueError('viewport unavailable')
    except (TypeError, ValueError):
        pw, ph = width, height
    # Work in horizontal canvas units, then map vertical units independently.
    ratio = (height * pw) / (width * ph)
    available_h = height / ratio
    card_w = min(width * .90, available_h * 2.75)
    card_h = min(card_w * .47, available_h * .86)
    pad = card_w * .025
    gap = card_w * .025
    close = card_w * .060
    button_h = card_w * .072
    poster_h = card_h - 2 * pad
    poster_w = poster_h * (2 / 3)
    tx = pad + poster_w + gap
    tw = card_w - tx - pad
    actions_y = card_h - pad - button_h
    bw = (tw - 3 * gap) / 4
    def rect(x, y, w, h):
        return tuple(round(v) for v in (x, y * ratio, w, h * ratio))
    details = {
        'poster': rect(pad, pad, poster_w, poster_h),
        'title': rect(tx, pad, tw-close-gap, card_w*.062),
        'year': rect(tx, pad+card_w*.065, tw, card_w*.042),
        'certification': rect(tx, pad+card_w*.112, tw*.25, card_w*.038),
        'runtime': rect(tx+tw*.26, pad+card_w*.112, tw*.35, card_w*.038),
        'rating': rect(tx+tw*.64, pad+card_w*.112, tw*.36, card_w*.038),
        'genres': rect(tx, pad+card_w*.155, tw, card_w*.043),
        'synopsis': rect(tx, pad+card_w*.202, tw,
                         max(0, actions_y-gap-pad-card_w*.202)),
    }
    return dict(x=round((width-card_w)/2), y=round((height-card_h*ratio)/2),
        width=round(card_w), height=round(card_h*ratio), compact=False,
        details=details, surface=rect(0, 0, card_w, card_h),
        close=rect(card_w-pad-close, pad, close, close),
        buttons=[rect(tx+i*(bw+gap), actions_y, bw, button_h) for i in range(4)])
