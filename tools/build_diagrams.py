#!/usr/bin/env python3
"""Build the README diagrams (self-contained SVG) and their draw.io sources.

The same layout spec is emitted twice:

  * ``.svg``     - what the READMEs display. Every technology logo is inlined as
                   vector paths, so the file contains no external references at
                   all and renders identically on GitHub, GitHub Pages, in VS
                   Code, in print, and offline.
  * ``.drawio``  - the editable diagram (app.diagrams.net / draw.io Desktop).
                   Icons are referenced by URL so the file stays small.

Layout specs live in ``tools/diagram_specs.py``.

Usage
-----
    python tools/build_diagrams.py                 # everything
    python tools/build_diagrams.py --icons-only    # refresh assets/icons
    python tools/build_diagrams.py --only 03-de-etl-flow
    python tools/build_diagrams.py --refresh       # re-download icons

To rasterise a finished diagram to PNG, see assets/README.md.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons"
MANIFEST = ICON_DIR / "ICONS.json"

SIMPLE = "https://cdn.simpleicons.org/{slug}"
ICONIFY = "https://api.iconify.design/{set}/{name}.svg"

# ---------------------------------------------------------------------------
# Icon registry
#
#   "simple:<slug>"          Simple Icons CDN (brand colour already baked in)
#   "iconify:<set>/<name>"   Iconify (devicon / logos / thesvg sets)
#   "badge:<LABEL>:<#hex>"   hand-drawn tile, for tools that publish no logo
# ---------------------------------------------------------------------------
_ICON_TABLE = [
    # section 1 - data analytics / machine learning
    ("python", "simple:python"),
    ("jupyter", "simple:jupyter"),
    ("pandas", "simple:pandas"),
    ("numpy", "simple:numpy"),
    ("scipy", "simple:scipy"),
    ("plotly", "simple:plotly"),
    ("scikitlearn", "simple:scikitlearn"),
    ("tensorflow", "simple:tensorflow"),
    ("keras", "simple:keras"),
    ("matplotlib", "iconify:devicon/matplotlib"),
    ("seaborn", "iconify:devicon/seaborn"),
    ("sqlite", "simple:sqlite"),
    ("xgboost", "badge:XGB:#189F3B"),
    ("catboost", "badge:CB:#FFCC00"),
    ("openpyxl", "badge:XLSX:#217346"),
    ("tkinter", "badge:Tk:#2596BE"),
    ("requests", "badge:API:#0A7EA4"),
    ("csv", "badge:CSV:#4B6B7B"),
    ("parquet", "badge:PARQ:#0E7490"),
    ("notebook", "badge:IPYNB:#F37626"),

    # section 2 - Power BI
    ("powerbi", "iconify:devicon/powerbi"),
    ("excel", "iconify:simple-icons/microsoftexcel", "#217346"),
    ("dax", "badge:DAX:#F2C811"),
    ("dim", "badge:DIM:#118DFF"),
    ("chiclet", "badge:SLICER:#118DFF"),

    # section 3 - data engineering
    ("apacheairflow", "simple:apacheairflow"),
    ("postgresql", "simple:postgresql"),
    ("duckdb", "simple:duckdb"),
    ("dbt", "iconify:devicon/dbt"),
    ("streamlit", "simple:streamlit"),
    ("apachekafka", "simple:apachekafka"),
    ("apachespark", "simple:apachespark"),
    ("databricks", "simple:databricks"),
    ("pytest", "simple:pytest"),
    ("sqlfluff", "badge:LINT:#259D9E"),
    ("soda", "badge:SODA:#00A3A1"),
    ("deltalake", "badge:DELTA:#00ADD4"),
    ("unitycatalog", "badge:UNITY:#1B3139"),
    ("autoloader", "badge:AUTO:#FF3621"),
    ("dlq", "badge:DLQ:#C0392B"),
    ("docker", "simple:docker"),
    ("git", "simple:git"),
    ("githubactions", "simple:githubactions"),

    # section 4 - generative AI
    ("googlegemini", "simple:googlegemini"),
    ("huggingface", "simple:huggingface"),
    ("langchain", "simple:langchain"),
    ("llamaindex", "iconify:thesvg-color/llamaindex"),
    ("crewai", "simple:crewai"),
    ("django", "simple:django"),
    ("postman", "simple:postman"),
    ("gradio", "simple:gradio"),
    ("ollama", "simple:ollama", "#1F1F1F"),
    ("chromadb", "badge:CHROMA:#FF6B35"),
    ("tavily", "badge:TVLY:#3F51B5"),
    ("mcp", "iconify:simple-icons/modelcontextprotocol", "#000000"),
]

ICONS: dict[str, dict] = {}

for _row in _ICON_TABLE:
    _name, _src = _row[0], _row[1]
    _forced = _row[2] if len(_row) > 2 else None
    if _src.startswith("simple:"):
        _u = SIMPLE.format(slug=_src.split(":", 1)[1])
        ICONS[_name] = {"fetch": _u, "url": _u, "color": _forced, "badge": None}
    elif _src.startswith("iconify:"):
        _set, _ico = _src.split(":", 1)[1].split("/", 1)
        _u = ICONIFY.format(set=_set, name=_ico)
        ICONS[_name] = {"fetch": _u, "url": _u, "color": _forced, "badge": None}
    else:
        _, _label, _hex = _src.split(":")
        ICONS[_name] = {"fetch": None, "url": None,
                        "color": _hex, "badge": (_label, _hex)}

BADGE_FONT = "Segoe UI, Helvetica Neue, Helvetica, Arial, sans-serif"


# ---------------------------------------------------------------------------
# fetching + normalising icons
# ---------------------------------------------------------------------------
def _download(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "diagram-builder/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _badge_svg(label: str, colour: str) -> str:
    """A square tile with a short label - stands in for a missing logo."""
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    ink = "#ffffff" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.62 else "#15262e"
    size = 46 if len(label) <= 2 else (36 if len(label) == 3 else 27)
    if len(label) > 4:
        size = 22
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<rect width="100" height="100" rx="20" fill="{colour}"/>'
        f'<text x="50" y="{50 + size * 0.36:.1f}" text-anchor="middle" '
        f'font-family="{BADGE_FONT}" font-size="{size}" font-weight="700" '
        f'letter-spacing="0.5" fill="{ink}">{label}</text></svg>'
    )


def normalise(raw: str, name: str, colour: str | None) -> tuple[str, str]:
    """Strip the outer <svg>, namespace the ids; return (inner markup, viewBox)."""
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw, flags=re.S)
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S).strip()
    open_tag = re.search(r"<svg\b[^>]*>", raw, flags=re.S)
    if not open_tag:
        raise ValueError("no <svg> element")
    head = open_tag.group(0)
    inner = raw[open_tag.end():raw.rindex("</svg>")].strip()

    vb = re.search(r'viewBox="([^"]+)"', head)
    if vb:
        view_box = vb.group(1)
    else:
        w = re.search(r'width="([\d.]+)', head)
        h = re.search(r'height="([\d.]+)', head)
        if not (w and h):
            raise ValueError("no viewBox and no width/height")
        view_box = f"0 0 {w.group(1)} {h.group(1)}"

    if colour:
        inner = re.sub(r'fill="(currentColor|none)"', f'fill="{colour}"', inner)
        inner = inner.replace("currentColor", colour)
        # brand logos drawn in white would vanish on a white page
        for light in ('fill="#fff"', 'fill="#FFFFFF"', 'fill="#ffffff"'):
            inner = inner.replace(light, f'fill="{colour}"')

    # Simple Icons carry the brand colour on the root <svg fill="...">, which is
    # dropped together with the wrapper - re-apply it as an inherited fill.
    # An explicitly requested colour wins over the brand colour.
    root_fill = re.search(r'\bfill="(#[0-9A-Fa-f]{3,6})"', head)
    wrap = colour or (root_fill.group(1) if root_fill else None)
    if wrap:
        inner = f'<g fill="{wrap}">{inner}</g>'

    for ident in set(re.findall(r'id="([^"]+)"', inner)):
        prefixed = f"{name}-{ident}"
        inner = inner.replace(f'id="{ident}"', f'id="{prefixed}"')
        inner = inner.replace(f"url(#{ident})", f"url(#{prefixed})")

    inner = re.sub(r"\s+", " ", inner).strip()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
           'xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'viewBox="{view_box}">{inner}</svg>')
    ET.fromstring(svg)  # fail fast on malformed markup
    return inner, view_box


def ensure_icons(refresh: bool = False, quiet: bool = False) -> dict:
    """Download every registered icon into assets/icons (cached on disk)."""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}                       # rebuilt from the registry every run,
    cached = downloaded = drawn = 0     # so removed icons disappear from it
    for name, meta in ICONS.items():
        target = ICON_DIR / f"{name}.svg"
        badge = meta["fetch"] is None                    # registry says: drawn badge
        if target.exists() and not refresh:
            text = target.read_text(encoding="utf-8")
            badge = badge or ("<text" in text and "<path" not in text)
            cached += 1
        else:
            inner = view_box = None
            if meta["fetch"]:
                try:
                    inner, view_box = normalise(_download(meta["fetch"]), name,
                                                meta["color"])
                    downloaded += 1
                except Exception as exc:                  # noqa: BLE001
                    print(f"  ! {name}: {meta['fetch']} -> {exc}", file=sys.stderr)
            if inner is None:
                label, colour = meta["badge"] or (name.upper()[:4], "#4B6B7B")
                inner, view_box = normalise(_badge_svg(label, colour), name, None)
                badge = True
                drawn += 1
                if not quiet:
                    print(f"  - {name}: drew a '{label}' badge")
            text = ('<svg xmlns="http://www.w3.org/2000/svg" '
                    'xmlns:xlink="http://www.w3.org/1999/xlink" '
                    f'viewBox="{view_box}">{inner}</svg>\n')
            target.write_text(text, encoding="utf-8", newline="\n")

        meta["file"] = str(target.relative_to(ROOT)).replace("\\", "/")
        if badge:                       # draw.io gets an inline copy
            data = base64.b64encode(text.encode("utf-8")).decode("ascii")
            meta["diagrams_url"] = f"data:image/svg+xml;base64,{data}"
            meta["badge_used"] = True
        else:                           # ... or the fetchable logo URL
            meta["diagrams_url"] = meta["fetch"]
        manifest[name] = {k: meta[k] for k in ("url", "file", "diagrams_url")}
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    if not quiet:
        print(f"icons: {cached} cached, {downloaded} downloaded, {drawn} drawn")
    return ICONS




# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------
ICON_TILE = 36
TITLE_SIZE = 13
SUB_SIZE = 10.5
TITLE_LH = 16
SUB_LH = 13

PANEL = "#ffffff"
NODE_STROKE = "#d5e0e9"
TITLE_INK = "#16323f"
SUB_INK = "#5f7889"
FONT = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
EDGE_INK = "#7b8fa0"
BAND_FILL = "#f6f9fc"
BAND_STROKE = "#c9d8e4"
TILE_FILL = "#f4f7fa"
TILE_STROKE = "#e2eaf1"


def fmt(value) -> str:
    text = f"{float(value):.1f}"
    return text[:-2] if text.endswith(".0") else text


def esc(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def wrap(text: str, width: float, char_w: float) -> list[str]:
    limit = max(6, int(width // char_w))
    out: list[str] = []
    for chunk in str(text).split("\n"):
        out.extend(textwrap.wrap(chunk, limit) or [""])
    return out


def node_text(node, node_w):
    titles = wrap(node["title"], node_w - 20, 7.3)
    subs = wrap(node.get("sub", ""), node_w - 24, 5.7) if node.get("sub") else []
    return titles, subs


def node_height(node, node_w) -> float:
    titles, subs = node_text(node, node_w)
    return 104 + TITLE_LH * (len(titles) - 1) + SUB_LH * max(0, len(subs) - 1)


def layout(spec) -> dict:
    width = spec.get("width", 1360)
    margin = spec.get("margin", 28)
    gap = spec.get("gap", 54)
    y = spec.get("top", 26)
    rows = []
    bottom = 0

    for source_row in spec["rows"]:
        nodes = source_row["nodes"]
        count = len(nodes)
        if source_row.get("fixed"):
            placed = []
            for item in nodes:
                width_item = item.get("w", 190)
                placed.append({**item, "w": width_item,
                               "h": max(item.get("h", 0), node_height(item, width_item))})
            rows.append({"index": len(rows), "nodes": placed, "edges": [], "y": 0,
                         "h": max(p["y"] + p["h"] for p in placed)})
            continue
        node_w = source_row.get("node_w")
        if node_w is None:
            available = width - 2 * margin - (count - 1) * gap
            node_w = min(spec.get("node_w", 196), available / max(count, 1))
        heights = [node_height(node, node_w) for node in nodes]
        row_h = max(heights) if heights else 0
        heights = [row_h] * len(nodes)          # one uniform height per row
        total = count * node_w + (count - 1) * gap
        x0 = (width - total) / 2

        band = source_row.get("band")
        band_top = source_row.get("band_top", 30) if band else 0
        band_pad = source_row.get("band_pad", 16)
        if band:
            y += band_top

        placed = []
        for index, node in enumerate(nodes):
            placed.append({
                **node,
                "x": x0 + index * (node_w + gap),
                "y": y,
                "w": node_w,
                "h": heights[index],
            })
        row = {"index": len(rows), "nodes": placed,
               "edges": source_row.get("edges", []), "y": y, "h": row_h}
        if band:
            row["band"] = {"x": x0 - band_pad, "y": y - band_top,
                           "w": total + 2 * band_pad, "h": row_h + band_top + band_pad,
                           "label": band}
        rows.append(row)
        bottom = max(bottom, y + row_h + (band_pad if band else 0))
        y = bottom + source_row.get("space", 56)

    links = []
    for link in spec.get("links", []):
        (r1, i1), (r2, i2) = link["from"], link["to"]
        links.append({"a": rows[r1]["nodes"][i1], "b": rows[r2]["nodes"][i2],
                      "label": link.get("label", ""), "dashed": link.get("dashed", False),
                      "target_x": link.get("target_x", 0.5)})

    # feedback edges are routed below their row - keep room for them
    for row in rows:
        by_id = {node["id"]: node for node in row["nodes"]}
        for edge in row["edges"]:
            if isinstance(edge, dict):
                a_id, b_id = edge["from"], edge["to"]
            else:
                a_id, b_id = edge[0], edge[1]
            if by_id[a_id]["x"] > by_id[b_id]["x"]:
                bottom = max(bottom, by_id[a_id]["y"] + by_id[a_id]["h"] + 42)

    connectors = []
    for connector in spec.get("connectors", []):
        (r1, i1), (r2, i2) = connector["from"], connector["to"]
        connectors.append({"a": rows[r1]["nodes"][i1], "b": rows[r2]["nodes"][i2],
                           "label": connector.get("label", "")})

    return {"rows": rows, "links": links, "connectors": connectors,
            "width": width, "height": spec.get("height") or bottom + 10,
            "name": spec.get("name", spec["slug"])}


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------
ICON_CACHE: dict[str, tuple[str, str]] = {}


def load_icon_cache() -> None:
    for name, meta in ICONS.items():
        text = (ROOT / meta["file"]).read_text(encoding="utf-8")
        head = re.search(r"<svg\b[^>]*>", text, flags=re.S)
        view_box = re.search(r'viewBox="([^"]+)"', head.group(0)).group(1)
        ICON_CACHE[name] = (text[head.end():text.rindex("</svg>")].strip(), view_box)


def _icon_svg(name: str, x: float, y: float, size: float, key: str) -> str:
    inner, view_box = ICON_CACHE[name]
    vx, vy, vw, vh = (float(v) for v in view_box.replace(",", " ").split())
    scale = size / max(vw, vh)
    dx = x + (size - vw * scale) / 2
    dy = y + (size - vh * scale) / 2
    inner = inner.replace(' id="', f' id="{key}-')
    inner = re.sub(r"url\(#", f"url(#{key}-", inner)
    return (f'<g transform="translate({fmt(dx)},{fmt(dy)}) scale({scale:.4f})">'
            f"{inner}</g>")


def _svg_node(node, slug: str) -> str:
    x, y, w, h = node["x"], node["y"], node["w"], node["h"]
    accent = node.get("accent", "#4b6b7b")
    icons = node.get("icons") or []
    out = [
        f'<rect x="{fmt(x + 2)}" y="{fmt(y + 3)}" width="{fmt(w)}" height="{fmt(h)}" '
        f'rx="10" fill="#dde6ee" opacity="0.6"/>',
        f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="10" '
        f'fill="{PANEL}" stroke="{NODE_STROKE}" stroke-width="1.2"/>',
        f'<rect x="{fmt(x)}" y="{fmt(y)}" width="7" height="{fmt(h)}" rx="7" fill="{accent}"/>',
        f'<rect x="{fmt(x + 3.5)}" y="{fmt(y + 0.6)}" width="3.5" height="{fmt(h - 1.2)}" '
        f'fill="{accent}"/>',
    ]
    if icons:
        span = len(icons) * ICON_TILE + (len(icons) - 1) * 8
        ix = x + (w - span) / 2
        for index, icon_name in enumerate(icons):
            tx = ix + index * (ICON_TILE + 8)
            out.append(f'<rect x="{fmt(tx)}" y="{fmt(y + 16)}" width="{ICON_TILE}" '
                       f'height="{ICON_TILE}" rx="8" fill="{TILE_FILL}" '
                       f'stroke="{TILE_STROKE}" stroke-width="1"/>')
            out.append(_icon_svg(icon_name, tx + 6, y + 22, 24,
                                 f"{slug}-{node['id']}-{index}"))
    titles, subs = node_text(node, w)
    cx = x + w / 2
    ty = y + 72
    for index, line in enumerate(titles):
        out.append(f'<text x="{fmt(cx)}" y="{fmt(ty + index * TITLE_LH)}" '
                   f'text-anchor="middle" font-family="{FONT}" font-size="{TITLE_SIZE}" '
                   f'font-weight="600" fill="{TITLE_INK}">{esc(line)}</text>')
    sy = ty + TITLE_LH * (len(titles) - 1) + 18
    for index, line in enumerate(subs):
        out.append(f'<text x="{fmt(cx)}" y="{fmt(sy + index * SUB_LH)}" '
                   f'text-anchor="middle" font-family="{FONT}" font-size="{SUB_SIZE}" '
                   f'fill="{SUB_INK}">{esc(line)}</text>')
    return "".join(out)


def _svg_label(x: float, y: float, text: str, size: float = 9) -> str:
    width = len(text) * size * 0.6 + 11
    return (f'<rect x="{fmt(x - width / 2)}" y="{fmt(y - 10.5)}" width="{fmt(width)}" '
            f'height="14.5" rx="3" fill="#ffffff"/>'
            f'<text x="{fmt(x)}" y="{fmt(y)}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="{size}" font-weight="700" letter-spacing="0.5" '
            f'fill="#5c7183">{esc(text)}</text>')


def _svg_edge(a, b, label: str, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="6 4"' if dashed else ""
    if b["x"] < a["x"]:
        # feedback edge - routed underneath the row so it never crosses a box
        ax = a["x"] + a["w"] / 2
        bx = b["x"] + b["w"] / 2
        y1 = a["y"] + a["h"] + 2
        y2 = b["y"] + b["h"] + 3
        bend = max(y1, y2) + 18
        path = (f"M{fmt(ax)},{fmt(y1)} L{fmt(ax)},{fmt(bend)} "
                f"L{fmt(bx)},{fmt(bend)} L{fmt(bx)},{fmt(y2)}")
        out = [f'<path d="{path}" fill="none" stroke="{EDGE_INK}" stroke-width="2" '
               f'stroke-linejoin="round" marker-end="url(#arrow)" stroke-dasharray="6 4"/>']
        if label:
            out.append(_svg_label((ax + bx) / 2, bend - 7, label))
        return "".join(out)

    y1 = a["y"] + a["h"] / 2
    x1, x2 = a["x"] + a["w"] + 2, b["x"] - 3
    out = [f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y1)}" '
           f'stroke="{EDGE_INK}" stroke-width="2" stroke-linecap="round" '
           f'marker-end="url(#arrow)"{dash}/>']
    if label:
        available = max(26.0, x2 - x1)
        size = 9.0
        if len(label) * size * 0.6 + 11 > available:
            size = max(7.0, (available - 11) / (len(label) * 0.6))
        out.append(_svg_label((x1 + x2) / 2, y1 - 9, label, size))
    return "".join(out)


def _svg_link(link) -> str:
    a, b = link["a"], link["b"]
    ax = a["x"] + a["w"] / 2
    bx = b["x"] + b["w"] * link.get("target_x", 0.5)
    if b["y"] < a["y"]:                                    # arrow points upward
        ay, by = a["y"] - 2, b["y"] + b["h"] + 3
    else:
        ay, by = a["y"] + a["h"] + 2, b["y"] - 3
    dash = ' stroke-dasharray="6 4"' if link["dashed"] else ""
    if abs(ax - bx) < 6:
        path = f"M{fmt(ax)},{fmt(ay)} L{fmt(ax)},{fmt(by)}"
        lx, ly = ax + 9, (ay + by) / 2
    else:
        mid = (ay + by) / 2
        path = (f"M{fmt(ax)},{fmt(ay)} L{fmt(ax)},{fmt(mid)} "
                f"L{fmt(bx)},{fmt(mid)} L{fmt(bx)},{fmt(by)}")
        lx, ly = bx + 9, mid - 7
    out = [f'<path d="{path}" fill="none" stroke="{EDGE_INK}" stroke-width="2" '
           f'stroke-linejoin="round" stroke-linecap="round" '
           f'marker-end="url(#arrow)"{dash}/>']
    if link["label"]:
        width_label = len(link["label"]) * 5.4 + 10
        out.append(f'<rect x="{fmt(lx - 4)}" y="{fmt(ly - 10)}" width="{fmt(width_label)}" '
                   f'height="14" rx="3" fill="#ffffff"/>')
        out.append(f'<text x="{fmt(lx)}" y="{fmt(ly)}" font-family="{FONT}" '
                   f'font-size="9.5" font-weight="700" letter-spacing="0.6" '
                   f'fill="#5c7183">{esc(link["label"])}</text>')
    return "".join(out)


def _svg_connector(connector) -> str:
    """Straight relationship line between two boxes (star-schema view)."""
    a, b = connector["a"], connector["b"]
    ax, ay = a["x"] + a["w"] / 2, a["y"] + a["h"] / 2
    bx, by = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    dx, dy = bx - ax, by - ay

    def edge(node, vx, vy, inward):
        cx, cy = node["x"] + node["w"] / 2, node["y"] + node["h"] / 2
        tx = (node["w"] / 2) / abs(vx) if vx else float("inf")
        ty = (node["h"] / 2) / abs(vy) if vy else float("inf")
        t = min(tx, ty)
        return cx + vx * t * (1 if inward else 0.94), cy + vy * t * (1 if inward else 0.94)

    x1, y1 = edge(a, dx, dy, False)
    x2, y2 = edge(b, -dx, -dy, True)
    return (f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" '
            f'stroke="#a9bccb" stroke-width="1.6" marker-end="url(#arrow-soft)"/>')


def _svg_band(band) -> str:
    x, y, w, h = band["x"], band["y"], band["w"], band["h"]
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="12" '
            f'fill="{BAND_FILL}" stroke="{BAND_STROKE}" stroke-width="1.2" '
            f'stroke-dasharray="7 5"/>'
            f'<text x="{fmt(x + 14)}" y="{fmt(y + 19)}" font-family="{FONT}" font-size="9.5" '
            f'font-weight="700" letter-spacing="1.3" fill="#8aa0b3">'
            f'{esc(band["label"])}</text>')


def render_svg(spec, lay) -> str:
    width, height = lay["width"], lay["height"]
    slug = spec["slug"]
    body = [f'<rect width="{fmt(width)}" height="{fmt(height)}" fill="#ffffff"/>']
    caption = spec.get("caption")
    if caption:
        body.append(f'<text x="{fmt(spec.get("margin", 28))}" y="22" font-family="{FONT}" '
                    f'font-size="10.5" font-weight="700" letter-spacing="1.4" '
                    f'fill="#93a6b6">{esc(caption.upper())}</text>')
    for row in lay["rows"]:
        if row.get("band"):
            body.append(_svg_band(row["band"]))
    for row in lay["rows"]:
        for node in row["nodes"]:
            body.append(_svg_node(node, slug))
    for row in lay["rows"]:
        by_id = {node["id"]: node for node in row["nodes"]}
        for edge in row["edges"]:
            if isinstance(edge, dict):
                a_id, b_id, label = edge["from"], edge["to"], edge.get("label", "")
            else:
                a_id, b_id, label = (list(edge) + ["", ""])[:3]
            body.append(_svg_edge(by_id[a_id], by_id[b_id], label,
                                  dashed=by_id[a_id]["x"] > by_id[b_id]["x"]))
    for link in lay["links"]:
        body.append(_svg_link(link))
    for connector in lay["connectors"]:
        body.append(_svg_connector(connector))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{fmt(width)}" height="{fmt(height)}" '
        f'viewBox="0 0 {fmt(width)} {fmt(height)}" role="img" '
        f'aria-label="{esc(lay["name"])}">'
        f"<title>{esc(lay['name'])}</title>"
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{EDGE_INK}"/></marker>'
        '<marker id="arrow-soft" viewBox="0 0 10 10" refX="8.5" refY="5" '
        'markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#a9bccb"/></marker></defs>'
        + "".join(body) + "</svg>\n"
    )


# ---------------------------------------------------------------------------
# draw.io rendering (same layout, editable in app.diagrams.net / draw.io)
# ---------------------------------------------------------------------------
def _xml(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _dio_cell(cid, value, style, x, y, w, h, parent="1", kind="vertex") -> str:
    geometry = (f'<mxGeometry x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" '
                f'height="{fmt(h)}" as="geometry"/>')
    return (f'<mxCell id="{cid}" value="{_xml(value)}" style="{style}" '
            f'{kind}="1" parent="{parent}">{geometry}</mxCell>')


def render_drawio(spec, lay) -> str:
    slug = spec["slug"]
    cells: list[str] = []
    for row in lay["rows"]:
        band = row.get("band")
        if band:
            cells.append(_dio_cell(
                f"band-{row['index']}", band["label"],
                'rounded=1;arcSize=6;whiteSpace=wrap;html=1;dashed=1;dashPattern=7 5;'
                'fillColor=#F6F9FC;strokeColor=#C9D8E4;align=left;verticalAlign=top;'
                'spacingLeft=14;spacingTop=6;fontSize=9;fontColor=#8AA0B3;fontStyle=1;',
                band["x"], band["y"], band["w"], band["h"]))
    for row in lay["rows"]:
        for node in row["nodes"]:
            node_id = f"n-{row['index']}-{node['id']}"
            titles, subs = node_text(node, node["w"])
            label = "<b>" + "<br>".join(_xml(t) for t in titles) + "</b>"
            if subs:
                label += ('<br><font style="font-size:10px" color="#5f7889">'
                          + "<br>".join(_xml(s) for s in subs) + "</font>")
            accent = node.get("accent", "#4b6b7b")
            cells.append(_dio_cell(
                node_id, label,
                'rounded=1;arcSize=7;whiteSpace=wrap;html=1;fillColor=#FFFFFF;'
                f'strokeColor={accent};strokeWidth=1.5;fontSize=13;fontStyle=1;'
                'fontColor=#16323F;align=center;verticalAlign=bottom;spacingBottom=14;'
                'shadow=1;',
                node["x"], node["y"], node["w"], node["h"]))
            icons = node.get("icons") or []
            span = len(icons) * ICON_TILE + (len(icons) - 1) * 8
            ix = node["x"] + (node["w"] - span) / 2
            for index, icon_name in enumerate(icons):
                url = ICONS[icon_name]["diagrams_url"]
                cells.append(_dio_cell(
                    f"i-{row['index']}-{node['id']}-{index}", "",
                    f'shape=image;imageAspect=1;aspect=fixed;image={_xml(url)};'
                    'strokeColor=none;fillColor=none;',
                    ix + index * (ICON_TILE + 8) - node["x"], 16,
                    ICON_TILE, ICON_TILE, parent=node_id))
    edge_style = ('edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#7B8FA0;'
                  'strokeWidth=2;endArrow=block;endFill=1;endSize=8;fontSize=9;'
                  'fontColor=#5C7183;fontStyle=1;labelBackgroundColor=#FFFFFF;')
    counter = 0
    for row in lay["rows"]:
        by_id = {node["id"]: node for node in row["nodes"]}
        for edge in row["edges"]:
            if isinstance(edge, dict):
                a_id, b_id, label = edge["from"], edge["to"], edge.get("label", "")
            else:
                a_id, b_id, label = (list(edge) + ["", ""])[:3]
            counter += 1
            dash = "dashed=1;" if by_id[a_id]["x"] > by_id[b_id]["x"] else ""
            cells.append(
                f'<mxCell id="e-{counter}" value="{_xml(label)}" '
                f'style="{edge_style}{dash}" edge="1" parent="1" '
                f'source="n-{row["index"]}-{a_id}" target="n-{row["index"]}-{b_id}">'
                '<mxGeometry relative="1" as="geometry"/></mxCell>')
    for link in lay["links"]:
        counter += 1
        a_row = next(r["index"] for r in lay["rows"] if link["a"] in r["nodes"])
        b_row = next(r["index"] for r in lay["rows"] if link["b"] in r["nodes"])
        dash = "dashed=1;" if link["dashed"] else ""
        cells.append(
            f'<mxCell id="l-{counter}" value="{_xml(link["label"])}" '
            f'style="{edge_style}{dash}" edge="1" parent="1" '
            f'source="n-{a_row}-{link["a"]["id"]}" target="n-{b_row}-{link["b"]["id"]}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>')
    for connector in lay["connectors"]:
        counter += 1
        a_row = next(r["index"] for r in lay["rows"] if connector["a"] in r["nodes"])
        b_row = next(r["index"] for r in lay["rows"] if connector["b"] in r["nodes"])
        cells.append(
            f'<mxCell id="c-{counter}" value="{_xml(connector["label"])}" '
            'style="edgeStyle=none;html=1;strokeColor=#A9BCCB;strokeWidth=1.6;'
            'endArrow=block;endFill=1;endSize=5;fontSize=9;fontColor=#5C7183;" '
            'edge="1" parent="1" '
            f'source="n-{a_row}-{connector["a"]["id"]}" '
            f'target="n-{b_row}-{connector["b"]["id"]}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>')

    return (
        '<mxfile host="app.diagrams.net" type="device">'
        f'<diagram id="{slug}" name="{_xml(lay["name"])}">'
        f'<mxGraphModel dx="{fmt(lay["width"])}" dy="{fmt(lay["height"])}" grid="1" '
        'gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
        f'page="1" pageScale="1" pageWidth="{fmt(lay["width"])}" '
        f'pageHeight="{fmt(lay["height"])}" background="#FFFFFF" math="0" shadow="0">'
        '<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
        + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>\n"
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--icons-only", action="store_true",
                        help="only refresh assets/icons")
    parser.add_argument("--only", nargs="*", metavar="SLUG",
                        help="build just these diagram slugs")
    parser.add_argument("--refresh", action="store_true",
                        help="re-download every icon")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from diagram_specs import SPECS                        # noqa: PLC0415

    ensure_icons(refresh=args.refresh)
    if args.icons_only:
        return 0
    load_icon_cache()

    wanted = set(args.only or [])
    built = 0
    for spec in SPECS:
        if wanted and spec["slug"] not in wanted:
            continue
        lay = layout(spec)
        target = ROOT / spec["out"]
        target.parent.mkdir(parents=True, exist_ok=True)
        svg = render_svg(spec, lay)
        (target.parent / f"{target.name}.svg").write_text(svg, encoding="utf-8",
                                                          newline="\n")
        (target.parent / f"{target.name}.drawio").write_text(
            render_drawio(spec, lay), encoding="utf-8", newline="\n")
        ET.fromstring(svg)
        print(f"  {target.name}.svg  {len(svg) // 1024} KB  "
              f"({fmt(lay['width'])}x{fmt(lay['height'])})")
        built += 1
    print(f"diagrams: {built} built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
