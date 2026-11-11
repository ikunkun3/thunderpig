# -*- coding: utf-8 -*-
"""生成 ThunderPig 的图标：紫底圆角 + 粉猪脸 + 右上角闪电。

以前那版模糊的原因（记下来，别再犯）：
  1. 只在 1024 上画一次，然后 LANCZOS 缩到 16/20/24/32。闪电的深色描边在
     1024 时只有 22px 宽，缩到 40 就剩 0.86px —— 抗锯齿把它摊成一层灰雾，
     整个图标看着就是糊的。**细节必须随尺寸重画，不能靠缩。**
  2. 闪电画到了圆角外面（x 到 0.969），右上角是透明的，闪电等于浮在空中。
     现在所有元素都按圆角矩形裁剪一遍。
  3. 小尺寸用渐变会出色带。<= 40 一律用纯色。

做法：每个尺寸按自己的「细节档」在 4 倍超采样画布上重画，再整数倍缩回去。
输出：ThunderPig.ico（9 档）+ ThunderPig-64.png + _icon_preview.png
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

BG_FLAT = (109, 40, 217)      # #6d28d9 小尺寸用纯色
BG_TOP = (139, 92, 246)       # #8b5cf6
BG_BOTTOM = (76, 29, 149)     # #4c1d95
PINK = (253, 220, 235)        # 猪脸
PINK_EDGE = (247, 178, 208)   # 耳朵
PINK_DEEP = (239, 141, 186)   # 鼻子
DARK = (42, 14, 82)           # 五官 / 闪电描边
BOLT = (253, 224, 71)         # #fde047

# ---- 归一化坐标（都按 0..1，乘尺寸即得像素）----
FACE_CX, FACE_CY, FACE_R = 0.462, 0.620, 0.298
EYE_DX, EYE_CY, EYE_R = 0.124, 0.566, 0.043
NOSE_CY, NOSE_RX, NOSE_RY = 0.734, 0.146, 0.100
NOSTRIL_DX, NOSTRIL_RX, NOSTRIL_RY = 0.066, 0.023, 0.047

EAR_L = [(0.218, 0.418), (0.180, 0.290), (0.330, 0.352)]
EAR_R = [(0.706, 0.418), (0.744, 0.290), (0.594, 0.352)]

# 闪电往内收了一点，整个落在圆角里面
BOLT_OUT = [(0.635, 0.105), (0.885, 0.105), (0.775, 0.265), (0.895, 0.265),
            (0.640, 0.452), (0.712, 0.278), (0.628, 0.278)]
BOLT_IN = [(0.654, 0.128), (0.845, 0.128), (0.742, 0.265), (0.850, 0.265),
           (0.674, 0.392), (0.740, 0.278), (0.656, 0.278)]

# 16px 上闪电只剩 5 个像素，画出来是噪点，这一档不放闪电
BOLT_MIN = 20

# 小尺寸（<= 24）单独一套几何：把脸放大到几乎撑满，眼睛变成小方点，
# 鼻子变成一条横杠。16px 时按 0.298 的半径算，脸只有 9px 宽，
# 五官全挤在一起就是一团粉色 —— 必须换比例，不能等比缩。
SMALL_FACE_CX, SMALL_FACE_CY, SMALL_FACE_R = 0.500, 0.545, 0.395


def _px(pts, s):
    return [(x * s, y * s) for x, y in pts]


def _gradient_bg(s):
    g = Image.new("RGB", (1, s))
    p = g.load()
    for y in range(s):
        t = y / max(1, s - 1)
        p[0, y] = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
    return g.resize((s, s), Image.BILINEAR).convert("RGBA")


def draw_pixel_icon(size):
    """16 / 20 / 24 用像素级画法：直接在目标尺寸上落像素，不做抗锯齿。

    这几个尺寸上一个像素就是一根线，任何抗锯齿都会变成一层灰雾 ——
    用户说的「糊」主要就是这里。宁可像素硬一点，也不要糊。
    几何也换一套（SMALL_*）：脸撑满、五官放大、不放耳朵和闪电。
    """
    s = size
    img = Image.new("RGBA", (s, s), BG_FLAT + (255,))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1],
                                           radius=max(2, int(s * 0.22)), fill=255)
    img.putalpha(mask)
    d = ImageDraw.Draw(img)

    cx, cy, r = SMALL_FACE_CX * s, SMALL_FACE_CY * s, SMALL_FACE_R * s

    # 耳朵：>= 24 才画得出形状，16/20 上只有两个像素点，纯属添乱
    if s >= 24:
        for sign in (-1, 1):
            outer_x = cx + sign * r * 0.86
            tip_x = cx + sign * r * 0.98
            base_y = cy - r * 0.55
            d.polygon([(outer_x, base_y), (tip_x, base_y - r * 0.42),
                       (cx + sign * r * 0.38, cy - r * 0.80)], fill=PINK_EDGE)

    d.ellipse([round(cx - r), round(cy - r), round(cx + r), round(cy + r)], fill=PINK)

    # 眼睛：实心方块，16px 时 2×2，20px 时 3×3
    ew = max(1, round(s * 0.115))
    eh = max(1, round(s * 0.135))
    ey = round(s * 0.475)
    for sign in (-1, 1):
        ex = round(cx + sign * s * 0.155)
        d.rectangle([ex - ew // 2, ey - eh // 2,
                     ex - ew // 2 + ew - 1, ey - eh // 2 + eh - 1], fill=DARK)

    # 鼻子：粉色圆角块 + 两个深色鼻孔（<=16 时鼻孔并成一条横线）
    nw = max(3, round(s * 0.30))
    nh = max(3, round(s * 0.185))
    ny = round(s * 0.665)
    d.rounded_rectangle([cx - nw // 2, ny - nh // 2, cx - nw // 2 + nw - 1, ny - nh // 2 + nh - 1],
                        radius=max(1, nh // 3), fill=PINK_DEEP)
    if s >= 20:
        dw = max(1, round(s * 0.055))
        dh = max(1, round(s * 0.075))
        for sign in (-1, 1):
            nx = round(cx + sign * s * 0.072)
            d.rectangle([nx - dw // 2, ny - dh // 2, nx - dw // 2 + dw - 1,
                         ny - dh // 2 + dh - 1], fill=DARK)
    else:
        bar = max(2, round(s * 0.16))
        d.rectangle([round(cx - bar / 2), ny, round(cx - bar / 2) + bar - 1, ny], fill=DARK)

    return img


def draw_icon(size):
    """按目标像素尺寸重画一遍（>= 32 用 4 倍超采样，更小的走像素画法）。"""
    if size <= 24:
        return draw_pixel_icon(size)

    ss = 4
    s = size * ss
    level = 0 if size >= 128 else (1 if size >= 48 else 2)

    # 背景
    if level <= 1:
        canvas = _gradient_bg(s)
    else:
        canvas = Image.new("RGBA", (s, s), BG_FLAT + (255,))

    # 圆角遮罩：画完所有元素后整体裁一次，确保没有东西跑出圆角
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1],
                                           radius=int(s * 0.225), fill=255)
    canvas.putalpha(mask)
    body = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)

    # 耳朵（只有 >= 32 会走到这里，再小就走 draw_pixel_icon 了）
    d.polygon(_px(EAR_L, s), fill=PINK_EDGE)
    d.polygon(_px(EAR_R, s), fill=PINK_EDGE)

    # 脸
    r = FACE_R * s
    cx, cy = FACE_CX * s, FACE_CY * s
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINK)

    # 眼睛：>= 48 画圆，32/40 画方块（圆在 8~10px 上会被抗锯齿抹成灰点）
    er = EYE_R * s
    for sign in (-1, 1):
        ex = (FACE_CX + sign * EYE_DX) * s
        ey = EYE_CY * s
        if size >= 48:
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=DARK)
        else:
            k = max(1, round(er * 0.92))
            d.rectangle([round(ex - k), round(ey - k), round(ex + k), round(ey + k)],
                        fill=DARK)

    # 鼻子
    ncy = NOSE_CY * s
    nrx, nry = NOSE_RX * s, NOSE_RY * s
    d.ellipse([cx - nrx, ncy - nry, cx + nrx, ncy + nry], fill=PINK_DEEP)
    for sign in (-1, 1):
        nx = (FACE_CX + sign * NOSTRIL_DX) * s
        rx, ry = NOSTRIL_RX * s, NOSTRIL_RY * s
        d.ellipse([nx - rx, ncy - ry, nx + rx, ncy + ry], fill=DARK)

    # 闪电
    d.polygon(_px(BOLT_OUT, s), fill=DARK)
    if size >= 40:
        d.polygon(_px(BOLT_IN, s), fill=BOLT)
    else:
        # 32px：描边占的比例太大，把黄色收一点，别被吃掉
        inner = [(x + (0.5 - x) * 0.10, y + (0.5 - y) * 0.10)
                 for x, y in BOLT_OUT]
        d.polygon(_px(inner, s), fill=BOLT)

    canvas.alpha_composite(body)
    # 必须用预乘 alpha（RGBa）再缩放。直接缩 RGBA 会把透明的 (0,0,0,0)
    # 当成黑色混进边缘像素，四个圆角就变成一块块黑角。
    return canvas.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")


def write_ico(path, frames):
    """自己拼 ICO 文件，一档一张图。

    不能用 `frames[256].save(path, sizes=[...])` —— Pillow 会拿那**一张**图
    反复缩出其它档，于是 16/20/24/32 全是从 256 硬缩下来的抗锯齿灰边，
    Windows 任务栏正好挑 32 那一档，看起来就永远是糊的。
    ICO 格式很简单：6 字节头 + 每档 16 字节目录 + 各档 PNG 原样拼接。
    """
    import io
    import struct

    blobs = []
    for size, im in frames:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        blobs.append((size, buf.getvalue()))

    head = struct.pack("<HHH", 0, 1, len(blobs))
    offset = 6 + 16 * len(blobs)
    entries = b""
    data = b""
    for size, blob in blobs:
        # 宽高各 1 字节，256 写 0
        wh = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", wh, wh, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
        data += blob

    with open(path, "wb") as f:
        f.write(head + entries + data)


def main():
    sizes = [256, 128, 64, 48, 40, 32, 24, 20, 16]
    frames = {s: draw_icon(s) for s in sizes}

    ico = os.path.join(HERE, "ThunderPig.ico")
    write_ico(ico, [(s, frames[s]) for s in sizes])
    print("ico:", os.path.basename(ico), os.path.getsize(ico), "bytes")

    png = os.path.join(HERE, "ThunderPig-64.png")
    frames[64].save(png)
    print("png:", os.path.basename(png), os.path.getsize(png), "bytes")

    frames[256].save(os.path.join(HERE, "_icon_512.png"))

    # 预览：上排按真实像素（放大 1:1 会太小，这里 1:1 摆，最左边单独放 256 大图）
    gut = 18
    big = 256
    total_w = gut + big + gut + sum(s + gut for s in sizes[1:])
    total_h = gut * 2 + big
    prev = Image.new("RGBA", (total_w, total_h), (246, 246, 250, 255))
    prev.paste(frames[256], (gut, gut), frames[256])
    x = gut + big + gut
    for s in sizes[1:]:
        prev.paste(frames[s], (x, gut + (big - s) // 2), frames[s])
        x += s + gut
    prev.save(os.path.join(HERE, "_icon_preview.png"))
    print("preview:", prev.size)

    # 真实尺寸 1:1 条带，用来判断 16/20/24 到底糊不糊
    strip = Image.new("RGBA", (sum(sizes[1:]) + 12 * len(sizes), 64), (246, 246, 250, 255))
    x = 12
    for s in sizes[1:]:
        strip.paste(frames[s], (x, 12), frames[s])
        x += s + 12
    strip.save(os.path.join(HERE, "_icon_strip.png"))
    print("strip:", strip.size)


if __name__ == "__main__":
    main()
