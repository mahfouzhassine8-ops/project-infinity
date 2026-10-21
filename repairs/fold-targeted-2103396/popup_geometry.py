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
    width_fraction = .56 if pw > ph * 1.45 else .90
    card_w = min(width * width_fraction, available_h * 2.75)
    card_h = min(card_w * .35, available_h * .86)
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
    metadata_y = pad + card_w * .060
    metadata_h = card_w * .038
    synopsis_y = metadata_y + metadata_h + gap
    details = {
        'poster': rect(pad, pad, poster_w, poster_h),
        'title': rect(tx, pad, tw-close-gap, card_w*.052),
        'year': rect(tx, metadata_y, tw*.15, metadata_h),
        'certification': rect(tx+tw*.16, metadata_y, tw*.12, metadata_h),
        'runtime': rect(tx+tw*.29, metadata_y, tw*.18, metadata_h),
        'rating': rect(tx+tw*.48, metadata_y, tw*.12, metadata_h),
        'genres': rect(tx+tw*.61, metadata_y, tw*.39, metadata_h),
        'synopsis': rect(tx, synopsis_y, tw, max(0, actions_y-gap-synopsis_y)),
    }
    return dict(x=round((width-card_w)/2), y=round((height-card_h*ratio)/2),
        width=round(card_w), height=round(card_h*ratio), compact=False,
        details=details, surface=rect(0, 0, card_w, card_h),
        close=rect(card_w-pad-close, pad, close, close),
        buttons=[rect(tx+i*(bw+gap), actions_y, bw, button_h) for i in range(4)])
