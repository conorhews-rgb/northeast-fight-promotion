#!/usr/bin/env python3
"""Render the NFP 1 recap posts, eleven 1080x1350 PNGs, from Paperview's gallery.

Photos are pulled from Pixieset's image CDN by key and cached in the temp dir,
so nothing large lands in the repo. Results and names mirror the fight card in
src/partials/fight-card.html. Type is the site's Barlow Condensed.

Run from the repo root:
    python3 tools/make-recap-posts.py OUT_DIR [POST_NUMBER ...]

A photo's key is the 32-character hex name in its gallery image URL:
images.pixieset.com/922645521/<key>-xlarge.jpg
"""
import concurrent.futures as cf
import os, sys, tempfile, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

out = sys.argv[1]
ONLY = {int(a) for a in sys.argv[2:]}
W, H = 1080, 1350
F = "assets/fonts/BarlowCondensed-{}-latin.woff2"
WHITE, MUTED, GREEN, GREEN_DK = (255, 255, 255), (164, 172, 166), (22, 194, 22), (15, 154, 15)
LOGO = Image.open("assets/img/nfp-logo-alpha.png").convert("RGBA")
CREDIT = "PHOTOS: PAPERVIEW PRODUCTIONS"
CDN = "https://images.pixieset.com/922645521/{}-{}.jpg"
CACHE = os.path.join(tempfile.gettempdir(), "nfp-photos")

PHOTOS = {  # name: Pixieset key, gallery set in the comment
    "barry-belt":        "53456eeaa7f22c8bea0d370084325068",  # barryvsteauge, portrait
    "barry-straight":    "115f98dd24bfe40b89455b60d4b8c8eb",  # barryvsteauge
    "walk-gold":         "b1f8487119e3d900de56e3cf42f1d575",  # barryvsteauge
    "walsh-belt":        "1577ded5b9ab168e28f7f4ac3b6ee5ce",  # walshvszahir, portrait
    "walsh-kick":        "5323b6955abf1c4aaa6edeaa3ecfe2f3",  # walshvszahir
    "walk-red":          "5e47f4150a28af43c8f9c6c04f69e980",  # walshvszahir
    "ferri-punch":       "cb4063ec7069514c6157524bb1e5c1af",  # ferrivssmythe
    "ferri-punch-close": "8bb867b3ea172dbcf4040e4188527e29",  # ferrivssmythe
    "kim-low-angle":     "9eaeb9c3f95db0a04aee6da557ff8442",  # kimvscolon
    "walk-blue":         "7f14224e2c4d2967e43c618fc69ea690",  # cetoutevsduffy
    "cetoute-kick":      "7b85b137caec3f410b2ea6f7c66924c5",  # cetoutevsduffy
    "corner-red":        "24183e35282688cb8a65c7260041274f",  # kellyvsstfelix
    "kelly-kick":        "1d8ca313ea78a377a666fc4d8143c422",  # kellyvsstfelix
    "drazhan-kick":      "54401115fbb02d377e1d651683cc0b3c",  # drazhanvsacuna
    "drazhan-knee":      "55e5ec3ef0562412a0c405875e8d8c1a",  # drazhanvsacuna
    "bernard-silva":     "b56e80910b391537ca3ddb275c929cbd",  # bernardvssilva
    "pacy-juarez":       "7e19cb6e37d1dcb3e3f4bdfbaee19feb",  # pacyvsjuarez
    "connerton-stocker": "aa54670386d6e9cf4992e92c4b567af2",  # connertonvsstocker
    "mackey-burbach":    "832c9bca4e4b4115c57332fb9d57e38a",  # mackeyvsburbach
    "round-1-card":      "f150bf85615cd5a9b288bb8d7a2cb1af",  # extras
}

# every 8th photo of the gallery, in gallery order, for the 766 PHOTOS mosaic
MOSAIC = """
    ddc75e8342167e8656eb541ba68ac500 2f867bdf74b838dd3855fdfb0b96d9bb fadf96321f76deefdc2a102ca57d8066
    4b71288a0a7595d04f6accea0d925de8 a0f4a5465a5f34bf1fb2e42b7b179fe7 30741b1d98eef439f97465f541779e38
    4a5e7af41ed617e5e80224ffb793f369 ba215ccd812fd259d0ae08e5b7341fad 78b326da2f361f07b1ca005b18004a1b
    a4d70cbfc3399514ac0c99c76deab590 87b7ff5f076b0248cdee2323a84328a7 ff15519a0d81f2b9721c304d6394e2fc
    a1dc9d82450ff907c16639d85584cc60 64321def2a1a092ef06129c084e39e81 ea7cd72124acf734c4953b78f5a9494d
    053e88a5a3acac22636aed81fadfe0a7 6d4362eb057eca71cfb118634a8b2317 88a3e77cdaf3358504902cfa8b0cc05d
    cbd3b87ea321aae95a77a5e855f80ef9 7d0be31c99feac58853f3782c533ddb0 afc8ce15f4f8a7f4444fc642ed70bbc6
    f43a855e87d235948f56709a5b176927 b8ccf674ddfb316168569ccf5d817dd9 25bc5cb5cf8d60cc4d666fbd57105845
    c49590090b85bc7707283b982be9814d 17427d24ed2e1adb6208f6e90d53ff25 80766165b7c8e8a509b06c139866f811
    0071b469f3f980d3b256017a82413e0f 5af1cee8e97a1fc32bd71f3e5cd0ba74 18f9a41d4390a16f7dcb36776580ce4e
    0d4e31dc7aa51491b29a0314a405f996 165684b6ed49c34c8e147a6d895b7835 98c259be78cc666f236adf94a2fe39b4
    bb5ea541539856f2f755dc9fc5c26489 1577ded5b9ab168e28f7f4ac3b6ee5ce 6baadd0df9261936c9cd0ad8732043e1
    6242fd483fced2b2ce44e1d6f9ad15af 3a124770ac527434d908ed22c8f41f1c ccf33fa7cb6c261f3513b92c2b9b333c
    9a7df08eed5e503935d28b795681a433 45421695841c87c6d35d9dee63427d6a 152b2a0be4de5d2fc6dd891469b63e31
    917c59dddfc922ab453b97623d67b451 a9e004a99ddfa9df163f243dfe967ea0 2d072e1de2b0871fa4c7493e90a8092f
    7723dc316fb903a287e90d50d2a5d893 5f45738f3addd2f55f0c89971947bb00 b886c0e55654321696b2c76db0ca6704
    6b7221ada21eeff5551e4e8f4d26dcdb fcf82e6ee216792c58939b4ec6a36672 de6cd1e291a0dbb0a7e7827aa39d5bb5
    5dd845ad3d40ff457292c5427703526c a98f359fdd1c76b5e3b5b7c885c0dc37 2c4b83bab36fe193f1a37b3ad52f73ce
    34228c26dbd91d4aa3bf2ef947f72626 5f3661a0c94d1672d285bf96ed8d8ed1 a4f738f4204b6e8a7175cd3d1196e6de
    6dab6d7ab29d5cb5fd24ba8e2bc6a353 712d031467a425e2d0f8d48df5b9eead cb2135080c7c9ee154756e6fcced1a68
    9a4932244c07084d57eaec337792a304 8b93c4d1335ff136ef2070ce34c0ce18 8bb98073c1d8f3aab85f669c6ba58f73
    a08ea0b8ab16073c0797861f7d6024e1 b47f8dfff38b33393281a766c6e36703 2c75cbb978601ff0983aad6ab84d2e15
    2f503d23d295f62395b1a010bad482e5 2fbb4e8ca106806ef97140c33960fa5d 70ff98d6e78806884625042c84828cdb
    09fd5a69e5a67bcdc01b31e358d0e045 70c4e953f46fabaefa0af474c05bdf74 56cd407c65752fe98e1d9ff639132691
    56e0f14571454f29a6af07e3191e7489 4e2a177b03e3c16b86bd3787fcfabb86 8f4badb5deb531f755d9ad1eea123588
    19ba3314798d3b2f45c1ba981e95961b f5867d1fa5d48c291fee6f57ff189dce df7d4cb52316f62fb7d860dad954945a
    e7e080a7b6fd2236446889db93863d7a 2940926333bde87aad7cb135bb9382b6 f0992d5247138b29858dccce08926a98
    492202f01cb7315b78ad2a479ab9cf98 caf696ec69c0a07ff148e2220f05f4cb c3fa9a3de60f99575a55e1b0d2887b2d
    48f667e1c90907b479ca8f29eb27a55a f9fd95964f64be1cb9413aa847c47014 ae75e189e2def1a37c4056744f6b6c60
    faf34ab6cd21f6c6d42572134e5d2ee8 ea8e40997200a633ebf6f32732b94a1d 6b8a5992fe79917e1343e10277b05c95
    95206cfebcbcf9dc23012d88ed88a115 fdb5dc6907f6e104fad4897b8cb8896f 4ccbe41eefdb9bc59b07d004d0605a8d
    53cd1df748f11d3f51561561e9d4f0ba d9f7bebf897585816e673088297fa22f f755e7c820e2bb978f5c3327eac7bc2e
""".split()

RESULTS = [  # (winner or first named, loser or second named, method, title fight)
    ("PRO BOXING", [
        ("CONNOR BARRY", "PAUL TEAGUE", "TKO RD2", True),
        ("JAKE FERRI", "TYLER SMYTHE", "UD", False)]),
    ("AMATEUR KICKBOXING", [
        ("VICTORIA WALSH", "MARIA ZAHIR", "UD", True),
        ("MIKE FAGAN", "JAMES JOHNSON", "TKO RD1", False),
        ("ARMANI KIM", "NATE COLON", "UD", False),
        ("JEFF CETOUTE", "TOM DUFFY", "UD", False),
        ("JOSH KELLY", "JEAN ST. FELIX", "UD", False),
        ("KYRYLO DRAZHAN", "ANDREW ACUNA", "UD", False)]),
    ("GRAPPLING", [
        ("BEN BERNARD", "RAMON SILVA", "DRAW", False),
        ("BRUCE PACY", "KRIS JUAREZ", "DRAW", False),
        ("JULIAN CONNERTON", "OWEN STOCKER", "DRAW", False),
        ("SHAYNE MACKEY", "BLANE BURBACH", "DRAW", False)]),
]


def fetch(key, size):
    """Cached path to a gallery photo; xxlarge is 1600 wide, medium 360."""
    path = os.path.join(CACHE, f"{key}-{size}.jpg")
    if not os.path.exists(path):
        with urllib.request.urlopen(CDN.format(key, size), timeout=30) as r:
            data = r.read()
        with open(path + ".part", "wb") as f:
            f.write(data)
        os.replace(path + ".part", path)                # no half-written files in the cache
    return path


def font(w, px): return ImageFont.truetype(F.format(w), int(px))
def photo(name): return Image.open(fetch(PHOTOS[name], "xxlarge")).convert("RGB")


def cover(im, w, h, fx=.5, fy=.5, zoom=1.0):
    """Scale to fill w x h (times zoom), then crop around the focal point (fx, fy as fractions)."""
    s = max(w / im.width, h / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = min(max(round(fx * im.width - w / 2), 0), im.width - w)
    y = min(max(round(fy * im.height - h / 2), 0), im.height - h)
    return im.crop((x, y, x + w, y + h)).convert("RGBA")


def poly_mask(pts):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


class Post:
    def __init__(self):
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    @property
    def d(self): return ImageDraw.Draw(self.im)

    def put(self, tile, xy=(0, 0), mask=None):
        if mask is None:
            self.im.alpha_composite(tile, xy)
        else:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.paste(tile, xy)
            self.im.paste(layer, (0, 0), mask)

    def shade(self, y0, y1, a0, a1, x0=0, x1=W):
        """Black vertical gradient, alpha a0 at y0 to a1 at y1."""
        h = abs(y1 - y0)
        g = Image.new("L", (1, h))
        g.putdata([int(a0 + (a1 - a0) * i / max(1, h - 1)) for i in range(h)])
        g = g.resize((x1 - x0, h))
        self.im.alpha_composite(Image.merge("RGBA", (*[Image.new("L", g.size, 0)] * 3, g)), (x0, min(y0, y1)))

    def width(self, runs):
        return sum(self.d.textlength(t, font=f) for t, f, _ in runs)

    def text(self, x, y, runs, align="l", shadow=0):
        """Draw runs [(text, font, fill)] on one baseline; align l / c / r about x."""
        w = self.width(runs)
        x = x - w / 2 if align == "c" else x - w if align == "r" else x
        if shadow:
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); cx = x
            for t, f, _ in runs:
                sd.text((cx + 2, y + 3), t, font=f, fill=(0, 0, 0, 235), anchor="ls"); cx += sd.textlength(t, font=f)
            self.im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow)))
        d = self.d
        for t, f, fill in runs:
            d.text((x, y), t, font=f, fill=fill, anchor="ls"); x += d.textlength(t, font=f)

    def fit(self, runs_fn, px, maxw):
        """runs_fn(px) at the largest px that fits in maxw."""
        while px > 10 and self.width(runs_fn(px)) > maxw: px -= 1
        return runs_fn(px)

    def logo(self, x, y, w=110, align="c"):
        lg = LOGO.resize((w, round(w * LOGO.height / LOGO.width)), Image.LANCZOS)
        x = x - w // 2 if align == "c" else x - w if align == "r" else x
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        glow.paste(Image.new("RGBA", lg.size, (0, 0, 0, 170)), (x, y), lg)
        self.im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
        self.im.alpha_composite(lg, (x, y))

    def credit(self, x, y, align="r"):
        self.text(x, y, [(CREDIT, font("600", 17), (255, 255, 255, 150))], align, shadow=3)

    def save(self, name):
        path = os.path.join(out, name + ".png")
        self.im.convert("RGB").save(path, optimize=True)
        print("wrote", path)


def new_champions():
    p = Post()
    top_x, bot_x = 600, 480                             # diagonal seam, Barry left, Walsh right
    # matching portraits at the same zoom: eyes level near the top, both belt plates clear of the seam and headline
    p.put(cover(photo("barry-belt"), 640, H, fx=.601, fy=.503, zoom=1.15))
    p.put(cover(photo("walsh-belt"), 640, H, fx=.393, fy=.478, zoom=1.15), (440, 0),
          poly_mask([(top_x, 0), (W, 0), (W, H), (bot_x, H)]))
    p.d.polygon([(top_x - 5, 0), (top_x + 5, 0), (bot_x + 5, H), (bot_x - 5, H)], fill=GREEN)
    p.shade(0, 190, 160, 0)
    p.shade(780, H, 0, 245)
    p.logo(592, 24, 112)                                # sits on the seam
    p.text(W / 2, 1060, [("AND ", font("800i", 200), WHITE), ("NEW", font("800i", 200), GREEN)], "c", shadow=8)
    for cx, name, div, how in ((270, "CONNOR BARRY", "MIDDLEWEIGHT CHAMPION", "TKO  |  RD 2"),
                               (810, "VICTORIA WALSH", "BANTAMWEIGHT CHAMPION", "UNANIMOUS DECISION")):
        p.text(cx, 1140, p.fit(lambda px: [(name, font("800i", px), WHITE)], 56, 470), "c", shadow=6)
        p.text(cx, 1182, [(div, font("700", 23), MUTED)], "c")
        p.text(cx, 1220, [(how, font("800i", 26), GREEN)], "c")
    p.text(W / 2, 1300, [("NFP 1  |  SAT OCT 24  |  NASHUA, NH", font("700", 21), MUTED)], "c")
    p.credit(W - 28, H - 18)
    p.save("01-new-champions")


def main_event_tko():
    p = Post()
    p.put(cover(photo("barry-straight"), W, 760), (0, 140))
    p.shade(140, 260, 255, 0)
    p.shade(700, 900, 0, 255)
    p.text(44, 76, [("MAIN EVENT", font("800i", 46), GREEN)])
    p.text(44, 112, [("NFP MIDDLEWEIGHT TITLE  |  PRO BOXING", font("700", 23), MUTED)])
    p.logo(W - 40, 22, 100, align="r")
    p.text(36, 1078, [("TKO", font("800i", 300), WHITE)], shadow=10)
    p.text(44, 1190, [("ROUND 2", font("800i", 120), GREEN)])
    p.text(W - 44, 928, [("CONNOR", font("800i", 64), WHITE)], "r", shadow=6)
    p.text(W - 44, 990, [("BARRY", font("800i", 64), WHITE)], "r", shadow=6)
    p.text(W - 44, 1038, [("DEF. PAUL TEAGUE", font("700", 30), MUTED)], "r")
    p.text(W - 44, 1078, [("NEW CHAMPION", font("800i", 30), GREEN)], "r")
    p.credit(W - 28, H - 22)
    p.save("02-main-event-tko")


def results():
    p = Post()
    p.put(cover(photo("drazhan-knee"), W, 540, fy=.42))
    p.shade(0, 160, 150, 0)
    p.shade(300, 540, 0, 255)
    p.logo(W // 2, 22, 104)
    p.text(W / 2, 470, [("NFP 1 ", font("800i", 140), GREEN), ("RESULTS", font("800i", 140), WHITE)], "c", shadow=8)
    p.text(W / 2, 512, [("SAT OCT 24  |  NASHUA, NH", font("700", 23), MUTED)], "c")
    name, small, meth = font("800i", 33), font("700", 22), font("800i", 29)
    y, L, R = 560, 56, W - 56
    for group, bouts in RESULTS:
        p.text(L, y + 22, [(group, font("800", 21), GREEN_DK)])
        y += 22
        for win, lose, how, title in bouts:
            y += 47
            draw = how == "DRAW"
            p.text(L, y, [(win, name, WHITE), ("  VS  " if draw else "  DEF.  ", small, MUTED), (lose, name, WHITE if draw else MUTED)])
            p.text(R, y, [(how, meth, MUTED if draw else GREEN)], "r")
            if title:
                tw = p.d.textlength("TITLE", font=font("800", 18)) + 16
                x1 = R - p.d.textlength(how, font=meth) - 14
                p.d.rounded_rectangle((x1 - tw, y - 24, x1, y - 2), 4, fill=GREEN)
                p.text(x1 - tw / 2, y - 6, [("TITLE", font("800", 18), (0, 0, 0))], "c")
            p.d.line((L, y + 14, R, y + 14), fill=(38, 42, 40), width=1)
        y += 30
    p.credit(W - 28, H - 16)
    p.save("03-results")


def the_walk():
    p = Post()
    gap, sw = 6, (W - 12) // 3
    for i, (name, fx) in enumerate((("walk-gold", .47), ("walk-red", .49), ("walk-blue", .48))):
        p.put(cover(photo(name), sw, H, fx=fx), (i * (sw + gap), 0))
    p.shade(0, 200, 170, 0)
    p.shade(820, H, 0, 248)
    p.logo(W // 2, 24, 104)
    p.text(W / 2, 1180, [("THE WALK", font("800i", 230), WHITE)], "c", shadow=10)
    p.text(W / 2, 1248, [("NFP 1  |  NASHUA, NH", font("700", 28), MUTED)], "c")
    p.credit(W / 2, H - 22, "c")
    p.save("04-the-walk")


def corner():
    p = Post()
    p.put(cover(photo("corner-red"), W, H, fx=.52))
    p.shade(0, 220, 150, 0)
    p.shade(760, H, 0, 250)
    p.logo(40, 26, 104, align="l")
    p.credit(W - 28, 46)
    p.text(48, 1130, [("LISTEN TO", font("800i", 160), WHITE)], shadow=8)
    p.text(48, 1280, p.fit(lambda px: [("YOUR CORNER", font("800i", px), GREEN)], 160, W - 96), shadow=8)
    p.save("05-listen-to-your-corner")


def grappling():
    p = Post()
    top, gap = 390, 6
    tw, th = (W - gap) // 2, (H - top - gap) // 2
    tiles = [("bernard-silva", .45, .5, "BERNARD VS SILVA", "NO-GI"), ("pacy-juarez", .55, .5, "PACY VS JUAREZ", "GI"),
             ("connerton-stocker", .45, .62, "CONNERTON VS STOCKER", "NO-GI"), ("mackey-burbach", .52, .55, "MACKEY VS BURBACH", "NO-GI")]
    for i, (name, fx, fy, label, rules) in enumerate(tiles):
        x, y = (i % 2) * (tw + gap), top + (i // 2) * (th + gap)
        p.put(cover(photo(name), tw, th, fx=fx, fy=fy), (x, y))
        p.shade(y + th - 120, y + th, 0, 200, x, x + tw)
        right = i % 2                                   # labels on the outer corners, clear of the badge
        p.text(x + tw - 22 if right else x + 22, y + th - 22,
               [(label, font("800i", 30), WHITE), ("  " + rules, font("700", 20), GREEN)], "r" if right else "l", shadow=4)
    p.text(44, 215, p.fit(lambda px: [("NOBODY TAPPED", font("800i", px), GREEN)], 200, W - 88))
    p.text(48, 296, p.fit(lambda px: [("ALL 4 GRAPPLING MATCHES WENT TO A DRAW", font("800i", px), WHITE)], 50, W - 96))
    p.text(W - 48, 368, [(CREDIT, font("600", 17), MUTED)], "r")
    cx, cy = W // 2, top + th + gap // 2               # logo badge where the four tiles meet
    p.d.ellipse((cx - 74, cy - 74, cx + 74, cy + 74), fill=(0, 0, 0), outline=GREEN_DK, width=4)
    p.logo(cx, cy - 44, 100)
    p.save("06-nobody-tapped")


def kicks_or_hands():
    p = Post()
    yl, yr = 820, 560                                   # seam: left edge y, right edge y
    p.put(cover(photo("drazhan-kick"), W, 830), (0, 80))  # dropped 80px so KICKS clears the heads
    p.put(cover(photo("ferri-punch"), W, 800, fy=.42), (0, 550), poly_mask([(0, yl), (W, yr), (W, H), (0, H)]))
    p.d.polygon([(0, yl - 6), (W, yr - 6), (W, yr + 6), (0, yl + 6)], fill=GREEN)
    p.shade(80, 300, 255, 0)
    p.shade(1080, H, 0, 230)
    p.logo(W - 40, 26, 96, align="r")
    p.text(40, 178, [("KICKS", font("800i", 176), WHITE)], shadow=10)
    p.text(48, 216, [("DRAZHAN VS ACUNA", font("700", 24), MUTED)], shadow=4)
    p.text(W - 40, 1232, [("HANDS", font("800i", 210), WHITE)], "r", shadow=10)
    p.text(W - 48, 1062, [("FERRI VS SMYTHE", font("700", 24), MUTED)], "r", shadow=4)
    cx, cy = W // 2, (yl + yr) // 2
    p.d.ellipse((cx - 68, cy - 68, cx + 68, cy + 68), fill=GREEN)
    p.text(cx, cy + 26, [("OR", font("800i", 76), (0, 0, 0))], "c")
    p.credit(W - 28, H - 18)
    p.save("07-kicks-or-hands")


def shot_of_the_night():
    p = Post()
    head, gap = 176, 5
    sh = (H - head - 2 * gap) // 3
    strips = [("kim-low-angle", .44, "KIM VS COLON"), ("walsh-kick", .42, "WALSH VS ZAHIR"), ("cetoute-kick", .42, "CETOUTE VS DUFFY")]
    for i, (name, fy, label) in enumerate(strips):
        y = head + i * (sh + gap)
        p.put(cover(photo(name), W, sh, fy=fy), (0, y))
        p.shade(y + sh - 110, y + sh, 0, 170)
        p.text(30, y + sh - 18, [(str(i + 1), font("800i", 150), GREEN)], shadow=8)
        p.text(W - 30, y + sh - 22, [(label, font("800i", 30), WHITE)], "r", shadow=5)
    p.text(40, 98, [("SHOT OF THE NIGHT", font("800i", 92), WHITE), ("?", font("800i", 92), GREEN)])
    p.text(42, 150, [("1, 2 OR 3?", font("800i", 40), GREEN)])
    p.logo(W - 40, 24, 96, align="r")
    p.text(W - 40, 158, [(CREDIT, font("600", 17), MUTED)], "r")
    p.save("08-shot-of-the-night")


def every_frame():
    p = Post()
    cols, rows, g = 8, 12, 3
    tw, th = (W - (cols - 1) * g) / cols, (H - (rows - 1) * g) / rows
    for i, key in enumerate(MOSAIC):
        x, y = round((i % cols) * (tw + g)), round((i // cols) * (th + g))
        p.put(cover(Image.open(fetch(key, "medium")).convert("RGB"), round(tw), round(th), fy=.4), (x, y))
    p.im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
    b0, b1 = 395, 955
    p.shade(b0 - 120, b0, 0, 200); p.shade(b1, b1 + 120, 200, 0)
    p.d.rectangle((0, b0, W, b1), fill=(0, 0, 0))
    p.d.rectangle((0, b0, W, b0 + 5), fill=GREEN_DK)
    p.d.rectangle((0, b1 - 5, W, b1), fill=GREEN_DK)
    p.logo(W // 2, b0 + 50, 104)
    p.text(W / 2, b0 + 350, [("766", font("800i", 230), GREEN)], "c")
    p.text(W / 2, b0 + 425, [("PHOTOS FROM NFP 1 ARE UP", font("800i", 64), WHITE)], "c")
    p.text(W / 2, b0 + 495, [("NFPFIGHTS.COM/PHOTOS", font("800i", 42), GREEN)], "c")
    p.text(W / 2, H - 22, [("SHOT BY PAPERVIEW PRODUCTIONS", font("800i", 26), WHITE)], "c", shadow=6)
    p.save("09-766-photos")


def that_was_round_1():
    p = Post()
    ph = 778                                            # card and shoulders, cropped above the waist
    p.put(photo("round-1-card").crop((343, 30, 1343, 750)).resize((W, ph), Image.LANCZOS).convert("RGBA"))
    p.shade(0, 170, 150, 0)
    p.shade(ph - 220, ph, 0, 255)
    p.logo(40, 24, 100, align="l")
    p.credit(W - 28, 44)
    p.text(W / 2, 905, [("THAT WAS", font("800i", 120), WHITE)], "c", shadow=8)
    p.text(W / 2, 1110, [("ROUND 1", font("800i", 240), GREEN)], "c")
    p.text(W / 2, 1190, [("NFP 2 IS COMING", font("800i", 44), WHITE)], "c")
    p.d.rectangle((W / 2 - 300, 1232, W / 2 + 300, 1302), outline=GREEN_DK, width=3)
    p.text(W / 2, 1281, [("GET ON THE LIST  |  NFPFIGHTS.COM", font("800i", 38), WHITE)], "c")
    p.save("10-that-was-round-1")


def who_next():
    p = Post()
    panel, bar = H // 2, 176                            # two shots stacked, headline bar on the seam
    p.put(cover(photo("kelly-kick"), W, panel, fy=.51))
    p.put(cover(photo("ferri-punch-close"), W, panel, fy=0), (0, panel))
    by0, by1 = panel - bar // 2, panel + bar // 2
    p.shade(0, 190, 150, 0)
    p.shade(by0 - 110, by0, 0, 170)
    p.shade(by1, by1 + 110, 170, 0)
    p.shade(H - 200, H, 0, 215)
    p.d.rectangle((0, by0, W, by1), fill=(0, 0, 0))
    p.d.rectangle((0, by0, W, by0 + 5), fill=GREEN_DK)
    p.d.rectangle((0, by1 - 5, W, by1), fill=GREEN_DK)
    runs = p.fit(lambda px: [("WHO SHOULD BE ON ", font("800i", px), WHITE), ("NFP 2?", font("800i", px), GREEN)], 140, W - 90)
    cap = runs[0][1].getbbox("H", anchor="ls")[1]       # negative cap height
    p.text(W / 2, panel - cap / 2, runs, "c")           # caps optically centred in the bar
    p.logo(W // 2, 26, 128)
    p.text(W / 2, H - 52, [("TAG ’EM BELOW", font("800i", 38), GREEN)], "c", shadow=6)
    p.save("11-who-should-be-on-nfp-2")


POSTS = [new_champions, main_event_tko, results, the_walk, corner, grappling,
         kicks_or_hands, shot_of_the_night, every_frame, that_was_round_1, who_next]

os.makedirs(out, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
todo = [fn for i, fn in enumerate(POSTS, 1) if not ONLY or i in ONLY]
# warm the cache in parallel before rendering
keys = [(k, "xxlarge") for k in PHOTOS.values()] + ([(k, "medium") for k in MOSAIC] if every_frame in todo else [])
with cf.ThreadPoolExecutor(8) as ex:
    list(ex.map(lambda ks: fetch(*ks), keys))
for fn in todo:
    fn()
