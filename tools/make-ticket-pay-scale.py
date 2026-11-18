#!/usr/bin/env python3
"""Render the fighter ticket pay scale, 1080x1350: four tiers and the coaches' share.

Same look as the NFP 2 bonuses and sponsor posters: the blurred hotel-and-cage
art (assets/img/poster-src/) under beams and green haze, frosted rows, green
gradient figures, sponsor row along the bottom. It names no event, so the NFP
logo leads instead of "NFP 2". Top: logo, FIGHTER TICKET PAY SCALE, tagline.
Then one row per tier, tickets sold left, the fighter's percentage right, and a
green-rimmed panel for the coaches. Lettering is Versa Versa
(~/Library/Fonts/Versa-Versa.otf); on a machine without it, pass another font
file as the second argument. Edit TIERS and COACHES to change the offer.

Run from the repo root:
    python3 tools/make-ticket-pay-scale.py OUT.png [FONT]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
from sponsor_row import sponsor_row

out = sys.argv[1]
art_path = "assets/img/poster-src/nfp2-hotel-cage.jpg"
logo_path = "assets/img/nfp-logo-alpha.png"
W, H = 1080, 1350
FONT = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/Library/Fonts/Versa-Versa.otf")


def versa(px):
    f = ImageFont.truetype(FONT, int(px))
    try: f.set_variation_by_axes([800])         # a variable stand-in: use its extra-bold
    except Exception: pass
    return f


HEAD = ("FIGHTER TICKET ", "PAY SCALE")
TAGLINE = "THE MORE YOU SELL, THE MORE YOU EARN"
UNIT = "TICKETS SOLD"
TIERS = [("0-50", "5%"), ("51-100", "10%"), ("101-150", "15%"), ("151+", "20%")]
COACHES = dict(
    head="COACHES",
    thanks=["WE APPRECIATE THE HARD WORK AND EFFORT",
            "YOU POUR INTO THESE FIGHTERS."],
    offer="PROFIT SHARING ON ALL TICKETS",
    when="ONCE YOUR FIGHTER SELLS 50 TICKETS",
    share="5%")

# layout
LOGO_Y, LOGO_H = 34, 232           # logo top and height
HEAD_Y, TAG_Y = 338, 380           # headline and tagline baselines
ROWS_Y0, ROW_H, ROW_GAP = 414, 96, 12
ROW_X0, ROW_X1 = 60, 1020
TEXT_X, FIG_X = 98, 982            # left text edge, right edge of the green figures
COACH_GAP, COACH_H = 34, 292       # space above the coaches panel, its height
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


def text_mask(runs, x, y):
    masks = []
    for t, f in runs:
        m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
        md.text((x, y), t, font=f, fill=255, anchor="ls")
        x += md.textlength(t, font=f)
        masks.append(m)
    full = masks[0]
    for m in masks[1:]: full = ImageChops.lighter(full, m)
    return full, masks


def width_of(runs):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return sum(d.textlength(t, font=f) for t, f in runs)


def cap(f): return -f.getbbox("H", anchor="ls")[1]

WHITE, SOFT, GREEN = ((255, 255, 255), (214, 218, 216)), ((204, 211, 206), (172, 180, 174)), ((70, 230, 70), (16, 156, 16))


def put_text(img, runs, x, y, align="c", deep=True, glow=0.0):
    """runs: [(text, font, (top, bottom))] on one baseline; align l / c / r about x."""
    plain = [(t, f) for t, f, _ in runs]
    w = width_of(plain)
    x = x - w / 2 if align == "c" else x - w if align == "r" else x
    full, masks = text_mask(plain, x, y)
    img.alpha_composite(shadow(full, 0, 7 if deep else 4, 11 if deep else 6, 0.85))
    img.alpha_composite(shadow(full, 0, 3, 2, 0.9))
    if glow: img.alpha_composite(shadow(full, 0, 0, 20, glow, (22, 194, 22)))
    for m, (_, _, (top, bottom)) in zip(masks, runs):
        img.alpha_composite(fill_with(m, top, bottom))
    return full


def fit(texts, px, width):
    """Largest size up to px at which every string in texts fits in width."""
    while max(width_of([(t, versa(px))]) for t in texts) > width: px -= 1
    return versa(px)


def panel(img, y0, y1, rim, rim_alpha):
    """Frosted row with a drop shadow and a 1 px rim, as on the bonuses poster."""
    box = (ROW_X0, y0, ROW_X1, y1)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle(box, 9, fill=255)
    img.alpha_composite(shadow(m, 0, 10, 16, 0.7))
    frost = Image.blend(img.filter(ImageFilter.GaussianBlur(14)), Image.new("RGBA", (W, H), (5, 9, 7, 255)), 0.66)
    img.paste(frost, (0, 0), m)
    r = Image.new("L", (W, H), 0); ImageDraw.Draw(r).rounded_rectangle(box, 9, outline=255, width=1)
    rl = Image.new("RGBA", (W, H), rim + (0,)); rl.putalpha(r.point(lambda v: int(v * rim_alpha))); img.alpha_composite(rl)


# ---------------------------------------------------------------- background (as on the sponsor poster, without the hotel)
art = Image.open(art_path).convert("RGB")
bg = art.resize((W, round(art.height * W / art.width)), Image.LANCZOS)
bg = bg.crop((0, (bg.height - H) // 2, W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(40))
base = arr(ImageEnhance.Brightness(bg).enhance(0.30))
ys = np.arange(H, dtype=np.float32)

beams = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(beams)
for x0, x1, spread in ((-40, 250, 120), (200, 330, 150), (880, 750, 150), (1120, 830, 120), (540, 540, 210)):
    bd.polygon([(x0 - 14, -60), (x0 + 14, -60), (x1 + spread, 900), (x1 - spread, 900)], fill=70)
beams = np.asarray(beams.filter(ImageFilter.GaussianBlur(38)), dtype=np.float32) / 255
beams *= np.clip(1 - ys / 900, 0, 1)[:, None] ** 1.2
base = screen(base, (150, 205, 165), beams * 0.55)

base = screen(base, (34, 62, 40), radial(W / 2, 170, 620, 280, 1.6) * 0.95)       # haze behind the top block
base = screen(base, (26, 104, 40), radial(W / 2, 760, 620, 480, 1.7) * 0.42)      # green pooled behind the rows
base = base * (1 - 0.88 * np.clip((ys - 1130) / 90, 0, 1))[:, None, None]         # near-black behind the sponsors
yy, xx = np.mgrid[0:H, 0:W]
vig = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
base = base * (1 - 0.38 * np.clip((vig - 0.6) / 0.6, 0, 1) ** 1.5)[..., None]
img = img_of(base).convert("RGBA")

# ---------------------------------------------------------------- top block
logo = Image.open(logo_path).convert("RGBA")
logo = logo.crop(logo.getbbox())
logo = logo.resize((round(logo.width * LOGO_H / logo.height), LOGO_H), Image.LANCZOS)
ll = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ll.paste(logo, ((W - logo.width) // 2, LOGO_Y))
la = ll.getchannel("A")
img.alpha_composite(shadow(la, 0, 12, 18, 0.75))
img.alpha_composite(shadow(la, 0, 0, 26, 0.22, (22, 194, 22)))
img.alpha_composite(ll)

f_head = fit(["".join(HEAD)], 66, ROW_X1 - ROW_X0)
put_text(img, [(HEAD[0], f_head, WHITE), (HEAD[1], f_head, GREEN)], W / 2, HEAD_Y)
put_text(img, [(TAGLINE, versa(27), SOFT)], W / 2, TAG_Y, deep=False)

# ---------------------------------------------------------------- tier rows
f_range, f_unit, f_fig = versa(58), versa(27), versa(80)
unit_x = TEXT_X + max(width_of([(r, f_range)]) for r, _ in TIERS) + 26   # one column for TICKETS SOLD
y0 = ROWS_Y0
for rng_, pct in TIERS:
    y1 = y0 + ROW_H; cy = (y0 + y1) / 2
    panel(img, y0, y1, (255, 255, 255), 0.16)
    yb = cy + cap(f_range) / 2
    put_text(img, [(rng_, f_range, WHITE)], TEXT_X, yb, align="l", deep=False)
    put_text(img, [(UNIT, f_unit, SOFT)], unit_x, yb, align="l", deep=False)
    put_text(img, [(pct, f_fig, GREEN)], FIG_X, cy + cap(f_fig) / 2, align="r", glow=0.30)
    y0 = y1 + ROW_GAP
ROWS_Y1 = y0 - ROW_GAP

# ---------------------------------------------------------------- coaches
c0 = ROWS_Y1 + COACH_GAP; c1 = c0 + COACH_H
panel(img, c0, c1, (60, 214, 60), 0.55)
f_ch, f_th = versa(54), versa(25)
f_offer = fit([COACHES["offer"]], 36, FIG_X - TEXT_X - width_of([(COACHES["share"], f_fig)]) - 40)
f_when = fit([COACHES["when"]], 25, width_of([(COACHES["offer"], f_offer)]))
RULE_GAP = 26                                   # space above and below the divider
TH_PITCH = 34
top_h = cap(f_ch) + 22 + cap(f_th) + TH_PITCH * (len(COACHES["thanks"]) - 1)
bot_h = cap(f_offer) + 16 + cap(f_when)
y = (c0 + c1) / 2 - (top_h + RULE_GAP * 2 + bot_h) / 2
put_text(img, [(COACHES["head"], f_ch, GREEN)], TEXT_X, y + cap(f_ch), align="l", glow=0.22)
ty = y + cap(f_ch) + 22 + cap(f_th)
for i, line in enumerate(COACHES["thanks"]):
    put_text(img, [(line, f_th, SOFT)], TEXT_X, ty + i * TH_PITCH, align="l", deep=False)
ry = round(y + top_h + RULE_GAP)
dv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(dv).line((TEXT_X, ry, FIG_X, ry), fill=(255, 255, 255, 38), width=1)
img.alpha_composite(dv)
by = ry + RULE_GAP
put_text(img, [(COACHES["offer"], f_offer, WHITE)], TEXT_X, by + cap(f_offer), align="l", deep=False)
put_text(img, [(COACHES["when"], f_when, SOFT)], TEXT_X, by + bot_h, align="l", deep=False)
put_text(img, [(COACHES["share"], f_fig, GREEN)], FIG_X, by + bot_h / 2 + cap(f_fig) / 2, align="r", glow=0.30)

# ---------------------------------------------------------------- current sponsors
sponsors, SPONSOR_TOP, _ = sponsor_row(W, H, LOGO_CY)
img.alpha_composite(sponsors)

rng = np.random.default_rng(27)
g = arr(img) + rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
img_of(g).save(out, optimize=True)
print("wrote", out, "rows", ROWS_Y0, ROWS_Y1, "coaches", c0, c1, "sponsors top", round(SPONSOR_TOP))
