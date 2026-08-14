# Northeast Fight Promotion website

Static site. No build dependencies beyond Python 3 (already on this Mac). Nothing to install.

```bash
python3 -m http.server 4602 --directory ~/northeast-fight-promotion
```

Then open <http://localhost:4602>.

## Editing

**Never edit the `.html` files in the project root.** They are generated. Edit the sources
in `src/`, then rebuild:

```bash
python3 ~/northeast-fight-promotion/build.py
```

| What you want to change | File |
| --- | --- |
| A page's content | `src/pages/<page>.html` |
| Nav, logo, mobile menu | `src/partials/header.html` |
| Footer links, socials, contact | `src/partials/footer.html` |
| The "Be first to know" band | `src/partials/notify.html` |
| `<head>`, meta tags, SEO | `src/partials/head.html` |
| The inbox every form sends to | `SITE["INBOX"]` in `build.py` |
| Colours, type, motion | `assets/css/site.css` |
| Countdown, reveals, forms | `assets/js/site.js` |

Each page in `src/pages/` opens with a JSON config comment setting its slug, `<title>`
and meta description. `{{> notify}}` pulls in the signup band.

## Placeholders to replace before launch

Search the source for `EDIT ME`. Every one is marked. The list:

- **Email.** `info@northeastfightpromotion.com` is invented. Set the real one in `build.py`.
- **Domain.** `northeastfightpromotion.com` appears in `robots.txt`, `sitemap.xml` and the
  form footer line in `assets/js/site.js`.
- **Socials.** All four footer icons point at `#`.
- **Event details.** Date (Fri 24 Oct 2026), venue (Nashua, NH) and the countdown target
  are all marked *(TBC)* on the page and in the copy. The countdown is set by
  `data-countdown="2026-10-24T19:00:00-04:00"` on the event cards in
  `src/pages/index.html` and `src/pages/events.html`.
- **News posts.** The six cards on `news.html` and the three on the home page are
  plausible placeholders, not real announcements.
- **Shop.** Six products with placeholder prices; the "Notify" links go to the drop
  signup form, not a store.
- **Card imagery.** Every card currently uses the logo on a gradient. Drop real fight
  photos into `assets/img/` and swap the `<img>` in the relevant `src/pages/` file.

## Forms

There's no backend. Every form opens a pre-filled email in the visitor's mail app
(`data-mailto` on the `<form>`, handled in `assets/js/site.js`). That works from day one
with zero hosting cost.

To move to a real form handler later (Formspree, Netlify Forms, your own endpoint),
replace the `data-mailto` submit handler in `site.js` section 10 with a `fetch()` POST.
The field `name` attributes are already sensible.

## Assets

| File | What it is |
| --- | --- |
| `assets/img/nfp-logo.png` | The logo, unmodified |
| `assets/img/nfp-wordmark.png` | The NFP letters only, cropped for the nav bar |
| `assets/img/region.png` | New England silhouette lifted from the logo, smoothed |
| `assets/img/nh.png` | New Hampshire, flood-filled from the logo and tinted brand green |
| `assets/img/favicon.png`, `apple-touch-icon.png` | Generated from the logo |
| `assets/fonts/` | Barlow Condensed + Inter, self-hosted (latin subsets only, ~280 KB) |

Fonts are self-hosted so the site has zero third-party requests and works offline.

## Layout reference

Structure and type follow ufc.com: a thin header with nav left and the mark centred, a
featured hero with an overlapping content card and a numbered Top Stories rail, a centred
fight banner with the countdown box straddling its bottom edge, Upcoming/Past tabs over
event rows, and image-on-top cards with a short green accent bar above the meta line.
Buttons are hard rectangles with no rounding, matching UFC's 16px by 32px padding.

## Colours

Pulled directly from the logo:

| Token | Value | Where it came from |
| --- | --- | --- |
| `--green` | `#0F9A0F` | the "P" and "NORTHEAST" |
| `--moss` | `#4D9726` | the New England map |
| `--green-bright` / `--green-glow` | `#16C216` / `#2CE62C` | derived, for hovers and glows |

## Deploying

It is a folder of static files, so any host works. GitHub Pages, Netlify drop, Cloudflare
Pages, or plain S3. Upload everything except `src/`, `build.py` and this README (or
upload them too; they're harmless).
