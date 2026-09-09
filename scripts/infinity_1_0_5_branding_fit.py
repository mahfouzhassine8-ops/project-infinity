#!/usr/bin/env python3
# Infinity 1.0.5 surgical branding fit
from __future__ import annotations
import argparse, io, json, zipfile
from pathlib import Path
from PIL import Image, ImageDraw
import infinity_1_0_4_responsive_branding as v104
import infinity_1_0_3_reference_ui as base

# Keep 1.0.4 home/typography behavior; only correct branding artwork geometry.

def make_sidebar_logo(src_icon, light=False):
    out = Image.new('RGBA', (360, 230), (0,0,0,0))
    # Deliberately smaller symbol with real separation from wordmark.
    sym = base._fit_symbol(src_icon, 230)
    out.alpha_composite(sym, ((360-sym.width)//2, 0))
    d = ImageDraw.Draw(out)
    color=(15,22,30,255) if light else (246,249,252,255)
    base._draw_centered_text(d, 174, 'I N F I N I T Y', base._font(25), color, 360)
    return out


def make_splash(src_icon, light=False, size=(1920,1080)):
    # Landscape-safe master with a compact centered branding block.
    # Important: all branding lives well inside the central portrait-safe region,
    # so Android/Kodi center-crop cannot cut the emblem/wordmark on the Fold cover screen.
    bg=(248,251,255) if light else (0,0,0)
    out=Image.new('RGB',size,bg)
    d=ImageDraw.Draw(out)
    color=(15,22,30) if light else (248,250,252)
    accent=(0,119,222) if light else (77,202,255)
    sym=base._fit_symbol(src_icon, 330)
    x=(size[0]-sym.width)//2
    out.paste(sym,(x,245),sym)
    base._draw_centered_text(d, 570, 'I N F I N I T Y', base._font(58), color, size[0])
    base._draw_centered_text(d, 665, 'Y O U R   M E D I A .   Y O U R   W A Y .', base._font(19), accent, size[0])
    return out

v104.make_sidebar_logo=make_sidebar_logo
v104.make_splash=make_splash
base.make_sidebar_logo=make_sidebar_logo
base.make_splash=make_splash

def main():
    p=argparse.ArgumentParser(); p.add_argument('src',type=Path); p.add_argument('out',type=Path); p.add_argument('receipt',type=Path)
    a=p.parse_args(); v104.base.build(a.src,a.out,a.receipt)

if __name__=='__main__': main()
