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
        separator_color = (100, 100, 100)
        box_outline = (0, 0, 0)
    else:
        # Dark theme: dark blue background (default)
        bg_color = (30, 50, 80)
        title_color = (100, 150, 255)
        text_color = (255, 255, 255)
        separator_color = (150, 180, 220)
        box_outline = (150, 180, 220)
    
    # Canvas setup - matching mockup dimensions
    WIDTH, HEIGHT = 1800, 2400
    margin_x = 120
    margin_y = 100
    
    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    title_font = _load_font(72, bold=True)
    section_font = _load_font(42, bold=True)
    normal_font = _load_font(32)
    small_font = _load_font(28)
    totals_font = _load_font(38, bold=True)
    
    # Prepare date - cross-platform format
    if prepared_date is None:
        today = date.today()
        # Use format that works on all platforms
        prepared_date = f"{today.month}/{today.day}/{today.year}"
    
    y = margin_y
    
    # ================================================================
    # HEADER - Title
    # ================================================================
    title_text = "Estimated Closing Costs (MX Real Estate)"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (WIDTH - title_w) // 2
    
    draw.text((title_x, y), title_text, font=title_font, fill=title_color)
    y += _get_font_size(title_font) + 60
    
    # Separator line
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # PURCHASE SUMMARY
    # ================================================================
    for key, value in purchase_summary.items():
        text = f"{key}: {value}"
        draw.text((margin_x, y), text, font=normal_font, fill=text_color)
        y += _get_font_size(normal_font) + 12
    
    y += 30
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # FEE BREAKDOWN Section
    # ================================================================
    section_title = "Fee Breakdown:"
    draw.text((margin_x, y), section_title, font=section_font, fill=title_color)
    y += _get_font_size(section_font) + 20
    
    def fmt_currency(val: float) -> str:
        return "${:,.0f}".format(val)
    
    for desc, min_v, max_v, notes in line_items:
        # Description
        draw.text((margin_x, y), desc, font=normal_font, fill=text_color)
        
        # Amount range
        if min_v == max_v:
            amount_text = fmt_currency(min_v)
        else:
            amount_text = f"{fmt_currency(min_v)} - {fmt_currency(max_v)}"
        
        # Position amount
        amount_x = margin_x + 500
        draw.text((amount_x, y), amount_text, font=normal_font, fill=text_color)
        
        # Notes if present
        if notes:
            notes_x = margin_x + 900
            draw.text((notes_x, y), f"({notes})", font=small_font, fill=text_color)
        
        y += _get_font_size(normal_font) + 16
    
    y += 30
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # ESTIMATED TOTALS
    # ================================================================
    # Estimated Range
    range_text = f"Estimated Range: {fmt_currency(est_min)} - {fmt_currency(est_max)}"
    draw.text((margin_x, y), range_text, font=totals_font, fill=text_color)
    y += _get_font_size(totals_font) + 20
    
    # Effective Rate
    rate_text = f"Effective Rate: {eff_min_pct:.1f}% - {eff_max_pct:.1f}%"
    draw.text((margin_x, y), rate_text, font=totals_font, fill=text_color)
    y += _get_font_size(totals_font) + 30
    
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # ADD-ONS INCLUDED Section
    # ================================================================
    section_title = "Add-Ons Included:"
    draw.text((margin_x, y), section_title, font=section_font, fill=title_color)
    y += _get_font_size(section_font) + 20
    
    for item in addons:
        draw.text((margin_x + 40, y), f"- {item}", font=normal_font, fill=text_color)
        y += _get_font_size(normal_font) + 12
    
    y += 30
    
    # ================================================================
    # SPONSOR TEXT (if provided)
    # ================================================================
    if sponsor_text:
        sponsor_y = HEIGHT - 140
        sponsor_bbox = draw.textbbox((0, 0), sponsor_text, font=small_font)
        sponsor_w = sponsor_bbox[2] - sponsor_bbox[0]
        sponsor_x = (WIDTH - sponsor_w) // 2
        draw.text((sponsor_x, sponsor_y), sponsor_text, font=small_font, fill=text_color)
    
    # ================================================================
    # FOOTER
    # ================================================================
    footer_y = HEIGHT - 80
    
    # Prepared date
    prepared_text = f"Prepared: {prepared_date}"
    draw.text((margin_x, footer_y), prepared_text, font=small_font, fill=text_color)
    
    # Disclaimer
    disclaimer = "Informational only; confirm with local professionals."
    disc_bbox = draw.textbbox((0, 0), disclaimer, font=small_font)
    disc_w = disc_bbox[2] - disc_bbox[0]
    disc_x = WIDTH - margin_x - disc_w
    draw.text((disc_x, footer_y), disclaimer, font=small_font, fill=text_color)
    
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
