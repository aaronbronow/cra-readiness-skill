#!/usr/bin/env python3
"""
Generates an updated 1280x640 Social Card layout using REAL, official logos:
- Removed top pill tag and bottom footnote text
- Title & subtitle moved to the top (within safe margins)
- Two rows of dashboard cards using authentic logos:
  Row 1 (Supported AI Agents): Claude Code, Cursor, Gemini CLI, GitHub Copilot
  Row 2 (Ecosystem & Authority): Packablock, GitHub Actions, Eclipse ORC, CE Mark
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 640

img = Image.new("RGBA", (WIDTH, HEIGHT), (8, 14, 24, 255))
draw = ImageDraw.Draw(img)

# 1. Background gradient (dark midnight slate)
for y in range(HEIGHT):
    factor = y / HEIGHT
    r = int(8 + factor * 6)
    g = int(14 + factor * 10)
    b = int(24 + factor * 18)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

# Cyan/blue ambient glow at center-top
glow_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_overlay)

cx_glow, cy_glow = int(WIDTH * 0.5), int(HEIGHT * 0.35)
for rad in range(550, 0, -20):
    alpha = int((1.0 - (rad / 550)) * 28)
    glow_draw.ellipse(
        [(cx_glow - rad, cy_glow - rad), (cx_glow + rad, cy_glow + rad)],
        fill=(14, 165, 233, alpha),
    )

# Subtle blueprint grid lines
grid_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
grid_draw = ImageDraw.Draw(grid_overlay)
for x in range(40, WIDTH, 80):
    grid_draw.line([(x, 0), (x, HEIGHT)], fill=(56, 189, 248, 10), width=1)
for y in range(40, HEIGHT, 80):
    grid_draw.line([(0, y), (WIDTH, y)], fill=(56, 189, 248, 10), width=1)

img = Image.alpha_composite(img, glow_overlay)
img = Image.alpha_composite(img, grid_overlay)
draw = ImageDraw.Draw(img)

# 2. Viewfinder HUD Corner Brackets
bracket_color = (56, 189, 248, 200)
bw = 36
bt = 3
m = 28

# Top-Left
draw.line([(m, m), (m + bw, m)], fill=bracket_color, width=bt)
draw.line([(m, m), (m, m + bw)], fill=bracket_color, width=bt)
# Top-Right
draw.line([(WIDTH - m - bw, m), (WIDTH - m, m)], fill=bracket_color, width=bt)
draw.line([(WIDTH - m, m), (WIDTH - m, m + bw)], fill=bracket_color, width=bt)
# Bottom-Left
draw.line([(m, HEIGHT - m), (m + bw, HEIGHT - m)], fill=bracket_color, width=bt)
draw.line([(m, HEIGHT - m - bw), (m, HEIGHT - m)], fill=bracket_color, width=bt)
# Bottom-Right
draw.line([(WIDTH - m - bw, HEIGHT - m), (WIDTH - m, HEIGHT - m)], fill=bracket_color, width=bt)
draw.line([(WIDTH - m, HEIGHT - m - bw), (WIDTH - m, HEIGHT - m)], fill=bracket_color, width=bt)

# 3. Typography
bold_font = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
reg_font = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

f_title = ImageFont.truetype(bold_font, 64)
f_subtitle = ImageFont.truetype(bold_font, 26)
f_row_label = ImageFont.truetype(bold_font, 13)
f_card_title = ImageFont.truetype(bold_font, 18)
f_card_sub = ImageFont.truetype(reg_font, 13)

# 4. Header Section: Title & Subtitle moved to top within safe margins
title_text = "cra-readiness-skill"
tb = f_title.getbbox(title_text)
tw = tb[2] - tb[0]
tx = (WIDTH - tw) // 2
ty = 65

# Soft title glow
t_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
tg_draw = ImageDraw.Draw(t_glow)
tg_draw.text((tx, ty), title_text, font=f_title, fill=(56, 189, 248, 35))
img = Image.alpha_composite(img, t_glow)
draw = ImageDraw.Draw(img)

draw.text((tx, ty), title_text, font=f_title, fill=(255, 255, 255))

# Subtitle (One-line value proposition)
sub_text = "Turn EU Cyber Resilience Act compliance into routine engineering."
sb = f_subtitle.getbbox(sub_text)
sw = sb[2] - sb[0]
sx = (WIDTH - sw) // 2
sy = 145

draw.text((sx, sy), sub_text, font=f_subtitle, fill=(203, 213, 225))

# 5. Row 1: Supported AI Agents
row1_label = "SUPPORTED AI AGENTS"
r1_box = f_row_label.getbbox(row1_label)
r1_w = r1_box[2] - r1_box[0]
r1_label_y = 205
draw.text((95, r1_label_y), row1_label, font=f_row_label, fill=(56, 189, 248))
draw.line([(95 + r1_w + 14, r1_label_y + 8), (WIDTH - 95, r1_label_y + 8)], fill=(30, 58, 95, 180), width=1)

row1_cards = [
    {
        "name": "Claude Code",
        "role": "Agent CLI & Skills",
        "color": (217, 119, 6),        # Amber
        "logo_file": "docs/assets/logos/claude.png",
        "invert_logo": True,
    },
    {
        "name": "Cursor",
        "role": "IDE Rules & Workspaces",
        "color": (168, 85, 247),       # Purple
        "logo_file": "docs/assets/logos/cursor.png",
        "invert_logo": True,
    },
    {
        "name": "Gemini CLI",
        "role": "Antigravity & AGY",
        "color": (59, 130, 246),       # Google Blue
        "logo_file": "docs/assets/logos/gemini.png",
        "invert_logo": True,
    },
    {
        "name": "GitHub Copilot",
        "role": "VS Code Agent Mode",
        "color": (16, 185, 129),       # Emerald
        "logo_file": "docs/assets/logos/copilot.png",
        "invert_logo": True,
    },
]

# 6. Row 2: Ecosystem & Regulatory Frameworks
row2_label = "ECOSYSTEM & REGULATORY FRAMEWORKS"
r2_box = f_row_label.getbbox(row2_label)
r2_w = r2_box[2] - r2_box[0]
r2_label_y = 405
draw.text((95, r2_label_y), row2_label, font=f_row_label, fill=(56, 189, 248))
draw.line([(95 + r2_w + 14, r2_label_y + 8), (WIDTH - 95, r2_label_y + 8)], fill=(30, 58, 95, 180), width=1)

row2_cards = [
    {
        "name": "Packablock",
        "role": "Supply Chain Attestation",
        "color": (249, 115, 22),       # Orange
        "logo_file": "docs/assets/logos/packablock.png",
        "invert_logo": False,
    },
    {
        "name": "GitHub Actions",
        "role": "Headless CI/CD Pipeline",
        "color": (34, 197, 94),        # Green
        "logo_file": "docs/assets/logos/githubactions.png",
        "invert_logo": True,
    },
    {
        "name": "Eclipse ORC",
        "role": "Open Regulatory Matrix",
        "color": (14, 165, 233),       # Cyan
        "logo_file": "docs/assets/logos/eclipse.png",
        "invert_logo": True,
    },
    {
        "name": "CE Mark",
        "role": "Module A Self-Declaration",
        "color": (234, 179, 8),        # Gold / Yellow
        "logo_file": "docs/assets/logos/ce.png",
        "invert_logo": True,
    },
]

card_w = 260
card_h = 135
card_gap = 16
total_w = 4 * card_w + 3 * card_gap
start_x = (WIDTH - total_w) // 2

def draw_card(cx, cy, c):
    global img, draw
    col = c["color"]
    # Outer card
    draw.rounded_rectangle(
        [(cx, cy), (cx + card_w, cy + card_h)],
        radius=14,
        fill=(13, 22, 38, 240),
        outline=(30, 58, 95, 230),
        width=2,
    )
    # Top color stripe
    draw.rounded_rectangle(
        [(cx + 16, cy + 2), (cx + card_w - 16, cy + 4)],
        radius=2,
        fill=col,
    )

    # Icon container
    ix = cx + 18
    iy = cy + 24
    iw = 48
    ih = 48
    draw.rounded_rectangle(
        [(ix, iy), (ix + iw, iy + ih)],
        radius=10,
        fill=(col[0] // 5, col[1] // 5, col[2] // 5, 255),
        outline=col,
        width=2,
    )

    # Paste real logo
    logo_path = Path(c["logo_file"])
    if logo_path.exists():
        logo_im = Image.open(logo_path).convert("RGBA")
        
        # Fit inside 32x32 inner area with aspect ratio preserved
        target_size = 32
        logo_im.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        
        # If invert_logo (white silhouette), tint non-transparent pixels to white
        if c.get("invert_logo", False):
            r, g, b, a = logo_im.split()
            white_fill = Image.new("RGBA", logo_im.size, (255, 255, 255, 255))
            logo_im = Image.composite(white_fill, Image.new("RGBA", logo_im.size, (0, 0, 0, 0)), a)

        # Center inside container
        paste_x = ix + (iw - logo_im.width) // 2
        paste_y = iy + (ih - logo_im.height) // 2
        img.paste(logo_im, (paste_x, paste_y), logo_im)
        draw = ImageDraw.Draw(img)

    # Text Block
    tx_text = ix + iw + 14
    draw.text((tx_text, cy + 28), c["name"], font=f_card_title, fill=(255, 255, 255))
    draw.text((tx_text, cy + 56), c["role"], font=f_card_sub, fill=(148, 163, 184))

# Draw Row 1 (Agents)
r1_y = 232
for i, c in enumerate(row1_cards):
    draw_card(start_x + i * (card_w + card_gap), r1_y, c)

# Draw Row 2 (Ecosystem)
r2_y = 432
for i, c in enumerate(row2_cards):
    draw_card(start_x + i * (card_w + card_gap), r2_y, c)

# Save image
out_png = "docs/assets/social-preview.png"
img.convert("RGB").save(out_png, "PNG", optimize=True)
print(f"Generated 2-row social card with REAL logos at {out_png} ({WIDTH}x{HEIGHT})")
