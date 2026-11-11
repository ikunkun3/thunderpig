# -*- coding: utf-8 -*-
"""生成 ThunderPig 的图标：紫底圆角 + 猪脸 + 右上角闪电。

先在 1024×1024 上画，再用 LANCZOS 缩到各尺寸，保证 16px 也不糊。
输出：ThunderPig.ico（多尺寸）+ _icon_preview.png（验收用）
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024

BG_TOP = (124, 58, 237)      # #7c3aed
BG_BOTTOM = (67, 20, 130)    # 深一档
PINK = (252, 214, 232)       # #fcd6e8 猪脸
PINK_EDGE = (246, 173, 205)  # 耳/鼻的边
PINK_DEEP = (240, 140, 185)  # 鼻子
DARK = (45, 16, 88)          # 五官
BOLT = (253, 224, 71)        # #fde047

# 脸的中心与半径
CX, CY, R = 470, 640, 300


def rounded_gradient():
    grad = Image.new("RGB", (1, S))
    px = grad.load()
    for y in range(S):
        t = y / (S - 1)
        px[0, y] = tuple(
            int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)
        )
    grad = grad.resize((S, S), Image.BILINEAR).convert("RGBA")

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=255
    )
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def draw_ears(img):
    """两只小三角耳，只从脸后面探出一点点，避免和右上角的闪电打架。"""
    d = ImageDraw.Draw(img)
    d.polygon([(CX - 250, CY - 210), (CX - 300, CY - 350), (CX - 140, CY - 285)],
              fill=PINK_EDGE)
    d.polygon([(CX + 250, CY - 210), (CX + 292, CY - 350), (CX + 140, CY - 285)],
              fill=PINK_EDGE)


def draw_face(img):
    d = ImageDraw.Draw(img)
    d.ellipse([CX - R, CY - R, CX + R, CY + R], fill=PINK)

    # 眼睛
    for ex in (-125, 125):
        d.ellipse([CX + ex - 40, CY - 100, CX + ex + 40, CY - 20], fill=DARK)

    # 鼻子
    sw, sh = 290, 200
    sy = CY + 110
    d.ellipse([CX - sw // 2, sy - sh // 2, CX + sw // 2, sy + sh // 2],
              fill=PINK_DEEP)
    for nx in (-66, 66):
        d.ellipse([CX + nx - 22, sy - 46, CX + nx + 22, sy + 46], fill=DARK)


def draw_bolt(img):
    """右上角闪电，整体落在脸的外侧，不挡眼睛。"""
    outer = [(724, 60), (984, 60), (866, 236), (992, 236), (700, 430),
             (772, 250), (686, 250)]
    inner = [(740, 82), (940, 82), (826, 236), (944, 236), (734, 372),
             (800, 250), (710, 250)]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.polygon(outer, fill=DARK)
    ld.polygon(inner, fill=BOLT)
    return Image.alpha_composite(img, layer)


def build():
    img = rounded_gradient()
    draw_ears(img)
    draw_face(img)
    return draw_bolt(img)


def main():
    master = build()
    master.save(os.path.join(HERE, "_icon_1024.png"))

    sizes = [256, 128, 64, 48, 40, 32, 24, 20, 16]
    frames = [master.resize((s, s), Image.LANCZOS) for s in sizes]
    ico = os.path.join(HERE, "ThunderPig.ico")
    frames[0].save(ico, format="ICO", sizes=[(s, s) for s in sizes])
    print("ico:", os.path.basename(ico), os.path.getsize(ico), "bytes")

    # 标题栏里用的小图标（Tk 的 PhotoImage 读不了 .ico，另存一张 PNG）
    png = os.path.join(HERE, "ThunderPig-64.png")
    master.resize((64, 64), Image.LANCZOS).save(png)
    print("png:", os.path.basename(png), os.path.getsize(png), "bytes")

    gut = 16
    total_w = sum(sizes) + gut * (len(sizes) + 1)
    total_h = max(sizes) + gut * 2
    prev = Image.new("RGBA", (total_w, total_h), (245, 245, 250, 255))
    x = gut
    for s, f in zip(sizes, frames):
        prev.paste(f, (x, gut + (max(sizes) - s) // 2), f)
        x += s + gut
    prev.save(os.path.join(HERE, "_icon_preview.png"))
    print("preview:", prev.size)


if __name__ == "__main__":
    main()
