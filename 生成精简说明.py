# -*- coding: utf-8 -*-
"""生成《PTA 写代码 · 精简版》docx —— 两页，只讲用处、用法、怎么排错。

不写性能数字、不写字符数、不写百分比 —— 使用者不关心那些。
完整版（13 页）仍由 生成使用说明文档.py 产出，本脚本不动它。
"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")
OUT = os.path.join(HERE, "PTA写代码使用说明-精简版.docx")

PURPLE = RGBColor(0x5B, 0x21, 0xB6)
GREY = RGBColor(0x55, 0x5F, 0x6D)
DARK = RGBColor(0x11, 0x18, 0x27)


def set_cn(run, name="微软雅黑"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def shade(par, hexcolor):
    pPr = par._p.get_or_add_pPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexcolor)
    pPr.append(sh)


def border_left(par, hexcolor, sz=18):
    pPr = par._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(sz))
    left.set(qn("w:space"), "6")
    left.set(qn("w:color"), hexcolor)
    bd.append(left)
    pPr.append(bd)


def para(doc, text="", size=10, color=None, bold=False, space_before=0,
         space_after=4, align=None, indent=0, line=1.35):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        if color is not None:
            r.font.color.rgb = color
        set_cn(r)
    return p


def rich(doc, parts, size=10, space_before=0, space_after=4, indent=0, line=1.35):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.left_indent = Cm(indent)
    for text, opt in parts:
        r = p.add_run(text)
        r.font.size = Pt(opt.get("size", size))
        r.bold = opt.get("b", False)
        if opt.get("color") is not None:
            r.font.color.rgb = opt["color"]
        set_cn(r, "Consolas" if opt.get("mono") else "微软雅黑")
    return p


def h1(doc, num, text, newpage=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0 if newpage else 12)
    pf.space_after = Pt(5)
    pf.keep_with_next = True
    if newpage:
        pf.page_break_before = True
    r = p.add_run("%s  " % num)
    r.font.size = Pt(14)
    r.bold = True
    r.font.color.rgb = PURPLE
    set_cn(r)
    r2 = p.add_run(text)
    r2.font.size = Pt(14)
    r2.bold = True
    r2.font.color.rgb = DARK
    set_cn(r2)
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "6")
    bot.set(qn("w:space"), "3")
    bot.set(qn("w:color"), "DDD6FE")
    bd.append(bot)
    pPr.append(bd)
    return p


def tip(doc, kind, title, body):
    colors = {"ok": ("E8F7EE", "0F7B42", "046C3B"),
              "warn": ("FDF3E7", "B45309", "92400E"),
              "bad": ("FDECEA", "B42318", "B42318"),
              "info": ("F1EDFE", "6D28D9", "5B21B6")}
    fill, bar, tc = colors[kind]
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(5)
    pf.space_after = Pt(6)
    pf.left_indent = Cm(0.12)
    pf.line_spacing = 1.35
    shade(p, fill)
    border_left(p, bar)
    r = p.add_run(title)
    r.font.size = Pt(10)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(tc)
    set_cn(r)
    r2 = p.add_run(body)
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = RGBColor(0x33, 0x3D, 0x4A)
    set_cn(r2)
    return p


def figure(doc, fname, caption, width=9.4):
    path = os.path.join(SHOTS, fname)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    c.paragraph_format.keep_together = True
    r = c.add_run(caption)
    r.font.size = Pt(8.5)
    r.font.color.rgb = GREY
    set_cn(r)


def table(doc, rows, widths=None):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, val in enumerate(row):
            cell = cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(str(val))
            r.font.size = Pt(8.5) if ri else Pt(9)
            set_cn(r)
            if ri == 0:
                r.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                shade(p, "5B21B6")
            elif ri % 2 == 0:
                shade(p, "F7F5FF")
    for ri, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if ri == 0:
            trPr.append(OxmlElement("w:tblHeader"))
    if widths:
        for ci, w in enumerate(widths):
            for row in t.rows:
                row.cells[ci].width = Cm(w)
    return t


def bullet(doc, lead, rest):
    rich(doc, [(u"·  ", {"b": True, "color": PURPLE}),
               (lead, {"b": True}),
               (rest, {})], size=9.5, indent=0.35, space_after=3)


# ===================== 文档 =====================
doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.0)
sec.right_margin = Cm(2.0)
sec.top_margin = Cm(1.8)
sec.bottom_margin = Cm(1.6)

style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.font.size = Pt(10)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

# ---------- 标题 ----------
para(doc, "PTA 写代码", size=20, color=PURPLE, bold=True, space_after=2)
para(doc, "PTA 的代码框不让粘贴。这个小工具替你一个字一个字敲进去 —— 代码还是你的，提交也还是你点。",
     size=9.5, color=GREY, space_after=6)

# ---------- 置顶警示（最显眼的一条） ----------
warn = doc.add_paragraph()
wpf = warn.paragraph_format
wpf.space_before = Pt(2)
wpf.space_after = Pt(10)
wpf.left_indent = Cm(0.1)
wpf.line_spacing = 1.4
shade(warn, "FDECEA")
border_left(warn, "B42318", sz=36)

_r = warn.add_run("注意事项（先看这条）\n")
_r.font.size = Pt(11)
_r.bold = True
_r.font.color.rgb = RGBColor(0xB4, 0x23, 0x18)
set_cn(_r)

_r = warn.add_run("这不是自动搜题、自动作答软件。")
_r.font.size = Pt(11)
_r.bold = True
_r.font.color.rgb = RGBColor(0x91, 0x1B, 0x13)
set_cn(_r)

_r = warn.add_run("它不搜题、不查答案、不认识题目、也不知道答案对不对 —— 它只会一件小事："
                  "把你复制给它的那段文字，一个字符一个字符地打到当前光标所在的输入框里，"
                  "跟有人坐在那里用键盘打出来一模一样。\n"
                  "答案从哪来、写什么内容、对不对，全是你自己的事。它只负责「搬运」，不负责「想」。")
_r.font.size = Pt(9.5)
_r.font.color.rgb = RGBColor(0x5A, 0x1A, 0x14)
set_cn(_r)

# ---------- 1 ----------
h1(doc, "1", "它是干什么用的")

para(doc, "你在自己电脑上把代码写好了（Word、记事本、VS Code 哪儿都行），要交到 PTA 的编程题里。"
          "问题是在 PTA 的代码框里按 Ctrl+V 没反应 —— 页面把粘贴拦了。", space_after=5)

para(doc, "这个工具干的事只有一件：把那段代码一个字符一个字符地「敲」进那个代码框 —— "
          "用的是模拟键盘输入，效果跟你自己用手打完全一样。所以它绕得过去："
          "页面拦的是「粘贴」这个动作，不是「打字」。", space_after=5)

bullet(doc, "它只打字，不思考。", "不搜题、不查答案、不判断对错 —— 代码内容由你决定。")
bullet(doc, "不用装什么、不用登录、不用联网。", "代码不出你的电脑。")
bullet(doc, "不点保存、不点测试、不点提交。", "什么时候交、交哪一题，全是你自己点。")
bullet(doc, "写错了它也不知道。", "它只负责搬运，对错得你自己看一眼。")

figure(doc, "02_面板弹出.png", "工具就长这样：中间那块粘代码，底部一行会告诉你成没成。", 7.2)

# ---------- 2 ----------
h1(doc, "2", "怎么用（四步）")

rich(doc, [(u"① ", {"b": True, "color": PURPLE}),
           ("装一次。", {"b": True}),
           ("打开 ", {}), ("安装书签.html", {"mono": True}),
           ("，按住那个紫色按钮拖到浏览器的书签栏里。书签栏没显示就按 ", {}),
           ("Ctrl+Shift+B", {"mono": True}), (" 打开。", {})], indent=0.3, space_after=5)

rich(doc, [(u"② ", {"b": True, "color": PURPLE}),
           ("打开一道编程题。", {"b": True}),
           ("左边选「函数题」，点开任意一题。判断标准很简单：页面右半边有个黑底的代码框。"
            "选择题、填空题没这个框，工具也用不上。", {})], indent=0.3, space_after=5)

rich(doc, [(u"③ ", {"b": True, "color": PURPLE}),
           ("点书签，粘代码。", {"b": True}),
           ("点一下书签栏里那个书签，屏幕上会浮出一个面板。把代码粘进面板里那个大框"
            "（注意是面板的框，不是 PTA 的框），然后点「写代码」，或者直接按 ", {}),
           ("Ctrl+Enter", {"mono": True}), ("。", {})], indent=0.3, space_after=5)

rich(doc, [(u"④ ", {"b": True, "color": PURPLE}),
           ("看结果，自己交。", {"b": True}),
           ("底部那行变绿就说明写进去了，再点一下面板右上角的 × 关掉它，"
            "然后自己点「测试用例」看通不通，自己点「提交本题作答」。", {})], indent=0.3, space_after=5)

tip(doc, "bad", "再强调一次：提交永远是你自己点。",
    "工具里一行「提交」的代码都没有，它连提交按钮在哪儿都不知道。它打进去的每一个字，"
    "都是你给它的那一段。")

# ---------- 3 ----------
h1(doc, "3", "三种方式，挑一个就行")

para(doc, "写进去的效果三种完全一样，区别只在「怎么把面板叫出来」。装哪个看你的情况：", space_after=4)

table(doc, [
    ["看情况", "书签（推荐）", "exe", "油猴脚本"],
    ["适合谁", "大多数人", "机房不让装扩展", "已经装了 Tampermonkey"],
    ["要装什么", "拖个书签，不装扩展", "下载一个文件，双击就用", "装扩展，再装脚本"],
    ["怎么叫出来", "点一下书签", "打开窗口，切回浏览器", "打开页面它自己出来"],
    ["什么时候用它", "默认就用这个", "书签拖不了的时候", "已经装过油猴了顺手"],
], widths=[3.2, 5.0, 4.4, 4.4])

para(doc, "三个可以同时装，不冲突。不建议都装 —— 选一个用熟就够了。",
     size=9.5, color=GREY, space_before=4)

# ---------- 4 ----------
h1(doc, "4", "出问题看这里")

table(doc, [
    ["你看到的", "怎么办"],
    ["点书签没反应", "书签网址没粘全。删掉重新装一次，确认装的时候是整个拖过去，没被截断"],
    ["红字「没找到代码框」", "当前页面没有答题区。切到左边「函数题」标签，点开一道题，再点书签"],
    ["弹出「不要粘贴」的提示", "你粘到 PTA 的框里了。应该粘进面板里的那个大框"],
    ["提示成功，但框还是空的", "刷新页面重来一次。反复这样就用 exe 那个版本"],
    ["缩进歪了、多出空格", "用 exe 版，把「PTA 模式」的勾去掉，让它按原样敲"],
    ["敲到一半停了", "你碰了键盘或鼠标。重来一次，等它敲完再动"],
], widths=[5.0, 12.0])

# ---------- 5 ----------
h1(doc, "5", "几句实话")

bullet(doc, "exe 上有个「PTA 模式」的勾，", "默认勾着，别动它。它让工具利用网页自己补的缩进，少敲几下。"
                                          "换了不是 PTA 的地方（比如记事本）才需要去掉。")
bullet(doc, "同一道题可以反复写。", "写坏了不怕，重新粘一遍再点「写代码」，它会整个覆盖掉。")
bullet(doc, "面板挡住了题目？", "按住面板顶部的标题栏拖动它，或者直接点 × 关掉，看完题再点书签叫回来。")

p = para(doc, "— 完 —　截图来自虚构的演示页面，不含任何真实学校、教师或账号身份信息。",
         size=8.5, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10)

doc.save(OUT)
print("saved:", OUT, os.path.getsize(OUT), "bytes")
