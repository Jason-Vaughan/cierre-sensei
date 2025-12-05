from datetime import date
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Try to load a reasonable TrueType font; fall back to the default bitmap font.
    """
    font_candidates = []
    if bold:
        font_candidates.extend([
            "DejaVuSans-Bold.ttf",
            "Arial Bold.ttf",
            "Arial-Bold.ttf",
        ])
    else:
        font_candidates.extend([
            "DejaVuSans.ttf",
            "Arial.ttf",
        ])

    for name in font_candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue

    # Fallback – always available but not as pretty
    return ImageFont.load_default()


def _get_font_size(font) -> int:
    """Get font size, handling both TrueType and default fonts."""
    try:
        return font.size
    except AttributeError:
        # Default font doesn't have .size, estimate from textbbox
        bbox = ImageDraw.Draw(Image.new("RGB", (100, 100))).textbbox((0, 0), "M", font=font)
        return bbox[3] - bbox[1] if len(bbox) == 4 else 12


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
    theme: str = "dark",
    sponsor_text: str | None = None,
) -> Image.Image:
    """
    Generate a printable PNG report for Cierre Sensei.
    
    Args:
        purchase_summary: dict with keys like Purchase Price, Type, State, etc.
        addons: list of strings, e.g. ["Title Insurance", "Home Inspection", ...]
        line_items: list of tuples: (description, min_amount, max_amount, notes)
        est_min / est_max: numeric totals for the estimated range
        eff_min_pct / eff_max_pct: effective % of purchase price
        filename: output PNG filename
        prepared_date: optional string like "12/1/2025"; if None, today is used
        theme: "dark" (dark blue background) or "light" (white background, printer-friendly)
        sponsor_text: optional text to display centered above footer
    """
    
    # Theme-based color scheme
    if theme == "light":
        # Light theme: white background, black text (printer-friendly)
        bg_color = (255, 255, 255)
        title_color = (0, 0, 0)
        text_color = (0, 0, 0)
        separator_color = (0, 0, 0)
        box_outline = (0, 0, 0)
    else:
        # Dark theme: dark blue background (default)
        bg_color = (30, 50, 80)
        title_color = (100, 150, 255)
        text_color = (255, 255, 255)
        separator_color = (150, 180, 220)
        box_outline = (150, 180, 220)
    
    # Canvas setup (US Letter @ ~300dpi)
    WIDTH, HEIGHT = 2550, 3300
    margin_x = 260
    margin_y = 260
    
    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    title_font = _load_font(80, bold=True)
    subtitle_font = _load_font(44, bold=False)
    normal_font = _load_font(34)
    small_bold = _load_font(30, bold=True)
    
    # Prepare date - cross-platform format
    if prepared_date is None:
        today = date.today()
        prepared_date = f"{today.month}/{today.day}/{today.year}"
    
    # --- Header ---
    y = margin_y
    title_text = "Cierre Sensei"
    prepared_text = f"Prepared: {prepared_date}"
    
    draw.text((margin_x, y), title_text, font=title_font, fill=title_color)
    
    # Right-aligned prepared date
    bbox = draw.textbbox((0, 0), prepared_text, font=small_bold)
    date_w = bbox[2] - bbox[0]
    draw.text((WIDTH - margin_x - date_w, y + 10),
              prepared_text, font=small_bold, fill=text_color)
    
    y += _get_font_size(title_font) + 40
    draw.text((margin_x, y), "Closing Costs Estimation",
              font=subtitle_font, fill=text_color)
    y += _get_font_size(subtitle_font) + 40
    
    # --- Add-ons (left) ---
    ax = margin_x
    ay = y
    draw.text((ax, ay), "Addons:", font=normal_font, fill=text_color)
    ay += _get_font_size(normal_font) + 12
    
    for item in addons:
        draw.text((ax + 40, ay), f"• {item}", font=normal_font, fill=text_color)
        ay += _get_font_size(normal_font) + 10
    
    addons_bottom = ay
    
    # --- Purchase summary box (right) ---
    box_width = 860
    bx = WIDTH - margin_x - box_width
    by = y
    
    lines = [f"{k}:  {v}" for k, v in purchase_summary.items()]
    line_height = _get_font_size(normal_font) + 8
    box_height = line_height * len(lines) + 26
    
    draw.rectangle([bx, by, bx + box_width, by + box_height],
                   outline=box_outline, width=3)
    
    ty = by + 14
    for line in lines:
        draw.text((bx + 18, ty), line, font=normal_font, fill=text_color)
        ty += line_height
    
    summary_bottom = by + box_height
    
    # Move y below the higher of the two blocks
    y = max(addons_bottom, summary_bottom) + 90
    
    # --- Table header ---
    desc_x = margin_x
    min_x = desc_x + 900
    max_x = min_x + 420
    notes_x = max_x + 420
    
    header_y = y
    draw.text((desc_x, header_y), "Description",
              font=small_bold, fill=text_color)
    draw.text((min_x, header_y), "Min Amount",
              font=small_bold, fill=text_color)
    draw.text((max_x, header_y), "Max Amount",
              font=small_bold, fill=text_color)
    draw.text((notes_x, header_y), "Notes",
              font=small_bold, fill=text_color)
    
    y += _get_font_size(small_bold) + 12
    draw.line((margin_x, y, WIDTH - margin_x, y),
              fill=separator_color, width=2)
    y += 26
    
    # --- Table rows ---
    def fmt_currency(val: float) -> str:
        return "${:,.0f}".format(val)
    
    row_height = _get_font_size(normal_font) + 18
    
    for desc, min_v, max_v, notes in line_items:
        # description
        draw.text((desc_x, y), desc, font=normal_font, fill=text_color)
        
        # min / max
        draw.text((min_x, y), fmt_currency(min_v),
                  font=normal_font, fill=text_color)
        draw.text((max_x, y), fmt_currency(max_v),
                  font=normal_font, fill=text_color)
        
        # notes
        if notes:
            draw.text((notes_x, y), notes, font=normal_font, fill=text_color)
        
        y += row_height
    
    # --- Totals section ---
    y += 100
    # Estimated Range label and value
    draw.text((margin_x, y), "Estimated Range:",
              font=_load_font(40, bold=True), fill=text_color)
    draw.text((margin_x + 420, y),
              f"{fmt_currency(est_min)} – {fmt_currency(est_max)}",
              font=_load_font(40), fill=text_color)
    
    y += 40 + 18
    
    # Effective Rate label and value
    draw.text((margin_x, y), "Effective Rate %:",
              font=_load_font(40, bold=True), fill=text_color)
    draw.text((margin_x + 420, y),
              f"{eff_min_pct:.1f}% – {eff_max_pct:.1f}%",
              font=_load_font(40), fill=text_color)
    
    # --- SPONSOR TEXT (if provided) ---
    if sponsor_text:
        sponsor_y = HEIGHT - 140
        sponsor_bbox = draw.textbbox((0, 0), sponsor_text, font=small_bold)
        sponsor_w = sponsor_bbox[2] - sponsor_bbox[0]
        sponsor_x = (WIDTH - sponsor_w) // 2
        draw.text((sponsor_x, sponsor_y), sponsor_text, font=small_bold, fill=text_color)
    
    # --- FOOTER ---
    footer_y = HEIGHT - 80
    
    # Disclaimer
    disclaimer = "Informational only; confirm with local professionals."
    disc_bbox = draw.textbbox((0, 0), disclaimer, font=small_bold)
    disc_w = disc_bbox[2] - disc_bbox[0]
    disc_x = WIDTH - margin_x - disc_w
    draw.text((disc_x, footer_y), disclaimer, font=small_bold, fill=text_color)
    
    img.save(filename)
    return img


# --------------------------------------------------------------------
# Example stand-alone usage
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
        theme="dark",
    )

    print("Saved cierre_sensei_report.png")
