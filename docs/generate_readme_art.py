"""Render the branded animated cover used by README.md.

Run with: python docs/generate_readme_art.py
Requires Pillow (pip install pillow).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/assets/gesture-racing-cover.gif"
W, H = 1440, 760
BG = (8, 10, 13)
WHITE = (239, 244, 238)
MUTED = (145, 160, 160)
LIME = (198, 255, 48)
CYAN = (58, 232, 218)
PINK = (255, 76, 197)
BLUE = (111, 130, 255)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def line(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], color, width=2):
    draw.line(points, fill=color, width=width, joint="curve")


def build_background() -> Image.Image:
    image = Image.new("RGB", (W, H))
    pixels = image.load()
    for y in range(H):
        for x in range(W):
            nx, ny = x / W, y / H
            bloom = max(0, 1 - math.sqrt(((nx - 0.72) / 0.62) ** 2 + ((ny - 0.42) / 0.95) ** 2))
            pixels[x, y] = (8, int(10 + bloom * 12), int(13 + bloom * 13))
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(24, W, 32):
        draw.line((x, 0, x, H), fill=(22, 29, 34, 52))
    for y in range(24, H, 32):
        draw.line((0, y, W, y), fill=(22, 29, 34, 52))
    return image


def draw_hand(draw: ImageDraw.ImageDraw, phase: float) -> None:
    wobble = math.sin(phase) * 3
    points = [
        (852, 496), (841, 455), (824, 418), (811, 387), (815, 377), (825, 380),
        (846, 414), (830, 355), (833, 345), (843, 346), (858, 405),
        (858, 337), (862, 327), (872, 328), (872, 406),
        (888, 350), (895, 342), (904, 346), (892, 423),
        (916, 389), (925, 387), (932, 394), (917, 440), (900, 482), (888, 514), (852, 496),
    ]
    points = [(x + (wobble if i % 3 == 0 else 0), y) for i, (x, y) in enumerate(points)]
    chains = [
        points[0:7], points[6:11], points[10:15], points[14:19], points[18:23], points[22:26]
    ]
    for chain in chains:
        line(draw, chain, (*LIME, 220), 3)
    line(draw, [points[i] for i in (6, 10, 14, 18, 22)], (*CYAN, 155), 2)
    joints = (0, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19, 21, 22, 23, 24, 25)
    for index in joints:
        x, y = points[index]
        radius = 5 if index in (6, 10, 14, 18, 22) else 3
        draw.ellipse((x - radius - 4, y - radius - 4, x + radius + 4, y + radius + 4), fill=(*LIME, 36))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*WHITE, 235))


def draw_wheel(draw: ImageDraw.ImageDraw, angle: float, bold, mono) -> None:
    cx, cy, radius = 1214, 432, 70
    # Layered bevel and offset shadow give the rim visible depth at README size.
    draw.ellipse((cx - 80, cy - 70, cx + 80, cy + 96), fill=(4, 7, 12, 220), outline=(*BLUE, 120), width=3)
    draw.ellipse((cx - 72, cy - 72, cx + 72, cy + 72), outline=(30, 41, 48, 255), width=22)
    draw.ellipse((cx - 69, cy - 69, cx + 69, cy + 69), outline=(*LIME, 225), width=12)
    draw.ellipse((cx - 60, cy - 60, cx + 60, cy + 60), outline=(24, 34, 38, 255), width=4)
    draw.arc((cx - 70, cy - 70, cx + 70, cy + 70), 198, 300, fill=(242, 255, 201, 230), width=3)
    draw.arc((cx - 72, cy - 72, cx + 72, cy + 72), 18, 130, fill=(*CYAN, 210), width=3)
    for index in range(3):
        radians = math.radians(angle + 90 + index * 120)
        x = cx + math.cos(radians) * (radius - 13)
        y = cy + math.sin(radians) * (radius - 13)
        draw.line((cx + 3, cy + 4, x + 3, y + 4), fill=(4, 8, 13, 230), width=11)
        draw.line((cx, cy, x, y), fill=(54, 72, 75, 255), width=9)
        draw.line((cx - 1, cy - 2, x - 1, y - 2), fill=(*WHITE, 235), width=4)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=CYAN)
    draw.ellipse((cx - 20, cy - 18, cx + 20, cy + 22), fill=(4, 8, 13, 235), outline=(*PINK, 210), width=2)
    draw.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), fill=(18, 27, 30), outline=(*LIME, 255), width=3)
    draw.text((cx - 7, cy - 9), "G", font=bold, fill=LIME)
    draw.arc((cx - 100, cy - 100, cx + 100, cy + 100), 200, 338, fill=(*PINK, 150), width=2)


def render() -> None:
    fonts = Path("C:/Windows/Fonts")
    title = ImageFont.truetype(str(fonts / "arialbd.ttf"), 102)
    bold = ImageFont.truetype(str(fonts / "bahnschrift.ttf"), 28)
    body = ImageFont.truetype(str(fonts / "segoeui.ttf"), 23)
    mono = ImageFont.truetype(str(fonts / "consola.ttf"), 15)
    small = ImageFont.truetype(str(fonts / "consola.ttf"), 12)
    base = build_background()
    draw = ImageDraw.Draw(base, "RGBA")

    for dx, dy, color in ((0, 0, LIME), (14, 0, CYAN), (0, 14, BLUE), (14, 14, PINK)):
        draw.rounded_rectangle((48 + dx, 43 + dy, 58 + dx, 53 + dy), radius=3, fill=color)
    draw.text((88, 40), "GESTURE / RACING", font=mono, fill=WHITE)
    draw.text((88, 61), "WEBCAM MOTION CONTROL  ·  PROJECT 001", font=small, fill=MUTED)
    draw.text((1188, 48), "SYSTEM STATUS", font=small, fill=MUTED)
    draw.ellipse((1187, 74, 1197, 84), fill=LIME)
    draw.text((1208, 70), "LOCAL VISION", font=mono, fill=WHITE)
    draw.line((48, 104, W - 48, 104), fill=(102, 124, 119, 90))

    draw.text((64, 160), "HUMAN MOTION  /  DIGITAL SPEED", font=mono, fill=LIME)
    draw.text((56, 190), "DRIVE BY", font=title, fill=WHITE)
    draw.text((56, 284), "INSTINCT.", font=title, fill=LIME)
    draw.rounded_rectangle((64, 410, 68, 535), radius=2, fill=CYAN)
    draw.text((88, 409), "Your hands are the controls.", font=body, fill=WHITE)
    draw.text((88, 446), "A webcam turns each gesture into", font=body, fill=MUTED)
    draw.text((88, 480), "input for the game on your device.", font=body, fill=MUTED)

    def pill(x: int, y: int, label: str, color, width: int) -> None:
        draw.rounded_rectangle((x, y, x + width, y + 34), radius=8, fill=(12, 17, 20, 230), outline=(*color, 155))
        draw.ellipse((x + 12, y + 13, x + 20, y + 21), fill=color)
        draw.text((x + 29, y + 9), label, font=small, fill=WHITE)

    pill(64, 570, "21 HAND LANDMARKS", LIME, 190)
    pill(266, 570, "TWO-HAND INPUT", CYAN, 178)
    pill(456, 570, "ON-DEVICE CAMERA", PINK, 186)
    draw.text((64, 667), "NO GAMEPAD  ·  NO TOUCH  ·  JUST MOTION", font=small, fill=(158, 176, 165))

    draw.rounded_rectangle((696, 128, 1380, 672), radius=22, fill=(10, 14, 17, 220), outline=(94, 119, 111, 110), width=1)
    draw.text((728, 151), "LIVE MOTION STUDY", font=mono, fill=WHITE)
    draw.text((1210, 153), "FRAME  /  001", font=small, fill=MUTED)
    draw.line((728, 182, 1348, 182), fill=(95, 119, 112, 75))

    def track_point(t: float, a: float, b: float) -> tuple[float, float]:
        rotation = -0.30
        u, v = a * math.cos(t), b * math.sin(t)
        return (1044 + u * math.cos(rotation) - v * math.sin(rotation),
                405 + u * math.sin(rotation) + v * math.cos(rotation))

    frames = []
    for frame in range(36):
        image = base.copy()
        draw = ImageDraw.Draw(image, "RGBA")
        for index, (a, b, color, width) in enumerate(((302, 147, (111, 130, 255, 60), 1), (279, 123, (58, 232, 218, 82), 1), (254, 104, (198, 255, 48, 140), 2))):
            pts = [track_point(2 * math.pi * step / 220, a, b) for step in range(221)]
            if index == 1:
                pts = [point for step, point in enumerate(pts) if (step // 4) % 2 == 0]
            line(draw, pts, color, width)
        car_x, car_y = track_point(2 * math.pi * frame / 36, 254, 104)
        draw.ellipse((car_x - 24, car_y - 24, car_x + 24, car_y + 24), fill=(*LIME, 25))
        draw.rounded_rectangle((car_x - 14, car_y - 7, car_x + 14, car_y + 7), radius=5, fill=LIME)
        draw.polygon(((car_x + 7, car_y - 6), (car_x + 18, car_y), (car_x + 7, car_y + 6)), fill=CYAN)

        draw.rounded_rectangle((785, 284, 951, 542), radius=13, outline=(*CYAN, 70))
        draw.text((796, 294), "HAND 01  /  TRACKED", font=small, fill=CYAN)
        draw_hand(draw, 2 * math.pi * frame / 36)
        curve = []
        for step in range(60):
            t = step / 59
            x = (1 - t) ** 3 * 936 + 3 * (1 - t) ** 2 * t * 1000 + 3 * (1 - t) * t**2 * 1078 + t**3 * 1137
            y = (1 - t) ** 3 * 424 + 3 * (1 - t) ** 2 * t * 356 + 3 * (1 - t) * t**2 * 394 + t**3 * 432
            curve.append((x, y))
        for step in range(0, 59, 3):
            line(draw, curve[step:step + 2], (*CYAN, 100))
        for offset, color in ((0, LIME), (13, CYAN), (26, PINK)):
            x, y = curve[(frame * 2 + offset) % 59]
            draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(*color, 40))
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(*color, 245))
        draw_wheel(draw, math.sin(2 * math.pi * frame / 36) * 19, bold, mono)

        draw.rounded_rectangle((751, 574, 972, 626), radius=9, fill=(13, 19, 21, 238), outline=(*LIME, 100))
        draw.text((768, 582), "GESTURE DETECTED", font=small, fill=MUTED)
        draw.text((768, 601), "INDEX  →  ACCELERATE", font=mono, fill=LIME)
        draw.rounded_rectangle((1002, 574, 1329, 626), radius=9, fill=(13, 19, 21, 238), outline=(*CYAN, 100))
        draw.text((1020, 582), "INPUT PIPELINE", font=small, fill=MUTED)
        draw.text((1020, 601), "CAMERA  →  GAME", font=mono, fill=CYAN)
        draw.text((1292, 644), "AUTO LOOP", font=small, fill=(134, 155, 149))
        frames.append(image)

    palette = frames[0].convert("P", palette=Image.Palette.ADAPTIVE, colors=160)
    indexed = [frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(OUT, save_all=True, append_images=indexed[1:], duration=85, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    render()
