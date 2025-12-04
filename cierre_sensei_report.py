from datetime import date
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    """
    Try to load a reasonable TrueType font; fall back to the default bitmap font.
    """
    font_candidates = []

    if bold and italic:
        font_candidates.extend([
            "DejaVuSans-BoldOblique.ttf",
            "Arial Bold Italic.ttf",
        ])
    elif bold:
        font_candidates.extend([
            "DejaVuSans-Bold.ttf",
            "Arial Bold.ttf",
            "Arial-Bold.ttf",
        ])
    elif italic:
        font_candidates.extend([
            "DejaVuSans-Oblique.ttf",
            "Arial Italic.ttf",
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


def generate_cierre_sensei_png(
    purchase_summary: Dict[str, str],
    addons: List[str],
    line_items: List[Tuple[str, float, float, str]],
    est_min: float,
    est_max: float,
    eff_min_pct: float,
    eff_max_pct: float,
    filename: str = "cierre_sensei_report.png",
    prepared_date: Optional[str] = None,
    theme: str = "mockup",
) -> Image.Image:
    """
    Generate a PNG report matching the mockup design.
    
    Args:
        purchase_summary: key/value strings for the summary.
        addons: list of add-on labels.
        line_items: (description, min, max, notes) tuples.
        est_min / est_max: total estimated range.
        eff_min_pct / eff_max_pct: effective percentage range.
        filename: output PNG filename.
        prepared_date: optional date string (e.g. '12/4/2025').
        theme: 'mockup' (matches report_mockup_cursor.png design).
    
    Returns:
        PIL Image object.
    """
    
    # Canvas setup - matching mockup dimensions
    WIDTH, HEIGHT = 1800, 2400
    margin_x = 120
    margin_y = 100
    
    # Dark blue-grey background (RGB: 30, 50, 80)
    bg_color = (30, 50, 80)
    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Color scheme matching mockup
    light_blue = (100, 150, 255)  # Light blue for titles
    white = (255, 255, 255)       # White for body text
    separator_color = (150, 180, 220)  # Light grey-blue for separator lines
    
    # Fonts
    title_font = _load_font(72, bold=True)
    section_font = _load_font(42, bold=True)
    normal_font = _load_font(32)
    small_font = _load_font(28)
    totals_font = _load_font(38, bold=True)
    
    # Prepare date
    if prepared_date is None:
        prepared_date = date.today().strftime("%-m/%-d/%Y")
    
    y = margin_y
    
    # ================================================================
    # HEADER - Title
    # ================================================================
    title_text = "Estimated Closing Costs (MX Real Estate)"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (WIDTH - title_w) // 2
    
    draw.text((title_x, y), title_text, font=title_font, fill=light_blue)
    y += title_font.size + 60
    
    # Separator line
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # PURCHASE SUMMARY
    # ================================================================
    for key, value in purchase_summary.items():
        text = f"{key}: {value}"
        draw.text((margin_x, y), text, font=normal_font, fill=white)
        y += normal_font.size + 12
    
    y += 30
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # FEE BREAKDOWN Section
    # ================================================================
    section_title = "Fee Breakdown:"
    draw.text((margin_x, y), section_title, font=section_font, fill=light_blue)
    y += section_font.size + 20
    
    def fmt_currency(val: float) -> str:
        return "${:,.0f}".format(val)
    
    for desc, min_v, max_v, notes in line_items:
        # Description
        draw.text((margin_x, y), desc, font=normal_font, fill=white)
        
        # Amount range
        if min_v == max_v:
            amount_text = fmt_currency(min_v)
        else:
            amount_text = f"{fmt_currency(min_v)} - {fmt_currency(max_v)}"
        
        # Position amount (right-aligned would be better, but keeping simple for now)
        amount_x = margin_x + 500
        draw.text((amount_x, y), amount_text, font=normal_font, fill=white)
        
        # Notes if present
        if notes:
            notes_x = margin_x + 900
            draw.text((notes_x, y), f"({notes})", font=small_font, fill=white)
        
        y += normal_font.size + 16
    
    y += 30
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # ESTIMATED TOTALS
    # ================================================================
    # Estimated Range
    range_text = f"Estimated Range: {fmt_currency(est_min)} - {fmt_currency(est_max)}"
    draw.text((margin_x, y), range_text, font=totals_font, fill=white)
    y += totals_font.size + 20
    
    # Effective Rate
    rate_text = f"Effective Rate: {eff_min_pct:.1f}% - {eff_max_pct:.1f}%"
    draw.text((margin_x, y), rate_text, font=totals_font, fill=white)
    y += totals_font.size + 30
    
    draw.line((margin_x, y, WIDTH - margin_x, y), fill=separator_color, width=2)
    y += 40
    
    # ================================================================
    # ADD-ONS INCLUDED Section
    # ================================================================
    section_title = "Add-Ons Included:"
    draw.text((margin_x, y), section_title, font=section_font, fill=light_blue)
    y += section_font.size + 20
    
    for item in addons:
        draw.text((margin_x + 40, y), f"- {item}", font=normal_font, fill=white)
        y += normal_font.size + 12
    
    y += 30
    
    # ================================================================
    # FOOTER
    # ================================================================
    footer_y = HEIGHT - 80
    
    # Prepared date
    prepared_text = f"Prepared: {prepared_date}"
    draw.text((margin_x, footer_y), prepared_text, font=small_font, fill=white)
    
    # Disclaimer
    disclaimer = "Informational only; confirm with local professionals."
    disc_bbox = draw.textbbox((0, 0), disclaimer, font=small_font)
    disc_w = disc_bbox[2] - disc_bbox[0]
    disc_x = WIDTH - margin_x - disc_w
    draw.text((disc_x, footer_y), disclaimer, font=small_font, fill=white)
    
    img.save(filename)
    return img


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
        filename="cierre_sensei_report_mockup.png",
        prepared_date="12/4/2025",
        theme="mockup",
    )
    print("Saved cierre_sensei_report_mockup.png")

