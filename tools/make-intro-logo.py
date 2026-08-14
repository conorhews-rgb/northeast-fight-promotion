#!/usr/bin/env python3
"""Build assets/img/nfp-logo-alpha.png from assets/img/nfp-logo.png.

The source logo sits on an opaque black plate, which is why it is shown with
mix-blend-mode: screen everywhere on the site. The intro animation flies the
mark across a page that is fading in underneath it, so blending is no use
there: the moment the black backdrop goes, the plate composites as a black
box. This bakes the same result into an alpha channel instead.

screen over a backdrop B gives  S + B*(1 - S).
straight alpha compositing gives C*a + B*(1 - a).
So take a = max(R,G,B) and unpremultiply the colour by it, and the two match
exactly on the dominant channel and stay very close elsewhere over a dark
backdrop, which is all this logo is ever shown against.

Run from the repo root:  python3 tools/make-intro-logo.py
"""
from PIL import Image

SRC = "assets/img/nfp-logo.png"
OUT = "assets/img/nfp-logo-alpha.png"

src = Image.open(SRC).convert("RGB")
w, h = src.size
out = Image.new("RGBA", (w, h))
sp, op = src.load(), out.load()

for y in range(h):
    for x in range(w):
        r, g, b = sp[x, y]
        a = max(r, g, b)
        if a == 0:
            op[x, y] = (0, 0, 0, 0)
        else:
            k = 255.0 / a
            op[x, y] = (
                min(255, int(r * k + 0.5)),
                min(255, int(g * k + 0.5)),
                min(255, int(b * k + 0.5)),
                a,
            )

out.save(OUT)
print("wrote %s (%dx%d)" % (OUT, w, h))
