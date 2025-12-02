from datetime import date

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Try to load a reasonable TrueType font; fall back to the default bitmap font.
    """
    font_candidates = []
    if bold:
        font_candidates.extend(
            [
                "DejaVuSans-Bold.ttf",
                "Arial Bold.ttf",
                "Arial-Bold.ttf",
            ]
        )
    else:
        font_candidates.extend(
            [
                "DejaVuSans.ttf",
                "Arial.ttf",
            ]
        )

    for name in font_candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue

    # Fallback – always available but not as pretty
    return ImageFont.load_default()


def generate_cierre_sensei_png(
    purchase_summary: dict,
    addons: list,
    line_items: list,
    est_min: float,
    est_max: float,
    eff_min_pct: float,
    eff_max_pct: float,
    filename: str = "cierre_sensei_report.png",
    prepared_date: str | None = None,
) -> Image.Image:
    """
    Generate a printable PNG report for Cierre Sensei.

    purchase_summary: dict with keys like:
        {
            "Purchase Price": "$500,000 USD",
            "Type": "Condo",
            "State": "Quintana Roo",
            "Restricted Zone": "Yes",
            "Foreign Buyer": "Yes",
        }

    addons: list of strings, e.g. ["Title Insurance", "Home Inspection", ...]

    line_items: list of tuples:
        [
            ("ISAI 3%", 15000, 15000, "% of purchase price"),
            ("Notarial Fees", 3000, 4500, "Range"),
            ...
        ]

    est_min / est_max: numeric totals for the estimated range.
    eff_min_pct / eff_max_pct: effective % of purchase price.
    filename: output PNG filename.
    prepared_date: optional string like "12/1/2025"; if None, today is used.
    """

    # --- Canvas setup (US Letter @ ~300dpi) ---
    WIDTH, HEIGHT = 2550, 3300          # 8.5" x 11" at 300 dpi
    margin_x = 260                      # nice whitespace at edges
    margin_y = 260

    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    title_font = _load_font(80, bold=True)
    subtitle_font = _load_font(44, bold=False)
    normal_font = _load_font(34)
    small_bold = _load_font(30, bold=True)
    totals_label_font = _load_font(40, bold=True)
    totals_value_font = _load_font(40, bold=False)

    # --- Header ---
    y = margin_y
    title_text = "Cierre Sensei"
    if prepared_date is None:
        prepared_date = date.today().strftime("%-m/%-d/%Y")
    prepared_text = f"Prepared: {prepared_date}"

    draw.text((margin_x, y), title_text, font=title_font, fill="black")

    # Right-aligned prepared date
    bbox = draw.textbbox((0, 0), prepared_text, font=small_bold)
    date_w = bbox[2] - bbox[0]
    draw.text(
        (WIDTH - margin_x - date_w, y + 10),
        prepared_text,
        font=small_bold,
        fill="black",
    )

    y += title_font.size + 40
    draw.text(
        (margin_x, y),
        "Closing Costs Estimation",
        font=subtitle_font,
        fill="black",
    )
    y += subtitle_font.size + 40

    # --- Add-ons (left) ---
    ax = margin_x
    ay = y
    draw.text((ax, ay), "Addons:", font=normal_font, fill="black")
    ay += normal_font.size + 12

    for item in addons:
        draw.text((ax + 40, ay), f"• {item}", font=normal_font, fill="black")
        ay += normal_font.size + 10

    addons_bottom = ay

    # --- Purchase summary box (right) ---
    box_width = 860
    bx = WIDTH - margin_x - box_width
    by = y

    lines = [f"{k}:  {v}" for k, v in purchase_summary.items()]
    line_height = normal_font.size + 8
    box_height = line_height * len(lines) + 26

    draw.rectangle(
        [bx, by, bx + box_width, by + box_height],
        outline="black",
        width=3,
    )

    ty = by + 14
    for line in lines:
        draw.text((bx + 18, ty), line, font=normal_font, fill="black")
        ty += line_height

    summary_bottom = by + box_height

    # Move y below the lower of the two blocks
    y = max(addons_bottom, summary_bottom) + 90

    # --- Table header ---
    desc_x = margin_x

    # Columns nudged slightly left and tightened so Notes stays on-page
    min_x = desc_x + 900      # was 920
    max_x = min_x + 420       # was 520
    notes_x = max_x + 420     # was 520

    header_y = y
    draw.text(
        (desc_x, header_y),
        "Description",
        font=small_bold,
        fill="black",
    )
    draw.text(
        (min_x, header_y),
        "Min Amount",
        font=small_bold,
        fill="black",
    )
    draw.text(
        (max_x, header_y),
        "Max Amount",
        font=small_bold,
        fill="black",
    )
    draw.text(
        (notes_x, header_y),
        "Notes",
        font=small_bold,
        fill="black",
    )

    y += small_bold.size + 12
    draw.line(
        (margin_x, y, WIDTH - margin_x, y),
        fill="black",
        width=2,
    )
    y += 26

    # --- Table rows ---
    def fmt_currency(val: float) -> str:
        return "${:,.0f}".format(val)

    row_height = normal_font.size + 18

    for desc, min_v, max_v, notes in line_items:
        # description
        draw.text((desc_x, y), desc, font=normal_font, fill="black")

        # min / max
        draw.text(
            (min_x, y),
            fmt_currency(min_v),
            font=normal_font,
            fill="black",
        )
        draw.text(
            (max_x, y),
            fmt_currency(max_v),
            font=normal_font,
            fill="black",
        )

        # notes (kept as single-line; your notes are short)
        if notes:
            draw.text((notes_x, y), notes, font=normal_font, fill="black")

        y += row_height

    # --- Totals section (dropped lower, larger text, better spacing) ---
    y += row_height * 8  # push totals further down from the table

    VALUE_OFFSET = 520  # horizontal spacing between label and value

    # Estimated Range
    draw.text(
        (margin_x, y),
        "Estimated Range:",
        font=totals_label_font,
        fill="black",
    )
    draw.text(
        (margin_x + VALUE_OFFSET, y),
        f"{fmt_currency(est_min)} – {fmt_currency(est_max)}",
        font=totals_value_font,
        fill="black",
    )

    # Effective Rate
    y += totals_value_font.size + 20
    draw.text(
        (margin_x, y),
        "Effective Rate %:",
        font=totals_label_font,
        fill="black",
    )
    draw.text(
        (margin_x + VALUE_OFFSET, y),
        f"{eff_min_pct:.1f}% – {eff_max_pct:.1f}%",
        font=totals_value_font,
        fill="black",
    )

    # Save and return image
    img.save(filename)
    return img


# --------------------------------------------------------------------
# Example stand-alone usage (matches your layout).
# --------------------------------------------------------------------
if __name__ == "__main__":
    purchase_summary_example = {
        "Purchase Price": "$500,000 USD",
        "Type": "Condo",
        "State": "Quintana Roo",
        "Restricted Zone": "Yes",
        "Foreign Buyer": "Yes",
    }

    addons_example = [
        "Title Insurance",
        "Home Inspection",
        "Attorney",
        "Translator",
        "Closing Coordinator",
    ]

    line_items_example = [
        ("ISAI 3%",            15000, 15000, "% of purchase price"),
        ("Notarial Fees",       3000,  4500, "Range"),
        ("Registration",        1500,  2500, ""),
        ("Escrow",               750,   750, "Flat fee"),
        ("Certificates",          40,    60, ""),
        ("Appraisal",            500,  2500, ""),
        ("Fideicomiso Setup",   1000,  2000, "If restricted + foreign"),
        ("Fideicomiso Permit",  1100,  1100, "One-time fee"),
        ("Fideicomiso Annual",   500,   800, "Recurring"),
        ("Title Insurance",     1500,  1500, ""),
        ("Home Inspection",      500,   500, ""),
        ("Attorney",            2500,  2500, ""),
        ("Translator",           500,   500, ""),
        ("Closing Coordinator",  750,   750, ""),
    ]

    img = generate_cierre_sensei_png(
        purchase_summary=purchase_summary_example,
        addons=addons_example,
        line_items=line_items_example,
        est_min=29140,
        est_max=34960,
        eff_min_pct=5.8,
        eff_max_pct=7.0,
        filename="cierre_sensei_report.png",
        prepared_date="12/1/2025",
    )

    print("Saved cierre_sensei_report.png")

