"""
Asset Generator for Audify
Generates high-resolution application icons (PNG and multi-size ICO)
with a modern dark theme and electric purple/cyan glowing audio visualizer motif.
"""

import os
from PIL import Image, ImageDraw, ImageFilter


def generate_icon(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background rounded rectangle with sleek dark gradient / glass styling
    # Outer subtle glow
    glow_box = [20, 20, size - 20, size - 20]
    draw.rounded_rectangle(glow_box, radius=110, fill=(24, 24, 38, 255), outline=(124, 58, 237, 200), width=6)

    # Inner subtle highlight gradient
    inner_box = [30, 30, size - 30, size - 30]
    draw.rounded_rectangle(inner_box, radius=100, fill=(15, 15, 26, 255), outline=(99, 102, 241, 100), width=3)

    # 2. Draw modern stylized audio soundwave bars in the center
    # Symmetrical audio visualizer bars: heights and colors
    bar_heights = [70, 130, 200, 280, 360, 280, 200, 130, 70]
    num_bars = len(bar_heights)
    bar_width = 24
    spacing = 18
    total_width = num_bars * bar_width + (num_bars - 1) * spacing
    start_x = (size - total_width) // 2
    center_y = size // 2

    # Color palette: electric purple (124, 58, 237) to vibrant cyan/blue (56, 189, 248)
    for i, h in enumerate(bar_heights):
        x0 = start_x + i * (bar_width + spacing)
        x1 = x0 + bar_width
        y0 = center_y - (h // 2)
        y1 = center_y + (h // 2)

        # Gradient interpolation
        ratio = i / (num_bars - 1)
        r = int(124 * (1 - ratio) + 56 * ratio)
        g = int(58 * (1 - ratio) + 189 * ratio)
        b = int(237 * (1 - ratio) + 248 * ratio)

        # Draw glow
        glow_pad = 6
        draw.rounded_rectangle(
            [x0 - glow_pad, y0 - glow_pad, x1 + glow_pad, y1 + glow_pad],
            radius=bar_width // 2 + glow_pad,
            fill=(r, g, b, 60)
        )
        # Draw solid bar
        draw.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=bar_width // 2,
            fill=(r, g, b, 255)
        )

    # 3. Add a glowing recording accent dot at the top right
    dot_center = (size - 90, 90)
    dot_r = 16
    draw.ellipse(
        [dot_center[0] - dot_r - 8, dot_center[1] - dot_r - 8,
         dot_center[0] + dot_r + 8, dot_center[1] + dot_r + 8],
        fill=(239, 68, 68, 80)
    )
    draw.ellipse(
        [dot_center[0] - dot_r, dot_center[1] - dot_r,
         dot_center[0] + dot_r, dot_center[1] + dot_r],
        fill=(239, 68, 68, 255)
    )

    # Save PNG
    png_path = os.path.join(output_dir, "icon.png")
    img.save(png_path, "PNG")
    print(f"Generated {png_path}")

    # Generate multi-size ICO
    ico_path = os.path.join(output_dir, "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Generated {ico_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(current_dir, "assets")
    generate_icon(assets_dir)
