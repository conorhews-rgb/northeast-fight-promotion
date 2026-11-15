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
| NFP 2 confirmed fights (home and events) | `src/partials/nfp2-card.html` |
| Fight night bonus amounts | `src/partials/bonuses.html` |
| NFP 1 results | `tools/make-fight-card.py` (writes `src/partials/fight-card.html`) |
| Fighter head squares | `tools/make-fighter-headshots.py` |
| `<head>`, meta tags, SEO | `src/partials/head.html` |
| The inbox every form sends to | `SITE["INBOX"]` in `build.py` |
| Colours, type, motion | `assets/css/site.css` |
| Countdown, reveals, forms | `assets/js/site.js` |

Each page in `src/pages/` opens with a JSON config comment setting its slug, `<title>`
and meta description. `{{> name}}` pulls in `src/partials/name.html`.

## Where things stand (Nov 2026)

- **NFP 1** ran Sat Oct 24 2026 at Nashua Community College. Results, champions and
  fight photos are on the site.
- **NFP 2** is Sat March 27 2027 at the Sheraton Hotel, Nashua. It leads the home page.
  The first fight is Kim vs Cetoute for the NFP 145 lb Muay Thai Championship. Add each
  new fight to `src/partials/nfp2-card.html`, cut its head squares with
  `tools/make-fighter-headshots.py`, and add a card to `src/pages/news.html`.
- **Tickets.** NFP 2 tickets are not on sale. `SITE["TICKETS"]` in `build.py` still
  points at the NFP 1 TicketSpice page and nothing on the site links to it. Change it,
  and the `NFP 1` eyebrow in `src/partials/tickets.html`, when NFP 2 goes on sale.
- **Still placeholders.** All four footer social icons point at `#`. Shop prices are
  placeholders and the shop has no store behind it.

## Forms

Every form posts to Web3Forms, which emails the submission to `SITE["INBOX"]` with the
visitor's address as reply-to. The access key is `SITE["FORM_KEY"]` in `build.py`. If the
post fails or takes longer than 12 seconds, the visitor's mail app opens with the message
pre-filled instead (`assets/js/site.js` section 9).

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

Live on GitHub Pages from the `main` branch root:

- Repo: <https://github.com/conorhews-rgb/northeast-fight-promotion>
- Site: <https://nfpfights.com>
- Fallback: <https://conorhews-rgb.github.io/northeast-fight-promotion/>

To publish a change, edit `src/`, rebuild, then push. Pages redeploys on its own, usually
within a minute:

```bash
cd ~/northeast-fight-promotion
python3 build.py
git add -A && git commit -m "Describe the change" && git push
```

### The custom domain

`nfpfights.com` is registered at GoDaddy and points here. The `CNAME` file at the project
root is what tells Pages to answer for it, so **do not delete it**: every `git add -A`
keeps it, but a stray `rm` drops the site back to the github.io URL.

DNS at GoDaddy, set 6 Sep 2026:

| Type | Name | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153, .109.153, .110.153, .111.153 |
| CNAME | www | conorhews-rgb.github.io |

The `pay`, `_domainconnect` and `_dmarc` records are GoDaddy's own and were left alone.
The original `A @` record pointed at a GoDaddy Website Builder site and was deleted.

Nothing needs a build step on the server. It is a folder of static files, so Netlify,
Cloudflare Pages or plain S3 would work just as well.
