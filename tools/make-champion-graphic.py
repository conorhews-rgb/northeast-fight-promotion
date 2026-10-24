#!/usr/bin/env python3
"""Render an "AND NEW" champion announcement, 1080x1350 for Instagram.

Photo fills the frame, the NFP logo sits above the champion's head, and the
announcement reads up from the foot of the frame the way a ring announcer
calls it: AND NEW, the title, then the name, biggest of all. Type is the
site's Barlow Condensed.

Run from the repo root:
    python3 tools/make-champion-graphic.py PHOTO "TITLE LINE 1" "TITLE LINE 2" "NAME" OUT.png
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

photo_path, line1, line2, name, out = sys.argv[1:6]
W, H = 1080, 1350
F = "assets/fonts/BarlowCondensed-{}-latin.woff2"
def font(w, px): return ImageFont.truetype(F.format(w), int(px))
WHITE, GREEN, GREEN_DK = (255, 255, 255), (22, 194, 22), (15, 154, 15)

# photo: fit to width, top aligned, on black
ph = Image.open(photo_path).convert("RGB")
s = W / ph.width
ph = ph.resize((W, round(ph.height * s)), Image.LANCZOS)
# lift the photo so the belt clears the type; the black above the head absorbs it
LIFT = 75
img = Image.new("RGB", (W, H), (0, 0, 0))
img.paste(ph.crop((0, LIFT, W, min(ph.height, H + LIFT))), (0, 0))

# fade the foot to black so the type sits on a clean ground
fade = Image.new("L", (1, H))
for y in range(H):
    t = (y - 820) / 330
    fade.putpixel((0, y), int(255 * min(1, max(0, t)) ** 1.4))
img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, fade.resize((W, H))).convert("RGBA")

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)

def fit(text, weight, px, maxw):
    while px > 10 and d.textlength(text, font=font(weight, px)) > maxw: px -= 1
    return font(weight, px)

def centred(y, text, f, fill, shadow=True):
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((W / 2 + 2, y + 3), text, font=f, fill=(0, 0, 0, 220), anchor="mt")
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    d.text((W / 2, y), text, font=f, fill=fill, anchor="mt")

# logo above the head
logo = Image.open("assets/img/nfp-logo-alpha.png").convert("RGBA")
lw = 190; lh = int(lw * logo.height / logo.width)
layer.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), (36, 34))

# announcement, bottom up
maxw = W - 120
fn = fit(name, "800i", 150, maxw)
centred(1160, name, fn, WHITE)
ft = fit(max(line1, line2, key=len), "800i", 70, maxw)
centred(1004, line1, ft, WHITE)
centred(1074, line2, ft, WHITE)
# AND NEW, flanked by short green rules
fa = font("800i", 46)
centred(944, "AND NEW", fa, GREEN)
tw = d.textlength("AND NEW", font=fa)
for x0, x1 in ((W / 2 - tw / 2 - 86, W / 2 - tw / 2 - 22), (W / 2 + tw / 2 + 22, W / 2 + tw / 2 + 86)):
    d.rectangle((x0, 966, x1, 970), fill=GREEN_DK)

img.alpha_composite(layer)
img.convert("RGB").save(out, optimize=True)
print(f"wrote {out} ({W}x{H})")
