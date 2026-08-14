#!/usr/bin/env python3
"""Trace assets/img/region.png into src/partials/region-map.html.

region.png is a flat silhouette whose states are already separated by
transparent gaps, so each state falls out as its own connected component.
This walks the boundary of each one, simplifies it, and writes an inline SVG
with a path per state. Inline is the point: an <img> cannot be hovered a
state at a time, a path can.

Boundary walk: collect the unit edges between a solid pixel and a hollow
neighbour, wound consistently, then chain them head to tail into closed
loops. That is exact and always closes, unlike neighbourhood tracing which
goes wrong on diagonal pinches. Loops are then simplified with
Ramer-Douglas-Peucker.

Run from the repo root:  python3 tools/make-region-svg.py
"""
from PIL import Image
from collections import deque

SRC = "assets/img/region.png"
OUT = "src/partials/region-map.html"
ALPHA = 140      # solid/hollow cutoff
MIN_AREA = 400   # ignore speckle and stray islands
EPSILON = 1.4    # RDP tolerance in pixels

# Identified from component centroids; see the printout at the end.
NAMES = [
    ((406, 540), "new-york", "New York"),
    ((1016, 269), "maine", "Maine"),
    ((690, 444), "vermont", "Vermont"),
    ((800, 488), "new-hampshire", "New Hampshire"),
    ((758, 640), "massachusetts", "Massachusetts"),
]


def components(solid, w, h):
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if not solid[y][x] or seen[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            cells = set()
            sx = sy = 0
            while q:
                cx, cy = q.popleft()
                cells.add((cx, cy))
                sx += cx
                sy += cy
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and solid[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(cells) >= MIN_AREA:
                n = len(cells)
                out.append((n, cells, (sx // n, sy // n)))
    out.sort(key=lambda c: -c[0])
    return out


def loops(cells):
    """Closed boundary loops as lists of integer lattice points."""
    edges = {}
    for (x, y) in cells:
        if (x, y - 1) not in cells:
            edges.setdefault((x, y), []).append((x + 1, y))
        if (x + 1, y) not in cells:
            edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
        if (x, y + 1) not in cells:
            edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
        if (x - 1, y) not in cells:
            edges.setdefault((x, y + 1), []).append((x, y))

    found = []
    while edges:
        start = next(iter(edges))
        loop = [start]
        cur = start
        while True:
            nxts = edges.get(cur)
            if not nxts:
                break
            nxt = nxts.pop()
            if not nxts:
                del edges[cur]
            cur = nxt
            if cur == start:
                break
            loop.append(cur)
        if len(loop) > 8:
            found.append(loop)
    return found


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    ax, ay = pts[0]
    bx, by = pts[-1]
    dx, dy = bx - ax, by - ay
    span = (dx * dx + dy * dy) ** 0.5
    worst, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = (abs(dy * px - dx * py + bx * ay - by * ax) / span) if span else (
            ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5)
        if d > worst:
            worst, idx = d, i
    if worst > eps:
        left = rdp(pts[:idx + 1], eps)
        right = rdp(pts[idx:], eps)
        return left[:-1] + right
    return [pts[0], pts[-1]]


def path_d(ls):
    parts = []
    for loop in ls:
        simple = rdp(loop + [loop[0]], EPSILON)
        if len(simple) < 4:
            continue
        parts.append("M" + " L".join("%d %d" % p for p in simple[:-1]) + " Z")
    return " ".join(parts)


def main():
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    a = im.getchannel("A").load()
    solid = [[a[x, y] > ALPHA for x in range(w)] for y in range(h)]

    comps = components(solid, w, h)
    print("traced %d regions from %s (%dx%d)" % (len(comps), SRC, w, h))

    def name_for(centroid):
        best, bd = ("state", "State"), None
        for (cx, cy), slug, label in NAMES:
            d = (cx - centroid[0]) ** 2 + (cy - centroid[1]) ** 2
            if bd is None or d < bd:
                bd, best = d, (slug, label)
        return best

    rows = []
    for n, cells, centroid in comps:
        slug, label = name_for(centroid)
        d = path_d(loops(cells))
        rows.append((slug, label, d, n, centroid))
        print("  %-14s %7d px  centroid %-12s  %d path commands"
              % (label, n, str(centroid), d.count("L") + d.count("M")))

    with open(OUT, "w") as f:
        f.write("<!-- Generated by tools/make-region-svg.py. Do not edit by hand. -->\n")
        # Carries the same class, parallax hooks and aria treatment the <img>
        # it replaces had. Still decorative, so it stays hidden from assistive
        # tech: the hover glow is ambience, not information. No <title> either,
        # or the browser pops a tooltip every time the cursor crosses the hero.
        f.write('<svg class="region region-map" viewBox="0 0 %d %d"\n'
                '     xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false"\n'
                '     data-parallax="0.06" data-parallax-base="translateY(-50%%)">\n' % (w, h))
        for slug, label, d, _n, _c in rows:
            f.write('  <path class="rm-state" id="rm-%s" data-state="%s"\n'
                    '        d="%s"></path>\n' % (slug, label, d))
        f.write("</svg>\n")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
