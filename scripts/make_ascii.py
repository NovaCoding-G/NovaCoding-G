#!/usr/bin/env python3
"""Generate NovaCoding's self-contained profile artwork.

The source mark and font live in this repository. Output SVGs contain no
remote requests and use only animation primitives supported by GitHub.
"""
from __future__ import annotations

import base64
import html
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "source" / "novacoding-logo.png"
FONT = ASSETS / "fonts" / "JetBrainsMono-Regular.woff2"
RAMP = " .:+*#@"
FAMILY = "NovaMono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def font_css(text: str) -> str:
    """Embed a local WOFF2, subset when fontTools is available."""
    payload = FONT.read_bytes()
    try:
        from fontTools import subset

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "subset.woff2"
            options = subset.Options()
            options.flavor = "woff2"
            options.layout_features = ["*"]
            font = subset.load_font(str(FONT), options)
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(text="".join(sorted(set(text))))
            subsetter.subset(font)
            subset.save_font(font, str(output_path), options)
            payload = output_path.read_bytes()
    except (ImportError, OSError):
        pass
    encoded = base64.b64encode(payload).decode("ascii")
    return (
        "@font-face{font-family:NovaMono;font-style:normal;font-weight:100 800;"
        f"font-display:block;src:url(data:font/woff2;base64,{encoded}) format('woff2')}}"
    )


def ascii_mark(cols: int = 48) -> list[str]:
    img = Image.open(SOURCE).convert("L")
    # Keep the celestial crescent and left star, but remove the raster wordmark:
    # it is rebuilt as crisp SVG text in the hero so the identity stays legible.
    width, height = img.size
    pixels = img.load()
    for y in range(int(height * 0.31), int(height * 0.67)):
        for x in range(int(width * 0.39), width):
            pixels[x, y] = 0
    bbox = img.point(lambda value: 255 if value > 18 else 0).getbbox()
    if not bbox:
        raise ValueError("NovaCoding source mark has no visible pixels")
    img = ImageOps.expand(img.crop(bbox), border=12, fill=0)
    img = ImageEnhance.Contrast(ImageOps.autocontrast(img)).enhance(2.7)
    width, height = img.size
    rows = max(1, int(cols * (height / width) * 0.46))
    img = img.resize((cols, rows), Image.Resampling.LANCZOS)
    img = img.point(
        lambda value: 0
        if value < 24
        else (55 if value < 90 else (145 if value < 180 else 255))
    )
    pixels = list(
        img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
    )
    count = len(RAMP)
    lines = [
        "".join(
            RAMP[min(count - 1, int(pixels[row * cols + col] / 255 * count))]
            for col in range(cols)
        ).rstrip()
        for row in range(rows)
    ]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def shared_style(text: str) -> str:
    return (
        font_css(text)
        + ".ink{fill:#24292f}.muted{fill:#57606a}.faint{fill:#8c959f}"
        ".line{stroke:#d0d7de}.accent{fill:#9a6700}.accent-line{stroke:#9a6700}"
        ".panel{fill:#f6f8fa;stroke:#d0d7de}"
        "@media(prefers-color-scheme:dark){"
        ".ink{fill:#f0f6fc}.muted{fill:#b1bac4}.faint{fill:#6e7681}"
        ".line{stroke:#30363d}.accent{fill:#e3b341}.accent-line{stroke:#e3b341}"
        ".panel{fill:#161b22;stroke:#30363d}}"
        "@media(prefers-reduced-motion:reduce){.motion{display:none}}"
    )


def build_hero(lines: list[str]) -> str:
    labels = (
        "NOVACODING INDEPENDENT STUDIO APULIA ITALY SOFTWARE FOR RESEARCH "
        "AND THE PUBLIC WEB AI SECURITY PLANETARY DATA COMPUTATIONAL BIOLOGY "
        "ASCII MARK RECONSTRUCTION nova CODING "
        + "".join(lines)
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="620" height="360" '
        'viewBox="0 0 620 360" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">NovaCoding independent software studio</title>",
        "<desc id=\"desc\">Animated ASCII mark with orbital research signals</desc>",
        f"<style>{shared_style(labels)}</style>",
        '<rect x=".5" y=".5" width="619" height="359" rx="12" class="panel"/>',
        '<path d="M24 55H596M24 305H596" class="line" opacity=".72"/>',
        '<circle cx="35" cy="28" r="3" class="accent"/>',
        '<text x="48" y="32" class="ink" font-family="NovaMono" font-size="11" '
        'letter-spacing="1.8">NOVACODING / INDEPENDENT STUDIO</text>',
        '<text x="596" y="32" text-anchor="end" class="faint" '
        'font-family="NovaMono" font-size="9">APULIA · ITALY</text>',
        '<text x="24" y="70" class="faint" font-family="NovaMono" font-size="7" '
        'letter-spacing="1.1">ASCII MARK / RECONSTRUCTION</text>',
        '<circle cx="211" cy="68" r="2.5" class="accent motion">'
        '<animate attributeName="opacity" values=".2;1;.2" dur="1.4s" '
        'repeatCount="indefinite"/></circle>',
    ]
    x, y, line_height = 25, 84, 8.4
    for index, line in enumerate(lines):
        safe = html.escape(line)
        parts.append(
            f'<text x="{x}" y="{y + index * line_height:.1f}" '
            'class="muted" font-family="NovaMono" font-size="7.2" '
            f'xml:space="preserve">{safe}'
            f'<animate attributeName="opacity" values="0;1" '
            f'begin="{.35 + index * .12:.2f}s" dur=".45s" fill="freeze"/></text>'
        )
    # The wordmark resolves after the crescent has started drawing. This makes
    # the ASCII animation read unmistakably as the NovaCoding logo.
    parts.extend(
        [
            '<clipPath id="wordmark-reveal"><rect x="137" y="119" width="0" height="55">'
            '<animate attributeName="width" from="0" to="145" begin="2.45s" '
            'dur="1.8s" fill="freeze"/></rect></clipPath>',
            '<text x="146" y="163" clip-path="url(#wordmark-reveal)" class="ink" '
            'font-family="Georgia,Times New Roman,serif" font-size="39" '
            'font-weight="700">nova</text>',
            '<path d="M135 143l3 1.5 1.5 3 1.5-3 3-1.5-3-1.5-1.5-3-1.5 3z" '
            'class="ink" opacity="0"><animate attributeName="opacity" from="0" '
            'to="1" begin="2.25s" dur=".5s" fill="freeze"/></path>',
            '<path d="M278 143l3 1.5 1.5 3 1.5-3 3-1.5-3-1.5-1.5-3-1.5 3z" '
            'class="accent" opacity="0"><animate attributeName="opacity" from="0" '
            'to="1" begin="4.1s" dur=".5s" fill="freeze"/></path>',
        ]
    )
    for index, letter in enumerate("CODING"):
        parts.append(
            f'<text x="{149 + index * 20}" y="187" class="ink" '
            'font-family="NovaMono" font-size="11" letter-spacing="1" opacity="0">'
            f"{letter}<animate attributeName=\"opacity\" from=\"0\" to=\"1\" "
            f'begin="{3.25 + index * .24:.2f}s" dur=".38s" fill="freeze"/></text>'
        )
    # Orbital system: three domains around one studio.
    parts.extend(
        [
            '<g transform="translate(486 181)" opacity="0">',
            '<animate attributeName="opacity" from="0" to="1" begin="4.65s" '
            'dur=".8s" fill="freeze"/>',
            '<ellipse rx="88" ry="59" fill="none" class="line" stroke-dasharray="2 7"/>',
            '<ellipse rx="62" ry="91" fill="none" class="line" '
            'stroke-dasharray="1 8" transform="rotate(31)"/>',
            '<circle r="28" fill="none" class="accent-line" stroke-width="1.2"/>',
            '<circle r="20" class="panel"/>',
            '<text y="-2" text-anchor="middle" class="accent" font-family="NovaMono" '
            'font-size="9" font-weight="700">NOVA</text>',
            '<text y="10" text-anchor="middle" class="faint" font-family="NovaMono" '
            'font-size="6">STUDIO/01</text>',
            '<circle r="3.5" class="accent motion"><animateMotion dur="10s" '
            'repeatCount="indefinite" path="M88 0A88 59 0 1 1 -88 0A88 59 0 1 1 88 0"/></circle>',
            '<circle r="2.5" class="muted motion"><animateMotion dur="11s" '
            'repeatCount="indefinite" path="M53 31A62 91 31 1 1 -53 -31A62 91 31 1 1 53 31"/></circle>',
            '<g transform="translate(-92 -45)"><circle r="4" class="accent"/>'
            '<text x="-8" y="-10" text-anchor="end" class="ink" font-family="NovaMono" '
            'font-size="8">AI SECURITY</text></g>',
            '<g transform="translate(72 -65)"><circle r="4" class="accent"/>'
            '<text x="-8" y="-10" text-anchor="end" class="ink" font-family="NovaMono" '
            'font-size="8">PLANETARY DATA</text></g>',
            '<g transform="translate(69 72)"><circle r="4" class="accent"/>'
            '<text x="-8" y="16" text-anchor="end" class="ink" font-family="NovaMono" '
            'font-size="8">COMPUTATIONAL BIOLOGY</text></g>',
            "</g>",
            '<text x="24" y="330" class="accent" font-family="NovaMono" font-size="10">&gt;_</text>',
            '<text x="52" y="330" class="ink" font-family="NovaMono" font-size="10">'
            "SOFTWARE FOR RESEARCH AND THE PUBLIC WEB</text>",
            '<rect x="334" y="319" width="7" height="14" class="accent motion">'
            '<animate attributeName="opacity" values="1;.15;1" dur="1.1s" '
            'repeatCount="indefinite"/></rect>',
            "</svg>",
        ]
    )
    return "".join(parts)


def build_projects() -> str:
    projects = [
        ("01", "NOVACHECK", "AI SECURITY", "GHOST PACKAGES · SARIF · LOCAL-FIRST"),
        ("02", "B.E.A.C.O.N", "PLANETARY DATA", "JPL CAD · JPL SENTRY · ESA NEOCC"),
        ("03", "IMMUNOMIND", "COMPUTATIONAL BIOLOGY", "IMMUNITY · SIMULATION · EDUCATION"),
    ]
    all_text = " ".join(" ".join(item) for item in projects)
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="620" height="238" '
        'viewBox="0 0 620 238" role="img" aria-label="Selected NovaCoding projects">',
        f"<style>{shared_style(all_text)}</style>",
    ]
    for index, (number, name, domain, detail) in enumerate(projects):
        y = index * 76 + 1
        p.extend(
            [
                f'<rect x=".5" y="{y}" width="619" height="67" rx="8" class="panel"/>',
                f'<text x="20" y="{y + 27}" class="accent" font-family="NovaMono" '
                f'font-size="12">{number}</text>',
                f'<path d="M54 {y + 13}V{y + 54}" class="line"/>',
                f'<text x="72" y="{y + 27}" class="ink" font-family="NovaMono" '
                f'font-size="15" font-weight="700">{name}</text>',
                f'<text x="72" y="{y + 47}" class="muted" font-family="NovaMono" '
                f'font-size="9">{detail}</text>',
                f'<text x="598" y="{y + 27}" text-anchor="end" class="faint" '
                f'font-family="NovaMono" font-size="8">{domain}</text>',
                f'<circle cx="588" cy="{y + 48}" r="3" class="accent">'
                f'<animate attributeName="opacity" values=".25;1;.25" '
                f'begin="{index * .4}s" dur="2.4s" repeatCount="indefinite"/></circle>',
                f'<path d="M560 {y + 48}H582" class="accent-line" '
                'stroke-dasharray="2 3"/>',
            ]
        )
    p.append("</svg>")
    return "".join(p)


def build_heading(label: str) -> str:
    safe = html.escape(label.upper())
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="620" height="34" '
        'viewBox="0 0 620 34">'
        f"<style>{shared_style(safe)}</style>"
        '<circle cx="5" cy="17" r="3" class="accent"/>'
        f'<text x="18" y="21" class="ink" font-family="NovaMono" font-size="11" '
        f'letter-spacing="1.5">{safe}</text>'
        f'<path d="M{max(115, 34 + len(label) * 8)} 17H620" class="line"/>'
        "</svg>"
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    lines = ascii_mark()
    (ASSETS / "hero.svg").write_text(build_hero(lines), encoding="utf-8")
    (ASSETS / "projects.svg").write_text(build_projects(), encoding="utf-8")
    for slug, label in (
        ("about", "Manifesto"),
        ("shipping", "Currently shipping"),
        ("signals", "Public signals"),
        ("contact", "Open channel"),
    ):
        (ASSETS / f"section-{slug}.svg").write_text(
            build_heading(label), encoding="utf-8"
        )
    print("generated hero, project cards, and section headings")


if __name__ == "__main__":
    main()
