#!/usr/bin/env python3
"""
Northeast Fight Promotion static site builder.

Assembles src/pages/*.html into flat HTML files at the project root using the
shared chrome in src/partials/. Run it after editing anything under src/:

    python3 build.py

Each page in src/pages/ starts with a JSON config comment:

    <!--{"slug": "events", "title": "...", "desc": "..."}-->

Body text supports two includes:
    {{> notify}}   the "be first to know" CTA band
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PARTIALS = ROOT / "src" / "partials"
PAGES = ROOT / "src" / "pages"

# ---- site-wide values -------------------------------------------------------
SITE = {
    # EDIT ME: the inbox every form on the site sends to
    "INBOX": "info@northeastfightpromotion.com",
}

CONFIG_RE = re.compile(r"^\s*<!--(\{.*?\})-->\s*", re.S)
INCLUDE_RE = re.compile(r"\{\{>\s*([a-z0-9_-]+)\s*\}\}")


def partial(name: str) -> str:
    return (PARTIALS / f"{name}.html").read_text()


def fill(text: str, **extra) -> str:
    values = dict(SITE, **extra)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def mark_active(html: str, slug: str) -> str:
    """Flag the current page in both nav menus."""
    target = f'href="{slug}.html"'
    return html.replace(target, f'{target} aria-current="page"')


def build_page(path: pathlib.Path) -> str:
    raw = path.read_text()
    match = CONFIG_RE.match(raw)
    if not match:
        sys.exit(f"{path.name}: missing leading <!--{{...}}--> config block")
    cfg = json.loads(match.group(1))
    body = raw[match.end():]

    body = INCLUDE_RE.sub(lambda m: partial(m.group(1)), body)
    body = fill(body)

    # Pages other than the home page link the header CTA back to the home anchor
    notify = "#notify" if cfg.get("notify_local", True) else "index.html#notify"

    html = "".join([
        fill(partial("head"), TITLE=cfg["title"], DESC=cfg["desc"]),
        fill(partial("header"), NOTIFY=notify),
        body,
        fill(partial("footer"), NOTIFY=notify),
    ])

    html = mark_active(html, cfg["slug"])
    out = ROOT / f"{cfg['slug']}.html"
    out.write_text(html)
    return out.name


def main() -> None:
    if not PAGES.exists():
        sys.exit("src/pages/ not found")
    built = sorted(build_page(p) for p in PAGES.glob("*.html"))
    print(f"built {len(built)} pages: " + ", ".join(built))


if __name__ == "__main__":
    main()
