#!/usr/bin/env python3
"""Cut square fighter headshots out of the fight posters.

Each poster has the venue line above the fighters' heads and the discipline
line across their chests, both in white type that runs behind the faces. A
crop that touches either band comes out with stray letters in it, so the
window is found from the pixels: scan a strip between the two fighters, where
there is only dark arena behind, for rows of near white, and fit the square
between the last venue row and the first discipline row.

Face centres are measured by eye off a gridded render of each poster, in
1080-wide poster space. Posters that are not 1080 wide are scaled to match.

Run from the repo root:  python3 tools/make-fighter-headshots.py
"""
from PIL import Image

POSTERS = "assets/img/posters"
OUT = "assets/img/fighters"
SIZE = 320          # output edge in px
PAD = 10            # clearance from each text band

# poster file -> [(slug, face centre x in 1080 space), left then right]
CARD = {
    "nfp1-barry-teague.webp":     [("connor-barry", 302), ("paul-teague", 768)],
    "nfp1-ferri-smythe.webp":     [("jake-ferri", 318), ("tyler-smythe", 783)],
    "nfp1-stocker-connerton.webp": [("owen-stocker", 330), ("julian-connerton", 800)],
    "nfp1-bernard-silva.jpg":     [("ben-bernard", 323), ("ramon-silva", 790)],
    "nfp1-pacy-juarez.jpg":       [("bruce-pacy", 311), ("kris-juarez", 777)],
    "nfp1-zahir-walsh.webp":      [("maria-zahir", 318), ("victoria-walsh", 782)],
    "nfp1-silva-medina.webp":     [("jeff-silva", 290), ("john-medina", 790)],
    "nfp1-mackey-burbach.webp":   [("shayne-mackey", 303), ("blane-burbach", 802)],
    "nfp1-johnson-fagan.webp":    [("james-johnson", 310), ("mike-fagan", 794)],
    "nfp1-acuna-drazhan.webp":    [("andrew-acuna", 305), ("kyrylo-drazhan", 795)],
    "nfp1-cetoute-duffy.webp":    [("jeff-cetoute", 318), ("tom-duffy", 796)],
    "nfp1-colon-kim.webp":        [("nate-colon", 316), ("armani-kim", 792)],
    "nfp1-kelly-st-felix.webp":   [("josh-kelly", 300), ("jean-st-felix", 786)],
    "nfp1-molai-nash.webp":       [("moeketsi-molai", 330), ("connor-nash", 760)],
}


def text_rows(im):
    """Rows in 1080 space whose centre strip carries white type."""
    k = im.width / 1080.0
    px = im.load()
    x0, x1 = int(420 * k), int(660 * k)
    rows = []
    for y1080 in range(300, 761):
        y = int(y1080 * k)
        white = sum(1 for x in range(x0, x1) if min(px[x, y]) > 215)
        if white > 12 * k:
            rows.append(y1080)
    return rows


def main():
    for poster, fighters in CARD.items():
        im = Image.open(f"{POSTERS}/{poster}").convert("RGB")
        k = im.width / 1080.0
        rows = text_rows(im)
        above = [y for y in rows if y <= 400]
        below = [y for y in rows if y >= 600]
        if not above or not below:
            raise SystemExit(f"{poster}: could not find both text bands")
        top, bottom = max(above) + PAD, min(below) - PAD
        edge = bottom - top
        for slug, cx in fighters:
            box = tuple(round(v * k) for v in (cx - edge / 2, top, cx + edge / 2, bottom))
            shot = im.crop(box).resize((SIZE, SIZE), Image.LANCZOS)
            shot.save(f"{OUT}/{slug}.jpg", quality=86, optimize=True, progressive=True)
            print(f"  {slug:18s} window y {top}-{bottom} ({edge}px)  box {box}")


if __name__ == "__main__":
    main()
