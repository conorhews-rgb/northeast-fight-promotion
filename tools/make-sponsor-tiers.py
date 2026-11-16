#!/usr/bin/env python3
"""Render the NFP 2 sponsor call, 1080x1350: Silver, Gold and Platinum tiers.

Same backdrop as the Kim vs Cetoute flyer: the Sheraton at night over a blurred
copy of the hotel-and-cage art (both in assets/img/poster-src/). Top: NFP 2,
BECOME A SPONSOR, date and venue, with the hotel's towers beneath. Then one
frosted row per tier, name and price left, perks right. CTA, then the current
sponsors' row. "NFP 2" is Arial Black to match the logo; all other lettering
is Versa Versa (~/Library/Fonts/Versa-Versa.otf). Edit TIERS to change the offer.

Run from the repo root:
    python3 tools/make-sponsor-tiers.py OUT.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
from sponsor_row import sponsor_row

out = sys.argv[1]
hotel_path = "assets/img/poster-src/sheraton-night.webp"
art_path = "assets/img/poster-src/nfp2-hotel-cage.jpg"
W, H = 1080, 1350
VERSA = os.path.expanduser("~/Library/Fonts/Versa-Versa.otf")
ARIAL_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
def versa(px): return ImageFont.truetype(VERSA, int(px))

TIERS = [  # name, price, metallic gradient for the name (top, bottom), perks
    dict(name="SILVER", price="$1,500", grad=((238, 241, 245), (148, 155, 164)), perks=[
        "2 FREE GENERAL ADMISSION TICKETS",
        "BUSINESS LOGO ON EVERY POSTER",
        "LOGO DISPLAYED IN VENUE",
        "2 IN RING MC ANNOUNCEMENTS AT THE EVENT",
        "SOCIAL MEDIA POST"]),
    dict(name="GOLD", price="$2,000", grad=((255, 228, 132), (198, 146, 42)), perks=[
        "4 GENERAL ADMISSION TICKETS",
        "LOGO ON CANVAS",
        "LOGO ON EVERY FUTURE POSTER",
        "4 IN RING MC ANNOUNCEMENTS AT THE EVENT",
        "DEDICATED SOCIAL MEDIA POST"]),
    dict(name="PLATINUM", price="$2,500", grad=((255, 255, 255), (166, 204, 224)), perks=[
        "4 FRONT ROW SEATS",
        "LOGO ON CANVAS",
        "LOGO ON EVERY FUTURE POSTER",
        "6 IN RING MC ANNOUNCEMENTS AT THE EVENT",
        "DEDICATED SOCIAL MEDIA POST",
        "DEDICATED TABLE AT THE EVENT"]),
]
CTA = ("DM US TO ", "LOCK IN YOUR SPOT")

# layout
TITLE_PX, TITLE_Y = 112, 112
HEAD_Y, INFO_Y = 174, 208          # BECOME A SPONSOR, then date and venue
HOTEL_S, HOTEL_TOWER_Y = 0.83, 216   # venue photo scale; tower tops land just under the info line
HOTEL_FADE0, HOTEL_FADE1 = 470, 760  # the hotel dissolves behind the tier rows
ROWS_Y0 = 432                      # first tier row starts under the hotel's sign
ROW_X0, ROW_X1 = 50, 1030
SPLIT_X = 350                      # divider between name/price and perks
PERK_X = 398                       # perk text starts here; bullet sits 22 px left
PITCH, PAD, ROW_GAP = 34, 34, 14   # perk line pitch, row padding (top + bottom), gap between rows
LOGO_CY = 1264


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


# ---------------------------------------------------------------- background (as on the fight flyer)
art = Image.open(art_path).convert("RGB")
bg = art.resize((W, round(art.height * W / art.width)), Image.LANCZOS)
bg = bg.crop((0, (bg.height - H) // 2, W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(40))
base = arr(ImageEnhance.Brightness(bg).enhance(0.30))

hotel = Image.open(hotel_path).convert("RGB")
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
    bd.polygon([(x0 - 14, -60), (x0 + 14, -60), (x1 + spread, 900), (x1 - spread, 900)], fill=70)
beams = np.asarray(beams.filter(ImageFilter.GaussianBlur(38)), dtype=np.float32) / 255
beams *= np.clip(1 - ys / 900, 0, 1)[:, None] ** 1.2
base = screen(base, (150, 205, 165), beams * 0.55)

base = screen(base, (34, 62, 40), radial(W / 2, 130, 620, 230, 1.6) * 0.95)       # haze behind the top block
base = screen(base, (26, 104, 40), radial(W / 2, 780, 620, 460, 1.7) * 0.42)      # green pooled behind the tier rows
base = base * (1 - 0.88 * np.clip((ys - 1090) / 110, 0, 1))[:, None, None]        # near-black behind CTA and sponsors
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
put_text(img, [("BECOME A ", versa(58), WHITE), ("SPONSOR", versa(58), GREEN)], W / 2, HEAD_Y)
put_text(img, [("SATURDAY MARCH 27  |  SHERATON HOTEL  |  NASHUA, NH", versa(26), SOFT)], W / 2, INFO_Y, deep=False)

# ---------------------------------------------------------------- tier rows
f_name, f_price = versa(46), versa(74)
px = 27                                                 # one perk size for every row: the largest that fits the widest perk
while max(width_of([(p, versa(px))]) for t in TIERS for p in t["perks"]) > ROW_X1 - 30 - PERK_X: px -= 1
f_perk = versa(px)

y0 = ROWS_Y0
for t in TIERS:
    h = len(t["perks"]) * PITCH + PAD
    y1 = y0 + h; cy = (y0 + y1) / 2
    panel = Image.new("L", (W, H), 0); ImageDraw.Draw(panel).rounded_rectangle((ROW_X0, y0, ROW_X1, y1), 9, fill=255)
    img.alpha_composite(shadow(panel, 0, 10, 16, 0.7))
    frost = Image.blend(img.filter(ImageFilter.GaussianBlur(14)), Image.new("RGBA", (W, H), (5, 9, 7, 255)), 0.66)
    img.paste(frost, (0, 0), panel)
    rim = Image.new("L", (W, H), 0); ImageDraw.Draw(rim).rounded_rectangle((ROW_X0, y0, ROW_X1, y1), 9, outline=255, width=1)
    rl = Image.new("RGBA", (W, H), t["grad"][0] + (0,)); rl.putalpha(rim.point(lambda v: int(v * .30))); img.alpha_composite(rl)
    dv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(dv).line((SPLIT_X, y0 + 22, SPLIT_X, y1 - 22), fill=(255, 255, 255, 38), width=1)
    img.alpha_composite(dv)

    # name over price, centred as a pair in the left column
    lx = (ROW_X0 + SPLIT_X) / 2
    gap = 20
    top = cy - (cap(f_name) + gap + cap(f_price)) / 2
    put_text(img, [(t["name"], f_name, t["grad"])], lx, top + cap(f_name), deep=False)
    put_text(img, [(t["price"], f_price, WHITE)], lx, top + cap(f_name) + gap + cap(f_price))

    # perks, centred as a block in the right column
    by = cy - (len(t["perks"]) - 1) * PITCH / 2 + cap(f_perk) / 2
    d = ImageDraw.Draw(img)
    for i, perk in enumerate(t["perks"]):
        yb = by + i * PITCH
        my = yb - cap(f_perk) / 2
        d.rounded_rectangle((PERK_X - 24, my - 5, PERK_X - 14, my + 5), 2, fill=(40, 206, 40))
        put_text(img, [(perk, f_perk, WHITE)], PERK_X, yb, align="l", deep=False)
    y0 = y1 + ROW_GAP
ROWS_Y1 = y0 - ROW_GAP

# ---------------------------------------------------------------- CTA and current sponsors
sponsors, SPONSOR_TOP, _ = sponsor_row(W, H, LOGO_CY)
f_cta = versa(38)
put_text(img, [(CTA[0], f_cta, WHITE), (CTA[1], f_cta, GREEN)], W / 2, (ROWS_Y1 + SPONSOR_TOP) / 2 + cap(f_cta) / 2)
img.alpha_composite(sponsors)

rng = np.random.default_rng(27)
g = arr(img) + rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
img_of(g).save(out, optimize=True)
print("wrote", out, "perk px", px, "rows", ROWS_Y0, ROWS_Y1, "sponsors top", round(SPONSOR_TOP))
