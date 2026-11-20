#!/usr/bin/env python3
"""Render the NFP 2 sponsor announcement: sponsorships are open, no pricing.

1080x1350 for the feed, or 1080x1920 for stories with --story (lettering stays
inside the story safe zone, clear of the top and bottom interface).

The opener to make-sponsor-tiers.py and built on the same backdrop: the Sheraton
at night over a blurred copy of the hotel-and-cage art (both in
assets/img/poster-src/). Top: NFP 2, SPONSORSHIPS NOW OPEN, date and venue, with
the hotel beneath. Then a grid of perks a package can include, the CTA and the current
sponsors' row. "NFP 2" is Arial Black
to match the logo; all other lettering is Versa Versa
(~/Library/Fonts/Versa-Versa.otf). Edit PERKS to change the benefits shown.

Run from the repo root:
    python3 tools/make-sponsor-call.py OUT.png
    python3 tools/make-sponsor-call.py --story OUT.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
from sponsor_row import sponsor_row

STORY = "--story" in sys.argv
out = [a for a in sys.argv[1:] if not a.startswith("--")][0]
hotel_path = "assets/img/poster-src/sheraton-night.webp"
art_path = "assets/img/poster-src/nfp2-hotel-cage.jpg"
W, H = 1080, 1920 if STORY else 1350
VERSA = os.path.expanduser("~/Library/Fonts/Versa-Versa.otf")
ARIAL_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
def versa(px): return ImageFont.truetype(VERSA, int(px))

HEAD = ("SPONSORSHIPS ", "NOW OPEN")
INFO = "SATURDAY MARCH 27  |  SHERATON HOTEL  |  NASHUA, NH"
LABEL = "SPONSOR PERKS CAN INCLUDE"       # perks depend on the sponsor level, so never promise all of them
PERKS = [  # (green kicker, white line), read left to right, top to bottom
    ("YOUR LOGO", "ON THE CANVAS"),
    ("YOUR LOGO", "ON EVERY POSTER"),
    ("IN RING", "MC ANNOUNCEMENTS"),
    ("TICKETS AND", "FRONT ROW SEATS"),
    ("DEDICATED", "SOCIAL MEDIA POSTS"),
    ("YOUR OWN", "TABLE AT THE EVENT"),
]
CTA = ("DM US TO ", "GET INVOLVED")

# layout
COL_X = ((50, 532), (548, 1030))
if STORY:
    TITLE_PX, TITLE_Y = 150, 400       # cap tops at y 293, under the story header
    HEAD_Y, INFO_Y, INFO_PX = 484, 526, 28
    HOTEL_S, HOTEL_TOWER_Y = 1.0, 540
    HOTEL_FADE0, HOTEL_FADE1 = 900, 1200
    LABEL_Y, GRID_Y0 = 1046, 1076
    TILE_H, TILE_GAP = 122, 18
    KICK_PX, MAIN_PX, CTA_PX = 26, 40, 52
    LOGO_CY = 1712                     # sponsor row ends at y 1764, above the reply bar
    HAZE_CY, GLOW_CY, DARK_Y, BEAM_H = 420, 1280, 1524, 1300
else:
    TITLE_PX, TITLE_Y = 112, 112
    HEAD_Y, INFO_Y, INFO_PX = 176, 212, 26   # headline, then date and venue
    HOTEL_S, HOTEL_TOWER_Y = 0.90, 222   # venue photo scale; tower tops land just under the info line
    HOTEL_FADE0, HOTEL_FADE1 = 520, 800  # the hotel dissolves behind the perk grid
    LABEL_Y, GRID_Y0 = 668, 694
    TILE_H, TILE_GAP = 106, 16
    KICK_PX, MAIN_PX, CTA_PX = 24, 38, 48
    LOGO_CY = 1264
    HAZE_CY, GLOW_CY, DARK_Y, BEAM_H = 130, 860, 1090, 900   # top haze, green pool, dark floor, light beams


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


def put_text(img, runs, x, y, align="c", deep=True):
    """runs: [(text, font, (top, bottom))] on one baseline; align l / c / r about x."""
    plain = [(t, f) for t, f, _ in runs]
    w = width_of(plain)
    x = x - w / 2 if align == "c" else x - w if align == "r" else x
    full, masks = text_mask(plain, x, y)
    img.alpha_composite(shadow(full, 0, 7 if deep else 4, 11 if deep else 6, 0.85))
    img.alpha_composite(shadow(full, 0, 3, 2, 0.9))
    for m, (_, _, (top, bottom)) in zip(masks, runs):
        img.alpha_composite(fill_with(m, top, bottom))
    return full


def fit(texts, px, max_w):
    """Largest size up to px at which every string fits max_w."""
    while max(width_of([(t, versa(px))]) for t in texts) > max_w: px -= 1
    return px


# ---------------------------------------------------------------- background (as on the fight flyer)
art = Image.open(art_path).convert("RGB")
k = max(W / art.width, H / art.height)                  # cover the canvas
bg = art.resize((round(art.width * k), round(art.height * k)), Image.LANCZOS)
bx, by = (bg.width - W) // 2, (bg.height - H) // 2
bg = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(40))
base = arr(ImageEnhance.Brightness(bg).enhance(0.30))

hotel = Image.open(hotel_path).convert("RGB")
hotel = hotel.resize((round(hotel.width * HOTEL_S), round(hotel.height * HOTEL_S)), Image.LANCZOS)
hotel = hotel.filter(ImageFilter.UnsharpMask(radius=1.2, percent=50, threshold=2))
hotel = ImageEnhance.Brightness(hotel).enhance(0.88)
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

base = screen(base, (34, 62, 40), radial(W / 2, HAZE_CY, 620, 230, 1.6) * 0.95)       # haze behind the top block
base = screen(base, (26, 104, 40), radial(W / 2, GLOW_CY, 620, 400, 1.7) * 0.42)      # green pooled behind the perk grid
base = base * (1 - 0.88 * np.clip((ys - DARK_Y) / 110, 0, 1))[:, None, None]        # near-black behind CTA and sponsors
yy, xx = np.mgrid[0:H, 0:W]
vig = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
base = base * (1 - 0.38 * np.clip((vig - 0.6) / 0.6, 0, 1) ** 1.5)[..., None]
img = img_of(base).convert("RGBA")

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
f_head = versa(fit(["".join(HEAD)], 64, 960))
put_text(img, [(HEAD[0], f_head, WHITE), (HEAD[1], f_head, GREEN)], W / 2, HEAD_Y)
put_text(img, [(INFO, versa(INFO_PX), SOFT)], W / 2, INFO_Y, deep=False)

# ---------------------------------------------------------------- perk grid
f_label = versa(26)
lw = width_of([(LABEL, f_label)])
put_text(img, [(LABEL, f_label, SOFT)], W / 2, LABEL_Y, deep=False)
rules = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rules)
ry = LABEL_Y - cap(f_label) / 2
rd.line((COL_X[0][0], ry, W / 2 - lw / 2 - 22, ry), fill=(255, 255, 255, 70), width=1)
rd.line((W / 2 + lw / 2 + 22, ry, COL_X[1][1], ry), fill=(255, 255, 255, 70), width=1)
img.alpha_composite(rules)

tile_w = COL_X[0][1] - COL_X[0][0]
f_kick = versa(fit([k for k, _ in PERKS], KICK_PX, tile_w - 60))
f_main = versa(fit([m for _, m in PERKS], MAIN_PX, tile_w - 60))
for i, (kick, main) in enumerate(PERKS):
    x0, x1 = COL_X[i % 2]
    y0 = GRID_Y0 + (i // 2) * (TILE_H + TILE_GAP); y1 = y0 + TILE_H
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    panel = Image.new("L", (W, H), 0); ImageDraw.Draw(panel).rounded_rectangle((x0, y0, x1, y1), 9, fill=255)
    img.alpha_composite(shadow(panel, 0, 10, 16, 0.7))
    frost = Image.blend(img.filter(ImageFilter.GaussianBlur(14)), Image.new("RGBA", (W, H), (5, 9, 7, 255)), 0.66)
    img.paste(frost, (0, 0), panel)
    rim = Image.new("L", (W, H), 0); ImageDraw.Draw(rim).rounded_rectangle((x0, y0, x1, y1), 9, outline=255, width=1)
    rl = Image.new("RGBA", (W, H), (255, 255, 255, 0)); rl.putalpha(rim.point(lambda v: int(v * .22))); img.alpha_composite(rl)
    gap = 14                                            # kicker over main line, centred as a pair
    top = cy - (cap(f_kick) + gap + cap(f_main)) / 2
    put_text(img, [(kick, f_kick, GREEN)], cx, top + cap(f_kick), deep=False)
    put_text(img, [(main, f_main, WHITE)], cx, top + cap(f_kick) + gap + cap(f_main), deep=False)
GRID_Y1 = GRID_Y0 + ((len(PERKS) + 1) // 2) * (TILE_H + TILE_GAP) - TILE_GAP

# ---------------------------------------------------------------- CTA and current sponsors
sponsors, SPONSOR_TOP, _ = sponsor_row(W, H, LOGO_CY)
f_cta = versa(CTA_PX)                                   # centred between the grid and the sponsor row
put_text(img, [(CTA[0], f_cta, WHITE), (CTA[1], f_cta, GREEN)], W / 2, (GRID_Y1 + SPONSOR_TOP) / 2 + cap(f_cta) / 2)
img.alpha_composite(sponsors)

rng = np.random.default_rng(27)
g = arr(img) + rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
img_of(g).save(out, optimize=True)
print("wrote", out, "head px", f_head.size, "kick/main px", f_kick.size, f_main.size,
      "grid", GRID_Y0, GRID_Y1, "sponsors top", round(SPONSOR_TOP))
