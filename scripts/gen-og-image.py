#!/usr/bin/env python3
"""
Generate Open Graph social-share images for freestate.party.

Produces 1200x630 PNGs in the brand palette: dark-900 background, gold logo,
Playfair Display wordmark. Run this when the brand assets or copy change, then
commit the resulting PNG(s).

Usage: python3 scripts/gen-og-image.py

Dependencies (already available on the build box):
  - Pillow            (pip)
  - inkscape          (rasterizes site/img/logo.svg)
  - Playfair Display + Inter TTFs — auto-downloaded to /tmp if missing
"""

import os
import subprocess
import urllib.request

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
IMG_DIR = os.path.join(ROOT, 'site', 'img')

W, H = 1200, 630
DARK_900 = (10, 10, 10)
DARK_50 = (250, 250, 249)
DARK_200 = (168, 162, 158)
GOLD_500 = (212, 160, 23)

FONTS = {
    'playfair': (
        '/tmp/PlayfairDisplay.ttf',
        'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf',
    ),
    'inter': (
        '/tmp/Inter.ttf',
        'https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf',
    ),
}


def ensure_font(key):
    path, url = FONTS[key]
    if not os.path.exists(path):
        print(f"  Downloading {key} font...")
        urllib.request.urlretrieve(url, path)
    return path


def load_logo(target_h):
    """Rasterize the gold logo SVG and scale it to target_h pixels tall."""
    tmp = '/tmp/fsp-logo.png'
    subprocess.run(
        ['inkscape', os.path.join(IMG_DIR, 'logo.svg'),
         '--export-type=png', f'--export-filename={tmp}', '--export-width=900'],
        check=True, capture_output=True,
    )
    logo = Image.open(tmp).convert('RGBA')
    scale = target_h / logo.height
    return logo.resize((round(logo.width * scale), target_h), Image.LANCZOS)


def measure(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1], box[0], box[1]


def main():
    playfair = ensure_font('playfair')
    inter = ensure_font('inter')

    wordmark_font = ImageFont.truetype(playfair, 86)
    wordmark_font.set_variation_by_axes([800])
    tagline_font = ImageFont.truetype(inter, 34)
    tagline_font.set_variation_by_axes([14, 400])

    img = Image.new('RGB', (W, H), DARK_900)
    draw = ImageDraw.Draw(img)

    # --- Logo, centered, upper third ---
    logo = load_logo(220)
    logo_x = (W - logo.width) // 2
    logo_y = 70
    img.paste(logo, (logo_x, logo_y), logo)

    # --- Wordmark: "Free State Party" with "Party" in gold ---
    parts = [('Free State ', DARK_50), ('Party', GOLD_500)]
    widths = [measure(draw, t, wordmark_font)[0] for t, _ in parts]
    total_w = sum(widths)
    x = (W - total_w) // 2
    wordmark_y = logo_y + logo.height + 36
    for (text, color), w in zip(parts, widths):
        draw.text((x, wordmark_y), text, font=wordmark_font, fill=color)
        x += w

    # --- Gold divider ---
    _, wm_h, _, wm_oy = measure(draw, 'Free State Party', wordmark_font)
    divider_y = wordmark_y + wm_oy + wm_h + 34
    draw.rectangle([(W // 2 - 60, divider_y), (W // 2 + 60, divider_y + 3)], fill=GOLD_500)

    # --- Tagline ---
    tagline = 'A private club for free men in New Hampshire.'
    tw, th, ox, oy = measure(draw, tagline, tagline_font)
    draw.text(((W - tw) // 2 - ox, divider_y + 30 - oy), tagline,
              font=tagline_font, fill=DARK_200)

    out = os.path.join(IMG_DIR, 'og-default.png')
    img.save(out)
    print(f"  Wrote: {os.path.relpath(out, ROOT)} ({W}x{H})")


if __name__ == '__main__':
    main()
