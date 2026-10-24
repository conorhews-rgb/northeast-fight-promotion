#!/usr/bin/env python3
"""Render the full NFP 1 fight card as one PNG poster.

Reads the bout table from tools/make-fight-card.py, so the poster and the
website card always list the same bouts in the same order. Main event gets
its own wide panel, the other featured bouts share a row, and the undercard
runs three across in card order. Type is the site's Barlow Condensed.

Two formats share one design, laid out on a 1024-wide grid:
    tall  1024x1536 grid, written at 2048x3072
    ig    1024x1280 grid, written at 1080x1350 for an Instagram post
The ig layout is the same design with the vertical spacing tightened.

Run from the repo root:
    python3 tools/make-fight-card-poster.py [tall|ig] [out.png]
"""
import importlib.util, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FORMATS = {
    "tall": dict(
        H=1536, out_w=2048,
        logo_w=232, logo_y=26, title=(246, 58), venue=(308, 30), times=(345, 21),
        main=(384, 652), main_ph=152, main_name=40, main_gym=18,
        co=(668, 950), co_ph=104,
        under=(966, 1426), u_ph=58, u_py=34, u_name=16, u_head=12,
        foot=(1444, 54, 1500, 34),
    ),
    "ig": dict(
        H=1280, out_w=1080,
        logo_w=168, logo_y=16, title=(176, 50), venue=(230, 26), times=(263, 19),
        main=(296, 540), main_ph=134, main_name=38, main_gym=17,
        co=(554, 802), co_ph=88,
        under=(816, 1184), u_ph=46, u_py=30, u_name=15, u_head=10,
        foot=(1203, 46, 1248, 29),
    ),
}

fmt = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in FORMATS else "tall"
args = [a for a in sys.argv[1:] if a not in FORMATS]
L = FORMATS[fmt]
W, H = 1024, L["H"]
S = L["out_w"] / W
OUT = args[0] if args else f"nfp1-fight-card-{fmt}.png"

spec = importlib.util.spec_from_file_location("card", "tools/make-fight-card.py")
card = importlib.util.module_from_spec(spec); spec.loader.exec_module(card)
BOUTS = card.BOUTS

F = "assets/fonts/BarlowCondensed-{}-latin.woff2"
def font(w, px): return ImageFont.truetype(F.format(w), max(1, int(px * S)))

WHITE, MUTED, GREEN, GREEN_DK = (255, 255, 255), (164, 172, 166), (22, 194, 22), (15, 154, 15)
VS_GREY = (120, 128, 124)
PANEL = (8, 10, 9, 196)

def plain(s): return re.sub(r"<[^>]+>", "", s).replace("  ", " ").upper()
def P(*v): return tuple(int(round(x * S)) for x in v)
OW, OH = round(W * S), round(H * S)

# ---------- background: the arena, cover-cropped from the top, darkened ----------
src = Image.open("assets/img/posters/fight-card-bg.webp").convert("RGB")
scale = OW / src.width
bg = src.resize((OW, round(src.height * scale)), Image.LANCZOS).crop((0, 0, OW, OH))
shade = Image.new("L", (1, OH))
for y in range(OH):
    t = y / OH
    shade.putpixel((0, y), int(255 * (0.30 + 0.40 * min(1, max(0, (t - 0.18) / 0.25)))))
shade = shade.resize((OW, OH))
img = Image.composite(Image.new("RGB", bg.size, (0, 0, 0)), bg, shade).convert("RGBA")
layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
d = ImageDraw.Draw(layer)

def fit(text, weight, px, maxw):
    """Largest size up to px that keeps text within maxw."""
    while px > 8:
        f = font(weight, px)
        if d.textlength(text, font=f) <= maxw * S: return f
        px -= 1
    return font(weight, 8)

def text(xy, s, f, fill, anchor="mt", shadow=False):
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text(P(xy[0] + 1.5, xy[1] + 2), s, font=f, fill=(0, 0, 0, 200), anchor=anchor)
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3 * S)))
    d.text(P(*xy), s, font=f, fill=fill, anchor=anchor)

def panel(x0, y0, x1, y1, featured):
    d.rectangle(P(x0, y0, x1, y1), fill=PANEL, outline=(255, 255, 255, 22), width=max(1, round(S)))
    d.rectangle(P(x0, y0, x1, y0 + 4), fill=GREEN_DK if featured else (60, 66, 64, 255))

def tag(cx, y, s):
    f = font("800i", 17); tw = d.textlength(s, font=f) / S
    d.rectangle(P(cx - tw / 2 - 10, y, cx + tw / 2 + 10, y + 24), fill=GREEN_DK)
    d.text(P(cx, y + 12.5), s, font=f, fill=WHITE, anchor="mm")

def photo(slug, x, y, size):
    im = Image.open(f"assets/img/fighters/{slug}.jpg").convert("RGBA").resize(P(size, size), Image.LANCZOS)
    layer.alpha_composite(im, P(x, y))
    d.rectangle(P(x, y, x + size, y + size), outline=(255, 255, 255, 40), width=max(1, round(S)))

def bout_head(cx, y, b, maxw, big):
    tg, name, meta = b[0], plain(b[1]), plain(b[2])
    if tg:
        tag(cx, y, tg.upper()); y += 32
    text((cx, y), name, fit(name, "800i", 34 if big else 26, maxw), WHITE); y += (38 if big else 30)
    text((cx, y), meta, font("700", 16 if big else 14), MUTED)
    return y + 22

# ---------- header ----------
logo = Image.open("assets/img/nfp-logo-alpha.png").convert("RGBA")
lw = L["logo_w"]; lh = int(lw * logo.height / logo.width)
layer.alpha_composite(logo.resize(P(lw, lh), Image.LANCZOS), P((W - lw) / 2, L["logo_y"]))
text((W / 2, L["title"][0]), "NFP 1 - OCTOBER 24TH", font("800i", L["title"][1]), WHITE, shadow=True)
text((W / 2, L["venue"][0]), "NASHUA COMMUNITY COLLEGE", font("800i", L["venue"][1]), WHITE, shadow=True)
text((W / 2, L["times"][0]), "DOORS 4PM   /   FIGHTS 6PM", font("700i", L["times"][1]), GREEN, shadow=True)

featured = [b for b in BOUTS if b[0]]
under = [b for b in BOUTS if not b[0]]
M = 40                                           # outer margin

# ---------- main event: wide panel, faces on the outside, names inside ----------
main = featured[0]
y0, y1 = L["main"]
panel(M, y0, W - M, y1, True)
y = bout_head(W / 2, y0 + 14, main, W - 2 * M - 40, True)
ph = L["main_ph"]; py = y + 6
for side, (slug, name, gym, code) in (("l", main[3]), ("r", main[4])):
    if side == "l":
        px, tx, anc = M + 28, M + 28 + ph + 18, "lt"
    else:
        px, tx, anc = W - M - 28 - ph, W - M - 28 - ph - 18, "rt"
    photo(slug, px, py, ph)
    maxw = W / 2 - 50 - (ph + 46)
    text((tx, py + ph / 2 - 36), name.upper(), fit(name.upper(), "800i", L["main_name"], maxw), WHITE, anc)
    text((tx, py + ph / 2 + 14), gym.upper(), fit(gym.upper(), "700", L["main_gym"], maxw), MUTED, anc)
text((W / 2, py + ph / 2), "VS", font("800i", 44), VS_GREY, "mm")

# ---------- co-main and title fight, side by side ----------
gap = 18
cw = (W - 2 * M - gap) / 2
y0, y1 = L["co"]
for i, b in enumerate(featured[1:3]):
    x0 = M + i * (cw + gap); cx = x0 + cw / 2
    panel(x0, y0, x0 + cw, y1, True)
    y = bout_head(cx, y0 + 14, b, cw - 30, False)
    ph = L["co_ph"]; py = y + 6
    for j, (slug, name, gym, code) in enumerate((b[3], b[4])):
        fx = x0 + cw * (0.27 if j == 0 else 0.73)
        photo(slug, fx - ph / 2, py, ph)
        text((fx, py + ph + 8), name.upper(), fit(name.upper(), "800i", 24, cw * 0.44), WHITE)
        text((fx, py + ph + 36), gym.upper(), fit(gym.upper(), "700", 14, cw * 0.44), MUTED)
    text((cx, py + ph / 2), "VS", font("800i", 30), VS_GREY, "mm")

# ---------- undercard, three across in card order ----------
cols, g = 3, 14
uw = (W - 2 * M - (cols - 1) * g) / cols
rows = (len(under) + cols - 1) // cols
top, bottom = L["under"]
uh = (bottom - top - (rows - 1) * g) / rows
for k, b in enumerate(under):
    r, c = divmod(k, cols)
    x0 = M + c * (uw + g); y0 = top + r * (uh + g); cx = x0 + uw / 2
    panel(x0, y0, x0 + uw, y0 + uh, False)
    head = plain(b[1]) + "  /  " + plain(b[2])
    text((cx, y0 + L["u_head"]), head, fit(head, "800i", 16, uw - 20), WHITE)
    ph = L["u_ph"]; py = y0 + L["u_py"]
    for j, (slug, name, gym, code) in enumerate((b[3], b[4])):
        fx = x0 + uw * (0.26 if j == 0 else 0.74)
        photo(slug, fx - ph / 2, py, ph)
        text((fx, py + ph + 5), name.upper(), fit(name.upper(), "800i", L["u_name"], uw * 0.46), WHITE)
        text((fx, py + ph + 22), gym.upper(), fit(gym.upper(), "700", 11, uw * 0.46), MUTED)
    text((cx, py + ph / 2), "VS", font("800i", 20), VS_GREY, "mm")

# ---------- footer ----------
fy, fpx, uy, upx = L["foot"]
ft = font("800i", fpx)
a, b2 = "TICKETS ON SALE ", "NOW"
tw = (d.textlength(a, font=ft) + d.textlength(b2, font=ft)) / S
x = W / 2 - tw / 2
text((x, fy), a, ft, WHITE, "lt", shadow=True)
text((x + d.textlength(a, font=ft) / S, fy), b2, ft, GREEN, "lt", shadow=True)
text((W / 2, uy), "NFPFIGHTS.COM", font("800i", upx), WHITE, shadow=True)

img.alpha_composite(layer)
img.convert("RGB").save(OUT, optimize=True)
print(f"wrote {OUT} ({OW}x{OH}), {len(BOUTS)} bouts")
