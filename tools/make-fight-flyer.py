#!/usr/bin/env python3
"""Render an NFP 2 fight flyer: two fighters over the Sheraton at night.

The house layout from the Kim vs Cetoute flyer. Top: NFP 2, date, venue, with
the hotel's towers between the fighters. Fighters stand either side of a green
VS and fade out at the waist. Under them the bout line, then each name at the
sides with the weight and glove size between them (a title fight puts the belt
there instead). The sponsor row closes it, as on every NFP poster. "NFP 2" is
Arial Black to match the logo; all other lettering is Versa Versa
(~/Library/Fonts/Versa-Versa.otf).

Fighter cutouts are transparent WebPs in assets/img/poster-src/. Each entry
gives the eye line and face centre in the cutout's own pixels and a scale, so
both faces land the same size on the same line.

Run from the repo root:
    python3 tools/make-fight-flyer.py OUT.png            1080x1350 feed
    python3 tools/make-fight-flyer.py --story OUT.png    1080x1920 story
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
from sponsor_row import sponsor_row

STORY = "--story" in sys.argv
out = [a for a in sys.argv[1:] if not a.startswith("--")][0]
SRC = "assets/img/poster-src/"
W, H = 1080, 1920 if STORY else 1350
VERSA = os.path.expanduser("~/Library/Fonts/Versa-Versa.otf")
ARIAL_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
def versa(px): return ImageFont.truetype(VERSA, int(px))

# ---------------------------------------------------------------- the fight
BOUT = ("PROFESSIONAL ", "KICKBOXING")                  # white run, green run
MID = ("135 LBS", "4 OZ GLOVES")                        # between the names, where a title fight has the belt
FIGHTERS = [  # left, right. eye / cx are in the cutout's pixels; scale sets eye-to-chin near 102 px on the feed
    dict(first="LIAM", last="MACNEIL", gym="KTA NASHUA", code="MACNEIL", img="nfp2-liam-macneil.webp",
         eye=261.5, cx=458, scale=0.52, contrast=1.06, bright=0.97, sat=0.96, tint=(1.0, 1.0, 1.0)),
    dict(first="JOSH", last="VILLEGES", gym="RECON MMA", code="VILLEGES", img="nfp2-josh-villeges.webp",
         eye=336, cx=464, scale=0.44, contrast=1.10, bright=0.92, sat=0.84, tint=(0.97, 1.0, 1.05)),   # phone flash, cooled to match
]

# ---------------------------------------------------------------- layout
if STORY:
    TITLE_PX, TITLE_Y = 150, 400       # cap tops at y 293, under the story header
    DATE_Y, VENUE_Y, T = 470, 512, 1.1 # T scales the lettering
    EYE_Y, K, FIGHTER_CX = 716, 1.06, (256, 810)
    FADE0, FADE1 = 1160, 1286          # fighters dissolve at the waist
    VS_Y, BOUT_Y, MID_CY, NAME_CX = 1118, 1334, 1490, 160
    HOTEL_S, HOTEL_TOWER_Y, HOTEL_FADE0, HOTEL_FADE1 = 0.95, 520, 860, 1160
    LOGO_CY = 1712                     # sponsor row ends at y 1764, above the reply bar
    HAZE_CY, GLOW_CY, DARK_Y, BEAM_H = 420, 1520, 1300, 1300
else:
    TITLE_PX, TITLE_Y = 130, 134
    DATE_Y, VENUE_Y, T = 196, 232, 1.0
    EYE_Y, K, FIGHTER_CX = 370, 1.0, (262, 800)
    FADE0, FADE1 = 805, 925
    VS_Y, BOUT_Y, MID_CY, NAME_CX = 712, 920, 1062, 162
    HOTEL_S, HOTEL_TOWER_Y, HOTEL_FADE0, HOTEL_FADE1 = 0.85, 236, 500, 740
    LOGO_CY = 1264
    HAZE_CY, GLOW_CY, DARK_Y, BEAM_H = 130, 1090, 900, 900
NAME_W = 256                           # last names shrink to fit this


# ---------------------------------------------------------------- helpers
def arr(im): return np.asarray(im.convert("RGB"), dtype=np.float32) / 255
def img_of(a): return Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))


def radial(cx, cy, rx, ry, power=2.0):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    return np.clip(1 - d, 0, 1) ** power


def screen(base, color, amount):
    c = np.array(color, np.float32)[None, None, :] / 255 * amount[..., None]
    return 1 - (1 - base) * (1 - c)


def vgrad(h, top, bottom):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    g = np.array(top, np.float32) * (1 - t) + np.array(bottom, np.float32) * t
    return Image.fromarray(np.repeat(g, W, axis=1).astype(np.uint8))


def fill_with(mask, top, bottom):
    bb = mask.getbbox()
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(vgrad(bb[3] - bb[1], top, bottom).convert("RGBA"), (0, bb[1]))
    layer.putalpha(mask)
    return layer


def shadow(mask, dx, dy, blur, opacity, color=(0, 0, 0)):
    m = ImageChops.offset(mask, dx, dy).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", (W, H), color + (0,))
    layer.putalpha(m.point(lambda v: int(v * opacity)))
    return layer


def text_mask(runs, x, y, track=0.0):
    masks = []
    for t, f in runs:
        m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
        for ch in t:
            md.text((x, y), ch, font=f, fill=255, anchor="ls")
            x += md.textlength(ch, font=f) + (track if ch != " " else -track * .5)
        masks.append(m)
    full = masks[0]
    for m in masks[1:]: full = ImageChops.lighter(full, m)
    return full, masks


def width_of(runs, track=0.0):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return sum(d.textlength(t, font=f) for t, f in runs) + track * (sum(len(t) for t, _ in runs) - 1)


def cap(f): return -f.getbbox("H", anchor="ls")[1]

WHITE, SOFT, GREEN = ((255, 255, 255), (214, 218, 216)), ((204, 211, 206), (172, 180, 174)), ((70, 230, 70), (16, 156, 16))


def put_text(img, runs, x, y, align="c", deep=True, halo=False):
    """runs: [(text, font, (top, bottom))] on one baseline; align l / c / r about x."""
    plain = [(t, f) for t, f, _ in runs]
    w = width_of(plain)
    x = x - w / 2 if align == "c" else x - w if align == "r" else x
    full, masks = text_mask(plain, x, y)
    if halo:                                            # dark cloud so lettering holds over a photo
        img.alpha_composite(shadow(full.filter(ImageFilter.MaxFilter(9)), 0, 0, 20, 0.8))
    img.alpha_composite(shadow(full, 0, 7 if deep else 4, 11 if deep else 6, 0.85))
    img.alpha_composite(shadow(full, 0, 3, 2, 0.9))
    for m, (_, _, (top, bottom)) in zip(masks, runs):
        img.alpha_composite(fill_with(m, top, bottom))
    return full


def fit(text, px, max_w):
    while width_of([(text, versa(px))]) > max_w: px -= 1
    return versa(px)


# ---------------------------------------------------------------- background
art = Image.open(SRC + "nfp2-hotel-cage.jpg").convert("RGB")
k = max(W / art.width, H / art.height)
bg = art.resize((round(art.width * k), round(art.height * k)), Image.LANCZOS)
bx, by = (bg.width - W) // 2, (bg.height - H) // 2
bg = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(40))
base = arr(ImageEnhance.Brightness(bg).enhance(0.30))

hotel = Image.open(SRC + "sheraton-night.webp").convert("RGB")
hotel = hotel.resize((round(hotel.width * HOTEL_S), round(hotel.height * HOTEL_S)), Image.LANCZOS)
hotel = hotel.filter(ImageFilter.UnsharpMask(radius=1.2, percent=50, threshold=2))
hotel = ImageEnhance.Brightness(hotel).enhance(0.84)
hx = round(W / 2 - 655 * HOTEL_S)                      # tower centre is source x=655
hy = round(HOTEL_TOWER_Y - 195 * HOTEL_S)              # tower tops are source y=195
canvas = Image.new("RGB", (W, H)); canvas.paste(hotel, (hx, hy))
ys = np.arange(H, dtype=np.float32)
ha = np.clip((ys - hy) / 130, 0, 1) * np.clip((HOTEL_FADE1 - ys) / (HOTEL_FADE1 - HOTEL_FADE0), 0, 1) ** 1.2
ha[(ys < hy) | (ys >= hy + hotel.height)] = 0
base = base * (1 - ha[:, None, None]) + arr(canvas) * ha[:, None, None]

beams = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(beams)
for x0, x1, spread in ((-40, 250, 120), (200, 330, 150), (880, 750, 150), (1120, 830, 120), (540, 540, 210)):
    bd.polygon([(x0 - 14, -60), (x0 + 14, -60), (x1 + spread, BEAM_H), (x1 - spread, BEAM_H)], fill=70)
beams = np.asarray(beams.filter(ImageFilter.GaussianBlur(38)), dtype=np.float32) / 255
beams *= np.clip(1 - ys / BEAM_H, 0, 1)[:, None] ** 1.2
base = screen(base, (150, 205, 165), beams * 0.55)
base = screen(base, (34, 62, 40), radial(W / 2, HAZE_CY, 620, 230, 1.6) * 0.95)   # haze behind the top block
yy, xx = np.mgrid[0:H, 0:W]
vig = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
base = base * (1 - 0.38 * np.clip((vig - 0.6) / 0.6, 0, 1) ** 1.5)[..., None]
img = img_of(base).convert("RGBA")

# ---------------------------------------------------------------- fighters
fade = np.clip((FADE1 - ys) / (FADE1 - FADE0), 0, 1) ** 1.3
for f, cx in zip(FIGHTERS, FIGHTER_CX):
    cut = Image.open(SRC + f["img"]).convert("RGBA")
    s = f["scale"] * K
    cut = cut.resize((round(cut.width * s), round(cut.height * s)), Image.LANCZOS)
    rgb = ImageEnhance.Color(cut.convert("RGB")).enhance(f["sat"])
    rgb = Image.merge("RGB", [c.point(lambda v, m=m: min(255, int(v * m))) for c, m in zip(rgb.split(), f["tint"])])
    rgb = ImageEnhance.Contrast(ImageEnhance.Brightness(rgb).enhance(f["bright"])).enhance(f["contrast"])
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = round(cx - f["cx"] * s), round(EYE_Y - f["eye"] * s)
    layer.paste(Image.merge("RGBA", (*rgb.split(), cut.getchannel("A"))), (x, y))
    a = np.asarray(layer.getchannel("A"), dtype=np.float32) * fade[:, None]
    alpha = Image.fromarray(a.astype(np.uint8))
    layer.putalpha(alpha)
    img.alpha_composite(shadow(alpha, 0, 10, 34, 0.42)) # soft dark halo lifts them off the hotel
    img.alpha_composite(layer)

# floor: the fighters and the hotel sink into near-black, with green pooled behind the lower block
a = arr(img)
a = a * (1 - 0.90 * np.clip((ys - DARK_Y) / 130, 0, 1) * np.clip(1 - (ys - DARK_Y - 130) / 2000, 0, 1))[:, None, None]
a = screen(a, (22, 110, 38), radial(W / 2, GLOW_CY, 560, 190, 1.6) * 0.42)
img = img_of(a).convert("RGBA")

# ---------------------------------------------------------------- top block
ft = ImageFont.truetype(ARIAL_BLACK, TITLE_PX)
track = -0.03 * TITLE_PX
runs = [("NF", ft), ("P 2", ft)]
full, (white_m, green_m) = text_mask(runs, (W - width_of(runs, track)) / 2, TITLE_Y, track)
img.alpha_composite(shadow(full, 0, 13, 19, 0.70))
img.alpha_composite(shadow(full, 0, 5, 4, 0.85))
img.alpha_composite(shadow(green_m, 0, 0, 22, 0.34, (22, 194, 22)))
img.alpha_composite(fill_with(white_m, (255, 255, 255), (206, 211, 208)))
img.alpha_composite(fill_with(green_m, (58, 222, 58), (14, 152, 14)))
edge = ImageChops.subtract(full, ImageChops.offset(full, 0, 2)).point(lambda v: int(v * 0.45))
hl = Image.new("RGBA", (W, H), (255, 255, 255, 0)); hl.putalpha(edge); img.alpha_composite(hl)
put_text(img, [("SATURDAY MARCH 27", versa(50 * T), WHITE)], W / 2, DATE_Y)
put_text(img, [("SHERATON HOTEL  |  NASHUA, NH", versa(28 * T), SOFT)], W / 2, VENUE_Y, deep=False)

# ---------------------------------------------------------------- VS, bout line, names
put_text(img, [("VS", versa(64 * T), GREEN)], W / 2, VS_Y, halo=True)
put_text(img, [(BOUT[0], versa(40 * T), WHITE), (BOUT[1], versa(40 * T), GREEN)], W / 2, BOUT_Y, halo=True)

f_first, f_gym, f_code = versa(36 * T), versa(27 * T), versa(26 * T)
for f, cx in zip(FIGHTERS, (NAME_CX, W - NAME_CX)):
    f_last = fit(f["last"], round(63 * T), NAME_W)
    lines = [(f["first"], f_first, SOFT, 16 * T), (f["last"], f_last, WHITE, 16 * T)]
    if f["gym"]: lines.append((f["gym"], f_gym, GREEN, 14 * T))
    if f["code"]: lines.append(("CODE: " + f["code"], f_code, SOFT, 0))
    total = sum(cap(fn) for _, fn, _, _ in lines) + sum(g for *_, g in lines[:-1])
    y = MID_CY - total / 2                               # the block is centred on the middle line
    for i, (t, fn, col, gap) in enumerate(lines):
        y += cap(fn)
        put_text(img, [(t, fn, col)], cx, y, deep=(i == 1), halo=True)
        y += gap

f_mid, f_sub = versa(86 * T), versa(34 * T)             # weight and gloves, centred between the names
gap = 20 * T
top = MID_CY - (cap(f_mid) + gap + cap(f_sub)) / 2
put_text(img, [(MID[0], f_mid, WHITE)], W / 2, top + cap(f_mid))
put_text(img, [(MID[1], f_sub, GREEN)], W / 2, top + cap(f_mid) + gap + cap(f_sub), deep=False)

sponsors, _, _ = sponsor_row(W, H, LOGO_CY)
img.alpha_composite(sponsors)

rng = np.random.default_rng(27)
g = arr(img) + rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
img_of(g).save(out, optimize=True)
print("wrote", out)
