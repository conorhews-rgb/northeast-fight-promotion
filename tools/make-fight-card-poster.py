#!/usr/bin/env python3
"""Render the full NFP 1 fight card as one PNG poster.

Reads the bout table from tools/make-fight-card.py, so the poster and the
website card always list the same bouts in the same order. Main event gets
its own wide panel, the other featured bouts share a row, and the undercard
runs three across in card order. Type is the site's Barlow Condensed.

Run from the repo root:
    python3 tools/make-fight-card-poster.py [out.png]
"""
import importlib.util, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 2                                  # render at 2x the 1024x1536 layout
W, H = 1024, 1536
OUT = sys.argv[1] if len(sys.argv) > 1 else "nfp1-fight-card.png"

spec = importlib.util.spec_from_file_location("card", "tools/make-fight-card.py")
card = importlib.util.module_from_spec(spec); spec.loader.exec_module(card)
BOUTS = card.BOUTS

F = "assets/fonts/BarlowCondensed-{}-latin.woff2"
def font(w, px): return ImageFont.truetype(F.format(w), int(px * S))

WHITE, MUTED, GREEN, GREEN_DK = (255, 255, 255), (164, 172, 166), (22, 194, 22), (15, 154, 15)
PANEL = (8, 10, 9, 196)

def plain(s): return re.sub(r"<[^>]+>", "", s).replace("  ", " ").upper()
def P(*v): return tuple(int(round(x * S)) for x in v)

# ---------- background: the arena, darkened so type reads over it ----------
bg = Image.open("assets/img/posters/fight-card-bg.webp").convert("RGB").resize((W * S, H * S), Image.LANCZOS)
shade = Image.new("L", (1, H * S))
for y in range(H * S):
    t = y / (H * S)
    shade.putpixel((0, y), int(255 * (0.30 + 0.40 * min(1, max(0, (t - 0.18) / 0.25)))))
shade = shade.resize((W * S, H * S))
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
    d.rectangle(P(x0, y0, x1, y1), fill=PANEL, outline=(255, 255, 255, 22), width=S)
    d.rectangle(P(x0, y0, x1, y0 + 4), fill=GREEN_DK if featured else (60, 66, 64, 255))

def tag(cx, y, s):
    f = font("800i", 17); tw = d.textlength(s, font=f) / S
    d.rectangle(P(cx - tw / 2 - 10, y, cx + tw / 2 + 10, y + 24), fill=GREEN_DK)
    d.text(P(cx, y + 12.5), s, font=f, fill=WHITE, anchor="mm")

def photo(slug, x, y, size):
    im = Image.open(f"assets/img/fighters/{slug}.jpg").convert("RGBA").resize(P(size, size), Image.LANCZOS)
    layer.alpha_composite(im, P(x, y))
    d.rectangle(P(x, y, x + size, y + size), outline=(255, 255, 255, 40), width=S)

def bout_head(cx, y, b, maxw, big):
    tg, name, meta = b[0], plain(b[1]), plain(b[2])
    if tg:
        tag(cx, y, tg.upper()); y += 32
    text((cx, y), name, fit(name, "800i", 34 if big else 26, maxw), WHITE); y += (38 if big else 30)
    text((cx, y), meta, font("700", 16 if big else 14), MUTED)
    return y + 22

# ---------- header ----------
logo = Image.open("assets/img/nfp-logo-alpha.png").convert("RGBA")
lw = 232; lh = int(lw * logo.height / logo.width)
layer.alpha_composite(logo.resize(P(lw, lh), Image.LANCZOS), P((W - lw) / 2, 26))
text((W / 2, 246), "NFP 1 - OCTOBER 24TH", font("800i", 58), WHITE, shadow=True)
text((W / 2, 308), "NASHUA COMMUNITY COLLEGE", font("800i", 30), WHITE, shadow=True)
text((W / 2, 345), "DOORS 4PM   /   FIGHTS 6PM", font("700i", 21), GREEN, shadow=True)

featured = [b for b in BOUTS if b[0]]
under = [b for b in BOUTS if not b[0]]
M = 40                                           # outer margin

# ---------- main event: wide panel, faces on the outside, names inside ----------
main = featured[0]
y0, y1 = 384, 652
panel(M, y0, W - M, y1, True)
y = bout_head(W / 2, y0 + 14, main, W - 2 * M - 40, True)
ph = 152; py = y + 6
for side, (slug, name, gym, code) in (("l", main[3]), ("r", main[4])):
    if side == "l":
        px, tx, anc = M + 28, M + 28 + ph + 18, "lt"
    else:
        px, tx, anc = W - M - 28 - ph, W - M - 28 - ph - 18, "rt"
    photo(slug, px, py, ph)
    maxw = W / 2 - 50 - (ph + 46)
    text((tx, py + 40), name.upper(), fit(name.upper(), "800i", 40, maxw), WHITE, anc)
    text((tx, py + 90), gym.upper(), fit(gym.upper(), "700", 18, maxw), MUTED, anc)
text((W / 2, py + ph / 2), "VS", font("800i", 44), (120, 128, 124), "mm")

# ---------- co-main and title fight, side by side ----------
gap = 18
cw = (W - 2 * M - gap) / 2
y0, y1 = 668, 950
for i, b in enumerate(featured[1:3]):
    x0 = M + i * (cw + gap); cx = x0 + cw / 2
    panel(x0, y0, x0 + cw, y1, True)
    y = bout_head(cx, y0 + 14, b, cw - 30, False)
    ph = 104; py = y + 6
    for j, (slug, name, gym, code) in enumerate((b[3], b[4])):
        fx = x0 + cw * (0.27 if j == 0 else 0.73)
        photo(slug, fx - ph / 2, py, ph)
        text((fx, py + ph + 8), name.upper(), fit(name.upper(), "800i", 24, cw * 0.44), WHITE)
        text((fx, py + ph + 36), gym.upper(), fit(gym.upper(), "700", 14, cw * 0.44), MUTED)
    text((cx, py + ph / 2), "VS", font("800i", 30), (120, 128, 124), "mm")

# ---------- undercard, three across in card order ----------
cols, g = 3, 14
uw = (W - 2 * M - (cols - 1) * g) / cols
rows = (len(under) + cols - 1) // cols
top, bottom = 966, 1426
uh = (bottom - top - (rows - 1) * g) / rows
for k, b in enumerate(under):
    r, c = divmod(k, cols)
    x0 = M + c * (uw + g); y0 = top + r * (uh + g); cx = x0 + uw / 2
    panel(x0, y0, x0 + uw, y0 + uh, False)
    head = plain(b[1]) + "  /  " + plain(b[2])
    text((cx, y0 + 12), head, fit(head, "800i", 16, uw - 20), WHITE)
    ph = 58; py = y0 + 34
    for j, (slug, name, gym, code) in enumerate((b[3], b[4])):
        fx = x0 + uw * (0.26 if j == 0 else 0.74)
        photo(slug, fx - ph / 2, py, ph)
        text((fx, py + ph + 5), name.upper(), fit(name.upper(), "800i", 16, uw * 0.46), WHITE)
        text((fx, py + ph + 22), gym.upper(), fit(gym.upper(), "700", 11, uw * 0.46), MUTED)
    text((cx, py + ph / 2), "VS", font("800i", 20), (120, 128, 124), "mm")

# ---------- footer ----------
ft = font("800i", 54)
a, b2 = "TICKETS ON SALE ", "NOW"
tw = (d.textlength(a, font=ft) + d.textlength(b2, font=ft)) / S
x = W / 2 - tw / 2
text((x, 1444), a, ft, WHITE, "lt", shadow=True)
text((x + d.textlength(a, font=ft) / S, 1444), b2, ft, GREEN, "lt", shadow=True)
text((W / 2, 1500), "NFPFIGHTS.COM", font("800i", 34), WHITE, shadow=True)

img.alpha_composite(layer)
img.convert("RGB").save(OUT, optimize=True)
print(f"wrote {OUT} ({W * S}x{H * S}), {len(BOUTS)} bouts")
