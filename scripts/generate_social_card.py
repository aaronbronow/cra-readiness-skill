#!/usr/bin/env python3
"""
Generates a simplified, high-contrast 1280x640 Social Card (Open Graph Image)
optimized for mobile search results, social feeds, and small preview thumbnails.

Focused entirely on 3 core elements:
1. Tool Name: cra-readiness-skill (massive, bold, readable)
2. One-line Value Prop: Turn EU Cyber Resilience Act compliance into routine engineering.
3. Badges / Compatibility Marks:
   - Packablock
   - Eclipse ORC
   - Cursor IDE
   - Claude Code
"""

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 640

img = Image.new("RGBA", (WIDTH, HEIGHT), (8, 14, 24, 255))
draw = ImageDraw.Draw(img)

# 1. Background: Deep rich tech gradient with ambient glow
for y in range(HEIGHT):
    factor = y / HEIGHT
    r = int(8 + factor * 6)
    g = int(14 + factor * 10)
    b = int(24 + factor * 18)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

# Strong central cyan/emerald ambient glow
glow_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_overlay)

cx_glow, cy_glow = int(WIDTH * 0.5), int(HEIGHT * 0.42)
for rad in range(550, 0, -20):
    alpha = int((1.0 - (rad / 550)) * 32)
    glow_draw.ellipse(
        [(cx_glow - rad, cy_glow - rad), (cx_glow + rad, cy_glow + rad)],
        fill=(14, 165, 233, alpha),
    )

# Subtle blueprint grid lines
grid_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
grid_draw = ImageDraw.Draw(grid_overlay)
for x in range(40, WIDTH, 80):
    grid_draw.line([(x, 0), (x, HEIGHT)], fill=(56, 189, 248, 12), width=1)
for y in range(40, HEIGHT, 80):
    grid_draw.line([(0, y), (WIDTH, y)], fill=(56, 189, 248, 12), width=1)

img = Image.alpha_composite(img, glow_overlay)
img = Image.alpha_composite(img, grid_overlay)
draw = ImageDraw.Draw(img)

# 2. Tech Viewfinder Corner Brackets
bracket_color = (56, 189, 248, 200)
bw = 36
bt = 3
m = 28  # margin

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

# 3. Fonts
bold_font = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
reg_font = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
mono_bold = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

f_top_pill = ImageFont.truetype(bold_font, 18)
f_title = ImageFont.truetype(bold_font, 68)
f_value_prop = ImageFont.truetype(bold_font, 28)
f_badge_title = ImageFont.truetype(bold_font, 20)
f_badge_sub = ImageFont.truetype(reg_font, 14)

# 4. Top Category Pill: "EU REGULATION 2024/2847 • CRA COMPLIANCE SKILL"
top_pill_text = "EU REGULATION 2024/2847  •  OPEN SOURCE COMPLIANCE SKILL"
tb = f_top_pill.getbbox(top_pill_text)
tb_w = tb[2] - tb[0]
tb_h = tb[3] - tb[1]
px = (WIDTH - tb_w) // 2
py = 90

draw.rounded_rectangle(
    [(px - 24, py - 10), (px + tb_w + 24, py + tb_h + 10)],
    radius=20,
    fill=(15, 23, 42, 230),
    outline=(56, 189, 248, 180),
    width=1,
)
draw.text((px, py - 2), top_pill_text, font=f_top_pill, fill=(56, 189, 248))

# 5. Core Element 1: Tool Name (Giant, crystal-clear typography)
title_text = "cra-readiness-skill"
t_box = f_title.getbbox(title_text)
t_w = t_box[2] - t_box[0]
t_x = (WIDTH - t_w) // 2
t_y = 175

# Glow behind the title
t_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
tg_draw = ImageDraw.Draw(t_glow)
tg_draw.text((t_x, t_y), title_text, font=f_title, fill=(56, 189, 248, 40))
img = Image.alpha_composite(img, t_glow)
draw = ImageDraw.Draw(img)

# Crisp white title
draw.text((t_x, t_y), title_text, font=f_title, fill=(255, 255, 255))

# 6. Core Element 2: One-line Value Prop (High contrast, centered, easily readable on mobile)
vp_text = "Turn EU Cyber Resilience Act compliance into routine engineering."
vp_box = f_value_prop.getbbox(vp_text)
vp_w = vp_box[2] - vp_box[0]
vp_x = (WIDTH - vp_w) // 2
vp_y = 275

draw.text((vp_x, vp_y), vp_text, font=f_value_prop, fill=(226, 232, 240))

# Horizontal dividing accent line
line_y = 350
draw.line([(WIDTH // 2 - 240, line_y), (WIDTH // 2 + 240, line_y)], fill=(30, 58, 95, 220), width=2)
draw.line([(WIDTH // 2 - 60, line_y), (WIDTH // 2 + 60, line_y)], fill=(56, 189, 248, 240), width=2)

# 7. Core Element 3: Badges / Compatibility Marks
# 4 Prominent High-Contrast Cards for:
# - Packablock
# - Eclipse ORC
# - Cursor
# - Claude Code

badges = [
    {
        "name": "Packablock",
        "role": "Supply Chain Policy",
        "color": (249, 115, 22),       # Orange
        "icon_type": "packablock",
    },
    {
        "name": "Eclipse ORC",
        "role": "Open Regulatory",
        "color": (14, 165, 233),       # Cyan / Blue
        "icon_type": "eclipse",
    },
    {
        "name": "Cursor",
        "role": "IDE Rules Ready",
        "color": (168, 85, 247),       # Purple
        "icon_type": "cursor",
    },
    {
        "name": "Claude Code",
        "role": "Agent-Agnostic",
        "color": (217, 119, 6),        # Amber
        "icon_type": "claude",
    },
]

card_w = 260
card_h = 110
card_gap = 20
total_w = len(badges) * card_w + (len(badges) - 1) * card_gap
start_x = (WIDTH - total_w) // 2
card_y = 400

for i, b in enumerate(badges):
    cx = start_x + i * (card_w + card_gap)
    cy = card_y
    col = b["color"]

    # Outer pill card
    draw.rounded_rectangle(
        [(cx, cy), (cx + card_w, cy + card_h)],
        radius=16,
        fill=(13, 22, 38, 240),
        outline=(30, 58, 95, 220),
        width=2,
    )

    # Accent top border
    draw.rounded_rectangle(
        [(cx + 20, cy + 2), (cx + card_w - 20, cy + 4)],
        radius=2,
        fill=col,
    )

    # Custom Vector Icon / Badge Mark (42x42 box)
    ix = cx + 22
    iy = cy + 28
    iw = 44
    ih = 44

    # Icon container with soft tinted background
    draw.rounded_rectangle(
        [(ix, iy), (ix + iw, iy + ih)],
        radius=10,
        fill=(col[0] // 4, col[1] // 4, col[2] // 4, 255),
        outline=col,
        width=2,
    )

    # Render distinct vector glyph inside container in bright crisp white/tint
    glyph_col = (255, 255, 255, 255)
    if b["icon_type"] == "packablock":
        # Packablock barbell / interconnected blocks
        center_x = ix + iw // 2
        draw.line([(center_x, iy + 9), (center_x, iy + ih - 9)], fill=glyph_col, width=3)
        draw.rounded_rectangle([(center_x - 8, iy + 7), (center_x + 8, iy + 17)], radius=3, fill=col, outline=glyph_col, width=1)
        draw.rounded_rectangle([(center_x - 8, iy + ih - 17), (center_x + 8, iy + ih - 7)], radius=3, fill=col, outline=glyph_col, width=1)

    elif b["icon_type"] == "eclipse":
        # Eclipse crescent / orbit
        center_x, center_y = ix + iw // 2, iy + ih // 2
        draw.ellipse([(center_x - 13, center_y - 13), (center_x + 13, center_y + 13)], outline=glyph_col, width=3)
        draw.ellipse([(center_x - 6, center_y - 6), (center_x + 6, center_y + 6)], fill=col, outline=glyph_col, width=1)

    elif b["icon_type"] == "cursor":
        # Cursor arrow pointer
        pt_x, pt_y = ix + 13, iy + 10
        draw.polygon(
            [(pt_x, pt_y), (pt_x + 18, pt_y + 12), (pt_x + 10, pt_y + 14), (pt_x + 14, pt_y + 24), (pt_x + 9, pt_y + 26), (pt_x + 5, pt_y + 16), (pt_x, pt_y + 19)],
            fill=col,
            outline=glyph_col,
        )

    elif b["icon_type"] == "claude":
        # Claude star / spark burst
        center_x, center_y = ix + iw // 2, iy + ih // 2
        for angle_deg in [0, 45, 90, 135]:
            rad = 13 if angle_deg % 90 == 0 else 9
            import math
            rad_angle = math.radians(angle_deg)
            dx = int(rad * math.cos(rad_angle))
            dy = int(rad * math.sin(rad_angle))
            draw.line([(center_x - dx, center_y - dy), (center_x + dx, center_y + dy)], fill=glyph_col, width=3)

    # Badge Text
    tx_text = ix + iw + 16
    draw.text((tx_text, cy + 30), b["name"], font=f_badge_title, fill=(255, 255, 255))
    draw.text((tx_text, cy + 58), b["role"], font=f_badge_sub, fill=(148, 163, 184))

# 8. Clean Bottom Footer
footer_font = ImageFont.truetype(mono_bold, 15)
foot_text = "github.com/aaronbronow/cra-readiness-skill"
fb = footer_font.getbbox(foot_text)
fb_w = fb[2] - fb[0]
draw.text(((WIDTH - fb_w) // 2, 570), foot_text, font=footer_font, fill=(56, 189, 248, 190))

# Save output
out_png = "docs/assets/social-preview.png"
img.convert("RGB").save(out_png, "PNG", optimize=True)
print(f"Generated simplified social card at {out_png} ({WIDTH}x{HEIGHT})")
