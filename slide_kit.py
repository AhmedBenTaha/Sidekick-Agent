"""
Premium Slide Template for Voltway Research.
Generates a visually stunning, dark-mode fleet intelligence slide.
"""

import os
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt, Emu

# ==========================================
# DESIGN SYSTEM & CONSTANTS
# ==========================================

# Color Palette
NAVY_BASE = RGBColor(0x0A, 0x25, 0x40)      # Deep background
NAVY_SURFACE = RGBColor(0x12, 0x30, 0x4D)   # Card backgrounds
NAVY_HIGHLIGHT = RGBColor(0x1A, 0x3B, 0x5C) # Subtle geometric shapes
TEAL_ACCENT = RGBColor(0x00, 0xC2, 0xA8)    # Primary brand accent
TEAL_BRIGHT = RGBColor(0x00, 0xE5, 0xC7)    # Secondary bright accent
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MIST = RGBColor(0xB9, 0xC4, 0xD0)           # Secondary text

# Typography
FONT_FAMILY = "Segoe UI"  # Fallback to Arial/Calibri if Segoe UI is missing

# Layout Dimensions (16:9 Widescreen: 13.333 x 7.5)
SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN_L = 0.8
MARGIN_R = 0.8
CONTENT_W = SLIDE_W - MARGIN_L - MARGIN_R

# Asset Path
LOGO = os.path.join(
    os.path.dirname(__file__),
    "sandbox",
    "skills",
    "fleet-slide",
    "logo.png",
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _add_shape(slide, shape_type, left, top, width, height, fill_color=None, line_color=None, line_width=None):
    """Helper to add and format a shape."""
    shape = slide.shapes.add_shape(
        shape_type, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
        
    if line_color:
        shape.line.color.rgb = line_color
        if line_width:
            shape.line.width = Pt(line_width)
    else:
        shape.line.fill.background()
        
    return shape


def _add_text(slide, left, top, width, height, text, font_size, color, 
              bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font_name=FONT_FAMILY):
    """Helper to add and format a text box."""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font_name
    
    return txBox


# ==========================================
# SLIDE BUILDER
# ==========================================

def build_slide(
    title: str,
    key_points: list[str],
    recommendation: str,
    outfile: str,
) -> None:
    """Build the premium Voltway recommendation deck and save it."""

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    # Use a blank layout
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 1. BACKGROUND & DEPTH
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY_BASE

    # Subtle geometric background elements for depth
    _add_shape(slide, MSO_SHAPE.OVAL, 9.5, -2.0, 6.0, 6.0, fill_color=NAVY_HIGHLIGHT)
    _add_shape(slide, MSO_SHAPE.OVAL, -1.5, 4.5, 5.0, 5.0, fill_color=NAVY_HIGHLIGHT)
    
    # Diagonal subtle accent line in background
    _add_shape(slide, MSO_SHAPE.RECTANGLE, 10.0, 0.0, 0.02, 7.5, fill_color=NAVY_HIGHLIGHT)

    # 2. HEADER & BRANDING
    if os.path.isfile(LOGO):
        slide.shapes.add_picture(LOGO, Inches(MARGIN_L), Inches(0.5), width=Inches(0.5), height=Inches(0.5))
        brand_x = MARGIN_L + 0.7
    else:
        brand_x = MARGIN_L

    # Brand Name with a small teal accent dot
    _add_shape(slide, MSO_SHAPE.OVAL, brand_x, 0.68, 0.12, 0.12, fill_color=TEAL_ACCENT)
    _add_text(slide, brand_x + 0.25, 0.55, 4.0, 0.4, "VOLTWAY RESEARCH", 14, MIST, bold=True)

    # Right-aligned metadata tag
    _add_text(slide, SLIDE_W - MARGIN_R - 3.5, 0.55, 3.5, 0.4, 
              "FLEET INTELLIGENCE  |  CONFIDENTIAL", 10, MIST, align=PP_ALIGN.RIGHT)

    # 3. TITLE SECTION
    # Vertical teal accent bar next to title
    _add_shape(slide, MSO_SHAPE.RECTANGLE, MARGIN_L, 1.6, 0.06, 0.9, fill_color=TEAL_ACCENT)
    
    _add_text(slide, MARGIN_L + 0.3, 1.5, CONTENT_W - 0.3, 1.1, 
              title, 38, WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)

    # 4. KEY POINTS (EDITORIAL INSIGHTS CARDS)
    card_start_y = 3.0
    card_height = 0.75
    card_gap = 0.2
    
    for i, point in enumerate(key_points[:3]):
        y = card_start_y + i * (card_height + card_gap)
        
        # Card Background
        _add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 
                   MARGIN_L, y, CONTENT_W, card_height, 
                   fill_color=NAVY_SURFACE)
        
        # Large faint background number
        _add_text(slide, MARGIN_L + 0.2, y, 0.8, card_height, 
                  f"0{i+1}", 36, NAVY_HIGHLIGHT, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        
        # Vertical separator line inside card
        _add_shape(slide, MSO_SHAPE.RECTANGLE, 
                   MARGIN_L + 1.1, y + 0.15, 0.02, card_height - 0.3, 
                   fill_color=NAVY_HIGHLIGHT)
        
        # Point Text
        _add_text(slide, MARGIN_L + 1.35, y, CONTENT_W - 1.55, card_height, 
                  point, 18, WHITE, anchor=MSO_ANCHOR.MIDDLE)

    # 5. RECOMMENDATION SECTION (PREMIUM CALLOUT)
    rec_y = 5.6
    rec_h = 1.3
    
    # Outer Teal Border (creates a 4px border effect)
    _add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 
               MARGIN_L, rec_y, CONTENT_W, rec_h, 
               fill_color=TEAL_ACCENT)
               
    # Inner Dark Card
    border_thickness = 0.04
    _add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 
               MARGIN_L + border_thickness, rec_y + border_thickness, 
               CONTENT_W - (border_thickness * 2), rec_h - (border_thickness * 2), 
               fill_color=NAVY_BASE)

    # Recommendation Header with icon
    _add_shape(slide, MSO_SHAPE.DIAMOND, MARGIN_L + 0.3, rec_y + 0.25, 0.15, 0.15, fill_color=TEAL_BRIGHT)
    _add_text(slide, MARGIN_L + 0.6, rec_y + 0.2, 4.0, 0.3, 
              "STRATEGIC RECOMMENDATION", 12, TEAL_ACCENT, bold=True)

    # Recommendation Text
    _add_text(slide, MARGIN_L + 0.3, rec_y + 0.55, CONTENT_W - 0.6, rec_h - 0.65, 
              recommendation, 16, WHITE)

    # Save Presentation
    prs.save(outfile)
    print(f"Successfully generated premium slide: {outfile}")


# ==========================================
# EXECUTION EXAMPLE
# ==========================================
if __name__ == "__main__":
    build_slide(
        title="Q3 Fleet Electrification Strategy: Transitioning the Last-Mile Network",
        key_points=[
            "Current diesel fleet operational costs have exceeded baseline projections by 14% due to volatile fuel pricing.",
            "Pilot EV deployments in the Northeast corridor demonstrate a 22% reduction in total cost of ownership (TCO).",
            "Charging infrastructure gaps remain the primary bottleneck for scaling beyond the initial 15% target.",
        ],
        recommendation="Initiate Phase 2 EV rollout focusing exclusively on fixed-route urban deliveries, while simultaneously securing commercial charging partnerships to mitigate infrastructure risk.",
        outfile="voltway_premium_deck.pptx"
    )