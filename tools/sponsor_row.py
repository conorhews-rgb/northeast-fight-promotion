"""White sponsor row for NFP posters: Reliable Auto, Sequel, Diesel & Dirt.

Every poster carries this row along the bottom. Use it from any renderer:

    sys.path.insert(0, "tools")
    from sponsor_row import sponsor_row
    layer, top, bottom = sponsor_row(1080, 1350, cy=1264)
    poster.alpha_composite(layer)

The marks are white alpha PNGs in assets/img/sponsors/, made from the originals
beside them. Each is sized to the same optical weight, they are split by thin
dividers, and the row carries a soft drop shadow. At cy=1264 on a 1080x1350
post the row spans y 1212-1316 with 128 px side margins.
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "img", "sponsors")
SPONSORS = [  # (white mark, optical weight), left to right
    ("reliable-auto-white.png", 0.75),      # round badge fills its box; fine type reads light
    ("sequel-white.png", 1.15),             # thin subline reads light
    ("diesel-and-dirt-white.png", 1.0),
]
AREA = 14500                                # ink-box area per mark at weight 1, in px
GAP = 56                                    # half the space between marks; a divider sits mid-gap


def sponsor_row(W, H, cy, scale=1.0):
    """RGBA layer with the sponsor row centred on y=cy; returns (layer, top_y, bottom_y)."""
    marks = []
    for name, weight in SPONSORS:
        a = Image.open(os.path.join(DIR, name)).getchannel("A")
        a = a.crop(a.getbbox())
        aspect = a.width / a.height
        w = round((AREA * weight * aspect) ** .5 * scale)
        marks.append(a.resize((w, round(w / aspect)), Image.LANCZOS))

    gap = GAP * scale
    x = (W - sum(m.width for m in marks) - gap * 2 * (len(marks) - 1)) / 2
    mask = Image.new("L", (W, H), 0)
    dividers = []
    for i, m in enumerate(marks):
        mask.paste(m, (round(x), round(cy - m.height / 2)))
        x += m.width
        if i < len(marks) - 1:
            dividers.append(round(x + gap))
            x += 2 * gap

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = ImageChops.offset(mask, 0, 4).filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .75))
    zero = Image.new("L", (W, H), 0)
    layer.alpha_composite(Image.merge("RGBA", (zero, zero, zero, sh)))
    ink = Image.new("RGBA", (W, H), (240, 242, 241, 0))
    ink.putalpha(mask.point(lambda v: int(v * .94)))
    layer.alpha_composite(ink)

    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    for dx in dividers:
        d.line((dx, cy - 30 * scale, dx, cy + 30 * scale), fill=(255, 255, 255, 150), width=1)
    layer.alpha_composite(lines)

    half = max(m.height for m in marks) / 2
    return layer, cy - half, cy + half
