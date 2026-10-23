#!/usr/bin/env python3
"""Build src/partials/fight-card.html, the Confirmed fights block.

The card lives in the BOUTS table below, in card order with the main event
first. Any bout with a tag (Main event, Co-main event, Title fight) renders
as a large featured card, the main event across the full width; everything
else follows smaller. Reorder the card or swap a fighter here, then:

    python3 tools/make-fight-card.py && python3 build.py

Headshots are assets/img/fighters/<slug>.jpg, cut from the posters by
tools/make-fighter-headshots.py.
"""

BOUTS = [
    # (tag or None, bout name, meta line, left fighter, right fighter)
    # fighter = (headshot slug, name, gym, ticket code)
    ("Main event", "NFP Middleweight Championship",
     'Professional boxing <span class="sep">/</span> 185 lbs',
     ("connor-barry", "Connor Barry", "Imperium Martial Arts", "BARRY"),
     ("paul-teague", "Paul Teague", "No Mercy MMA", "TEAGUE")),
    ("Co-main event", "Professional boxing", "135 lbs",
     ("jake-ferri", "Jake Ferri", "KTA", "FERRI"),
     ("tyler-smythe", "Tyler Smythe", "Nostos", "SMYTHE")),
    ("Title fight", "NFP Bantamweight Championship",
     'Amateur kickboxing <span class="sep">/</span> 135 lbs',
     ("maria-zahir", "Maria Zahir", "Hard Knocks Everett", "ZAHIR"),
     ("victoria-walsh", "Victoria Walsh", "Black Wolf Martial Arts", "WALSH")),
    # Running order follows the official NFP Fight Night 1 sheet, bout 10
    # down to bout 1. The sheet numbers bouts in the order they happen, so
    # the bottom of this list opens the night.
    # The poster prints this code as FAGEN although the name is Fagan. Kept as
    # printed, because it has to match the coupon configured in TicketSpice.
    (None, "Amateur kickboxing", "155 lbs",                          # 10
     ("james-johnson", "James Johnson", "KTA Nashua", "JOHNSON"),
     ("mike-fagan", "Mike Fagan", "Recon MMA", "FAGEN")),
    # Gym printed as Moongose on the poster and the official sheet alike.
    (None, "Amateur kickboxing", "150 lbs",                          # 9
     ("nate-colon", "Nate Colon", "Moongose Academy", "COLON"),
     ("armani-kim", "Armani Kim", "Gate City MMA", "KIM")),
    (None, "Amateur kickboxing", "145 lbs",                          # 8
     ("jeff-cetoute", "Jeff Cetoute", "Rajasi", "CETOUTE"),
     ("tom-duffy", "Tom Duffy", "F.A.A", "DUFFY")),
    (None, "Amateur kickboxing", "165 lbs",                          # 7
     ("josh-kelly", "Josh Kelly", "KTA Nashua", "KELLY"),
     ("jean-st-felix", "Jean St. Felix", "Song Khao Muay Thai", "ST.FELIX")),
    (None, "Amateur kickboxing", "155 lbs",                          # 6
     ("andrew-acuna", "Andrew Acuna", "Rajasi", "ACUNA"),
     ("kyrylo-drazhan", "Kyrylo Drazhan", "Recon MMA", "DRAZHAN")),
    # Bout 5 on the sheet, Molai vs Nash, was called off; awaiting confirmation.
    (None, "No-gi submission only", "205 lbs",                       # 4
     ("ben-bernard", "Ben Bernard", "KTA Nashua", "BERNARD"),
     ("ramon-silva", "Ramon Silva", "Team Link Hooksett", "RAMON")),
    (None, "Gi grappling", "Heavyweight",                            # 3
     ("bruce-pacy", "Bruce Pacy", "Limitless Pride", "PACY"),
     ("kris-juarez", "Kris Juarez", "Elements MMA", "JUAREZ")),
    # Connerton has the red corner on the sheet, so he takes the left.
    (None, "No-gi submission only", "170 lbs",                       # 2
     ("julian-connerton", "Julian Connerton", "Hook N Roll", "CONNERTON"),
     ("owen-stocker", "Owen Stocker", "Team Link Hooksett", "STOCKER")),
    (None, "No-gi submission only", "200 lbs",                       # 1
     ("shayne-mackey", "Shayne Mackey", "KTA Nashua", "MACKEY"),
     ("blane-burbach", "Blane Burbach", "Balance Point BJJ", "BURBACH")),
]

OUT = "src/partials/fight-card.html"


def corner(f):
    slug, name, gym, code = f
    return f'''          <div class="corner">
            <img src="assets/img/fighters/{slug}.jpg" alt="{name}" width="320" height="320" loading="lazy">
            <h3 class="fighter">{name}</h3>
            <p class="gym">{gym}</p>
            <p class="code">Code <b>{code}</b></p>
          </div>'''


def bout(b):
    tag, name, meta, left, right = b
    cls = "bout"
    if tag:
        cls += " bout--title"
    if tag == "Main event":
        cls += " bout--main"
    tag = f'\n          <span class="tag">{tag}</span>' if tag else ""
    return f'''      <article class="{cls}" data-reveal aria-label="{left[1]} versus {right[1]}">
        <header class="bout-head">{tag}
          <p class="bout-name">{name}</p>
          <p class="meta">{meta}</p>
        </header>
        <div class="bout-body">
{corner(left)}
          <span class="vs" aria-hidden="true">VS</span>
{corner(right)}
        </div>
      </article>'''


def main():
    titles = "\n".join(bout(b) for b in BOUTS if b[0])
    rest = "\n".join(bout(b) for b in BOUTS if not b[0])
    html = f'''<!-- ===================== CONFIRMED FIGHTS =====================
     Generated by tools/make-fight-card.py. Edit the table there, not this file.
     Listed in card order, main event first. -->
<div class="section-head">
  <div data-reveal>
    <span class="bar"></span>
    <h2>Confirmed fights</h2>
  </div>
  <p class="meta" data-reveal="right">NFP 1 <span class="sep">/</span> Sat, Oct 24 2026 <span class="sep">/</span> Nashua Community College</p>
</div>

<div class="bouts bouts--title" data-stagger="90">
{titles}
</div>

<div class="bouts bouts--card" data-stagger="80">
{rest}
</div>

<div class="card-cta" data-reveal>
  <p>Supporting a fighter? Enter their code in the <b>Coupon Code</b> box at checkout so they get the credit.</p>
  <a class="btn" href="{{{{TICKETS}}}}" data-tickets>Buy tickets</a>
</div>
'''
    with open(OUT, "w") as f:
        f.write(html)
    print(f"wrote {OUT}: {html.count('<article')} bouts")


if __name__ == "__main__":
    main()
