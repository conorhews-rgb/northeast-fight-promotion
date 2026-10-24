#!/usr/bin/env python3
"""Render a "WHO YA GOT TONIGHT?" pick-a-side post, 1080x1350.

Two fighters side by side, red corner on the left, heads aligned, with the
bout line under the headline and names and gyms beneath each fighter.
Type is the site's Barlow Condensed.

Run from the repo root:
    python3 tools/make-who-ya-got.py LEFT.jpg "LEFT NAME" "LEFT GYM" \\
        RIGHT.jpg "RIGHT NAME" "RIGHT GYM" "BOUT LINE" OUT.png
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

lp, ln, lg, rp, rn, rg, bout, out = sys.argv[1:9]
W, H = 1080, 1350
F = "assets/fonts/BarlowCondensed-{}-latin.woff2"
def font(w, px): return ImageFont.truetype(F.format(w), int(px))
WHITE, MUTED, GREEN, GREEN_DK = (255, 255, 255), (164, 172, 166), (22, 194, 22), (15, 154, 15)

HEAD_Y = 352          # where the top of each head lands
PHOTO_W = 770         # width each photo is scaled to before cropping
BODY_BOTTOM = 1205    # photos fade out by here

img = Image.new("RGB", (W, H), (0, 0, 0)).convert("RGBA")

def place(path, half):
    ph = Image.open(path).convert("RGB")
    a = np.asarray(ph.convert("L")).astype(int) > 35
    top = np.where(a.sum(axis=1) > 15)[0].min()
    head = np.where(a[top:top + 250].sum(axis=0) > 5)[0]
    cx = (head.min() + head.max()) / 2
    s = PHOTO_W / ph.width
    ph = ph.resize((PHOTO_W, round(ph.height * s)), Image.LANCZOS)
    x0 = round(cx * s - W / 4)                      # centre the head in its half
    y0 = round(top * s - HEAD_Y)
    crop = ph.crop((x0, y0, x0 + W // 2, y0 + BODY_BOTTOM)).convert("RGBA")
    # fade the foot and the inner edge so the halves meet softly
    m = Image.new("L", crop.size, 255); md = m.load()
    for y in range(crop.height):
        fy = min(1, max(0, (BODY_BOTTOM - y) / 230))
        for x in range(crop.width):
            edge = x if half == "r" else crop.width - 1 - x
            fx = min(1, edge / 70)
            md[x, y] = int(255 * fy * fx)
    img.alpha_composite(Image.composite(crop, Image.new("RGBA", crop.size, (0, 0, 0, 0)), m),
                        (0 if half == "l" else W // 2, 0))

place(lp, "l"); place(rp, "r")

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)

def fit(text, weight, px, maxw):
    while px > 10 and d.textlength(text, font=font(weight, px)) > maxw: px -= 1
    return font(weight, px)

def say(xy, text, f, fill, anchor="mt", shadow=True):
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 2, xy[1] + 3), text, font=f, fill=(0, 0, 0, 230), anchor=anchor)
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text(xy, text, font=f, fill=fill, anchor=anchor)

# top: logo, headline, bout line
logo = Image.open("assets/img/nfp-logo-alpha.png").convert("RGBA")
lw = 120; lh = int(lw * logo.height / logo.width)
layer.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), ((W - lw) // 2, 22))
fh = font("800i", 100)
a, b = "WHO YA GOT ", "TONIGHT?"
tw = d.textlength(a, font=fh) + d.textlength(b, font=fh)
x = (W - tw) / 2
say((x, 150), a, fh, WHITE, "lt")
say((x + d.textlength(a, font=fh), 150), b, fh, GREEN, "lt")
say((W / 2, 262), bout, fit(bout, "700", 27, W - 120), MUTED)

# centre: VS on a short green rule
d.rectangle((W / 2 - 2, 470, W / 2 + 2, 560), fill=GREEN_DK)
d.rectangle((W / 2 - 2, 680, W / 2 + 2, 770), fill=GREEN_DK)
say((W / 2, 620), "VS", font("800i", 92), WHITE, "mm")

# names and gyms
for cx, name, gym in ((W / 4, ln, lg), (3 * W / 4, rn, rg)):
    say((cx, 1138), name, fit(name, "800i", 70, W / 2 - 50), WHITE)
    say((cx, 1218), gym, fit(gym, "700", 27, W / 2 - 60), MUTED)

say((W / 2, 1284), "COMMENT YOUR PICK", font("800i", 26), GREEN)

img.alpha_composite(layer)
img.convert("RGB").save(out, optimize=True)
print(f"wrote {out} ({W}x{H})")
