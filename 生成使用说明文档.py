# -*- coding: utf-8 -*-
"""生成《PTA 写代码 · 使用说明》docx（配 9 张演示截图，全部来自虚构演示页）"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")
OUT = os.path.join(HERE, "PTA写代码使用说明.docx")

PURPLE = RGBColor(0x5B, 0x21, 0xB6)
GREY = RGBColor(0x55, 0x5F, 0x6D)
DARK = RGBColor(0x11, 0x18, 0x27)
GREEN = RGBColor(0x04, 0x6C, 0x3B)
RED = RGBColor(0xB4, 0x23, 0x18)
AMBER = RGBColor(0x92, 0x40, 0x0E)


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


def para(doc, text="", size=10.5, color=None, bold=False, space_before=0,
         space_after=6, align=None, indent=0, line=1.55):
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


def rich(doc, parts, size=10.5, space_before=0, space_after=6, indent=0, line=1.55):
    """parts: [(text, {'b':True,'color':RGBColor,'mono':True})]"""
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
        if opt.get("mono"):
            set_cn(r, "Consolas")
        else:
            set_cn(r)
    return p


def h1(doc, num, text, newpage=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(6 if newpage else 20)
    pf.space_after = Pt(8)
    pf.keep_with_next = True
    if newpage:
        pf.page_break_before = True          # 用分页属性，别用空段落或 add_page_break（会多出空白页）
    r = p.add_run("%s  " % num)
    r.font.size = Pt(17)
    r.bold = True
    r.font.color.rgb = PURPLE
    set_cn(r)
    r2 = p.add_run(text)
    r2.font.size = Pt(17)
    r2.bold = True
    r2.font.color.rgb = DARK
    set_cn(r2)
    # 下划细线
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "6")
    bot.set(qn("w:space"), "4")
    bot.set(qn("w:color"), "DDD6FE")
    bd.append(bot)
    pPr.append(bd)
    return p


def h2(doc, text, step=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(14)
    pf.space_after = Pt(5)
    pf.keep_with_next = True
    if step is not None:
        r0 = p.add_run("%s " % step)
        r0.font.size = Pt(12.5)
        r0.bold = True
        r0.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cn(r0)
        # 给序号加底色
        rPr = r0._element.get_or_add_rPr()
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear")
        sh.set(qn("w:color"), "auto")
        sh.set(qn("w:fill"), "7C3AED")
        rPr.append(sh)
        r = p.add_run("  " + text)
    else:
        r = p.add_run(text)
    r.font.size = Pt(12.5)
    r.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x2A, 0x37)
    set_cn(r)
    return p


def tip(doc, kind, title, body):
    """kind: ok / warn / bad / info"""
    colors = {"ok": ("E8F7EE", "0F7B42", "046C3B"),
              "warn": ("FDF3E7", "B45309", "92400E"),
              "bad": ("FDECEA", "B42318", "B42318"),
              "info": ("F1EDFE", "6D28D9", "5B21B6")}
    fill, bar, tc = colors[kind]
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(8)
    pf.left_indent = Cm(0.15)
    pf.line_spacing = 1.5
    shade(p, fill)
    border_left(p, bar)
    r = p.add_run(title)
    r.font.size = Pt(10.5)
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(tc)
    set_cn(r)
    if body:
        r2 = p.add_run("  " + body)
        r2.font.size = Pt(10)
        r2.font.color.rgb = RGBColor(0x33, 0x3D, 0x4A)
        set_cn(r2)
    return p


def code(doc, text, size=9.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(8)
    pf.left_indent = Cm(0.3)
    pf.line_spacing = 1.35
    shade(p, "F6F7F9")
    border_left(p, "D8DCE3", 12)
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        r = p.add_run(ln)
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        set_cn(r, "Consolas")
        if i < len(lines) - 1:
            r.add_break()
    return p


def figure(doc, fname, caption, width=11.9):
    path = os.path.join(SHOTS, fname)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True          # 图和图注永远不分页
    p.add_run().add_picture(path, width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(12)
    c.paragraph_format.keep_together = True
    parts = caption.split("\n")
    for i, seg in enumerate(parts):
        r = c.add_run(seg)
        r.font.size = Pt(9)
        r.font.color.rgb = GREY
        set_cn(r)
        if i < len(parts) - 1:
            r.add_break()


def table(doc, rows, widths=None, head_fill="5B21B6"):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, val in enumerate(row):
            cell = cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(str(val))
            r.font.size = Pt(9) if ri else Pt(9.5)
            set_cn(r)
            if ri == 0:
                r.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                shade(p, head_fill)
            elif ri % 2 == 0:
                shade(p, "F7F5FF")
    # 表头跨页重复 + 单行不被拆成两页（否则会出现上页半个格子、下页空格子的难看效果）
    for ri, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        if ri == 0:
            hdr = OxmlElement("w:tblHeader")
            trPr.append(hdr)
    if widths:
        for ci, w in enumerate(widths):
            for row in t.rows:
                row.cells[ci].width = Cm(w)
    return t


# ===================== 文档 =====================
doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.6)
sec.right_margin = Cm(2.6)
sec.top_margin = Cm(2.3)
sec.bottom_margin = Cm(2.2)

style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

# ---------- 封面 ----------
p = para(doc, "", space_before=28, space_after=0)
p = para(doc, "PTA 写代码", size=32, color=PURPLE, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
p = para(doc, "使用说明", size=24, color=DARK, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
p = para(doc, "—— 把代码敲进 PTA 的代码框，不靠粘贴 ——",
         size=12, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)

tip(doc, "info", "一句话：",
    "PTA 编程题禁掉了粘贴，但没禁「键盘」。这三套工具都是把代码一个字一个字写进代码框，"
    "用的不是剪贴板，所以禁令拦不到。")

para(doc, "", space_after=2)
figure(doc, "01_打开题目.png", "图 1　打开一道函数题\n（本文所有截图都来自一个虚构的演示页，不含任何真实学校与个人信息）", 12.0)

para(doc, "", space_after=2)
rich(doc, [("文档版本 ", {}), ("v1.0", {"mono": True}), ("　·　适用：Chrome / Edge（100 以上）", {})],
     size=9.5, space_before=8, space_after=3)
rich(doc, [("配套文件：", {"b": True}), ("安装书签.html", {"mono": True}),
           ("、", {}), ("书签工具.js", {"mono": True}),
           ("、", {}), ("哇嘞哇嘞大雷猪.exe", {"mono": True}),
           ("、", {}), ("pta-typer.user.js", {"mono": True})], size=9.5, space_after=0)

# ---------- 目录 ----------
p = para(doc, "目录", size=16, color=DARK, bold=True, space_after=10)
p.paragraph_format.page_break_before = True
p.paragraph_format.space_before = Pt(6)
toc = [
    ("1", "先认识 PTA，再认识「PTA 模式 / 普通模式」", "这两个词是全文的地基"),
    ("2", "为什么要这三样东西", ""),
    ("3", "三种方式，选一个", ""),
    ("4", "方案 A：书签（推荐，30 秒装完）", "8 个步骤，配 8 张图"),
    ("5", "面板上每个控件是干什么的", ""),
    ("6", "出问题了怎么查", "10 种常见症状"),
    ("7", "方案 B：exe（不装扩展、不装脚本）", ""),
    ("8", "方案 C：油猴脚本", ""),
    ("9", "它不会做什么 · 原理一句话", ""),
]
for num, title, note in toc:
    parts = [("%s　" % num, {"color": PURPLE, "b": True, "size": 11}),
             (title, {"size": 11})]
    if note:
        parts.append(("　　（%s）" % note, {"color": GREY, "size": 9}))
    rich(doc, parts, space_before=3, space_after=3)

para(doc, "", space_after=8)
tip(doc, "warn", "关于本文的截图：",
    "为了让文档能直接发给任何人，截图全部来自一个专门做的演示页（学校写「示例大学」、"
    "作者写「demo」、网址是 pintia.example.edu）。真实站点上的按钮文字与位置是一致的，"
    "但你的页面里会有你自己的账号和课程名 —— 那部分不会被截图。")

doc.add_page_break()

# ---------- 1 ----------
h1(doc, "1", "先认识 PTA，再认识「PTA 模式 / 普通模式」")

h2(doc, "PTA 是什么")
para(doc, "PTA（Programming Teaching Assistant）是一个在线判题平台，拼题 A，网址是 pintia.cn。"
          "老师在上面建题库、发作业和考试，你在上面写代码、点提交，服务器用一批测试数据跑你的程序，"
          "全过就得分。它的编程题页面长这样：左边是题目描述、输入输出样例和各种限制，"
          "右边是一块黑色的代码编辑框。你在右边写完，点「测试用例」自查，最后点「提交本题作答」。")

para(doc, "它有个特点被很多人踩过：代码框里按 Ctrl+V 没反应。这不是你浏览器坏了 —— "
          "是网页在「粘贴」这个动作上挂了钩子，检测到就把内容丢掉，防止有人从别处整段拷答案。"
          "这份文档里提到的三套工具，都是为了绕开这一个限制而做的（原理见第 9 章）。")

tip(doc, "info", "记一下这两个页面元素：",
    "「测试用例」＝用题目给的样例数据自查，随便点，不计分；「提交本题作答」＝正式交卷，会计分、会占次数。"
    "工具只往代码框里写字，这两个按钮一个都不碰。")

h2(doc, "「普通模式」和「PTA 模式」指的是什么")
para(doc, "这是 exe 版（方案 B）控制条上的一个勾选框，决定「敲代码的时候，怎么处理每一行开头的空格」。"
          "两个模式写进去的代码是一模一样的，区别只在过程省不省事、以及出意外时怎么兜底。")

table(doc, [
    ["对比项", "普通模式（把「PTA 模式」的勾去掉）", "PTA 模式（默认，勾着）"],
    ["每行缩进怎么来", "一个空格一个空格地敲，完全照你粘进去的原文",
     "先让网页自己补，补对了就不重复敲；补错了就删掉重敲"],
    ["遇到换行时", "直接按回车，然后照原文敲空格", "按回车 → 比对网页补了几格 → 决定「跳过」还是「删掉」"],
    ["遇到 ( [ { \" '", "原样敲进去", "敲完立刻按一下 Delete，撤掉编辑器自动补的右半边括号"],
    ["按键数量", "100%（最费时）", "大约 85%（一段 183 字符的代码省掉 32 个空格）"],
    ["结果正确性", "正确", "正确（两种走法都会回读核对）"],
    ["什么时候用它", "网页不是 PTA、或者你发现缩进不对想排查时", "默认就用它，几乎不用改"],
], widths=[3.4, 6.1, 6.1])

para(doc, "", space_after=4)
para(doc, "为什么需要「模式」这个东西：PTA 的代码框是 CodeMirror 6，它有两个自动行为 —— "
          "一是你按回车时它会自己把上一行的缩进抄到新行（块头还会多加 4 格），"
          "二是你敲左括号时它会自动补上右括号。如果工具不知道这两件事，就会「它补一遍、我再敲一遍」，"
          "结果缩进变成双倍、括号变成两对。")

tip(doc, "ok", "PTA 模式的核心原则：不赌，只对账。",
    "工具从不假设自己算准了网页会补几格。它按回车之后先看网页实际补了多少，"
    "和自己预测的一样才跳过那几个空格；不一样就发 Shift+Home、Delete 把网页补的抹掉，老老实实照原文敲。"
    "两条路的结果都正确，差别只是省不省按键 —— 所以「规则猜错」永远不会变成「代码写错」。")

h2(doc, "一句话区分")
rich(doc, [("普通模式", {"b": True}), ("＝我照原文一个字符一个字符敲，网页爱补什么我不管。", {}),
           ("　　", {}),
           ("PTA 模式", {"b": True}), ("＝先问网页「你补了几格」，补对了我省事，补错了你让开我自己来。", {})])

tip(doc, "warn", "有一类行它不敢猜：",
    "else: / elif / except / finally 这四种。同一句 else: 在网页上有时补 4 格、有时补 0 格，取决于整段代码的语法结构。"
    "遇到它们，PTA 模式会直接放弃预测，改成「删掉重敲」—— 慢一点，但不会错。"
    "另外空行也一样处理，因为它拿不到上一行的缩进。")

# ---------- 2 ----------
h1(doc, "2", "为什么要这三样东西")

para(doc, "PTA 的编程题（函数题）代码框里，Ctrl+V 是被拦掉的。你按下去，什么都不会发生。")
para(doc, "这件事的原因很简单：网页在「粘贴」这个动作上挂了钩子，一旦检测到粘贴就把内容丢掉。"
          "所以任何「先复制、再粘进去」的办法都不行 —— 包括右键菜单里的粘贴、包括拖拽文字。")

rich(doc, [("但是网页拦不到的东西是：", {}), ("键盘自己敲出来的字符", {"b": True, "color": PURPLE}), ("。", {})],
     space_before=6)
para(doc, "这三套工具做的就是这件事 —— 把你要写的代码，变成一次一次的按键或者一次一次的写入，"
          "直接送到代码框里。整个过程不碰剪贴板，所以「禁止粘贴」这件事跟它无关。")

para(doc, "", space_after=4)
tip(doc, "ok", "效果：", "一段 100 行的 Python 函数，1～2 秒内出现在代码框里，缩进、空行、中文注释都正常。")

# ---------- 3 ----------
h1(doc, "3", "三种方式，选一个")

table(doc, [
    ["", "方案 A　书签", "方案 B　exe", "方案 C　油猴脚本"],
    ["要装什么", "一个书签（30 秒）", "下载一个 exe", "装扩展 + 装脚本"],
    ["能过禁粘贴", "能", "能（真按键）", "能"],
    ["需要联网", "不需要", "不需要", "不需要"],
    ["会不会被拦", "不会（就是个书签）", "Windows 可能提示「已保护你的电脑」", "不会"],
    ["适合谁", "大多数人", "不想装浏览器扩展的", "已经装了油猴的"],
], widths=[2.8, 4.3, 4.3, 4.3])

para(doc, "", space_after=6)
para(doc, "下面重点讲方案 A，因为它是唯一「装完就不用再管」的：书签一直在书签栏里，"
          "以后每次答题点一下就行。方案 B、C 放在第 7、8 章，用得着再看。")

h2(doc, "怎么选：三种情况")
rich(doc, [("① ", {"b": True, "color": PURPLE}),
           ("自己的电脑、能装扩展、只想点一下就完事", {}),
           (" → 方案 A（书签）", {"b": True})], indent=0.3)
rich(doc, [("② ", {"b": True, "color": PURPLE}),
           ("这台电脑不让装扩展 / 是机房电脑 / 扩展装了就报错", {}),
           (" → 方案 B（exe）", {"b": True})], indent=0.3)
rich(doc, [("③ ", {"b": True, "color": PURPLE}),
           ("已经装了 Tampermonkey，而且不想每次点书签", {}),
           (" → 方案 C（油猴）", {"b": True})], indent=0.3)

para(doc, "", space_after=2)
para(doc, "三种方案的写入原理完全一样（都不碰剪贴板），区别只在「怎么把面板叫出来」："
          "书签要你点一下，exe 是一个独立窗口，油猴是打开页面就自动弹。所以任选一种学会就够了，"
          "三者可以同时装，不会互相干扰。")

# ---------- 4 ----------
h1(doc, "4", "方案 A：书签（推荐，30 秒装完）")

para(doc, "整个工具就是一段代码，存在浏览器的「书签」里。你点它一下，它就在当前页面弹出一个面板。"
          "它不需要扩展权限，也不联网。")

h2(doc, "把书签栏打开，再把按钮拖上去", step="①")
para(doc, "先在浏览器里按 Ctrl + Shift + B，上方会多出一条横栏 —— 那就是书签栏。")
para(doc, "然后打开配套的「安装书签.html」，按住里面那个紫色按钮不放，拖到书签栏上松手。")
figure(doc, "08_拖书签.png", "图 2　按住紫色按钮 → 拖到书签栏 → 松手。松手早了会变成「打开这个链接」，那就再拖一次。", 9.6)

tip(doc, "warn", "拖不动？", "安装页里还有一个「拖不动？点这里复制」按钮：复制之后按 Ctrl+Shift+O 打开书签管理器，"
                        "右上角 ⋮ → 添加新书签 → 名称随便写 → 网址粘进去 → 保存。")

h2(doc, "打开一道函数题", step="②")
para(doc, "在 PTA 里进入答题页，切到「函数题」标签，随便点开一道。判断标准很简单：")
rich(doc, [("页面右半边有一个黑底的代码框 —— 那就对了。", {"b": True})], indent=0.4)
figure(doc, "01_打开题目.png", "图 3　左边是题目，右边是代码框。这一页就是工具能干活的地方。")

tip(doc, "info", "注意：", "单选题和填空题的页面上没有代码框，在那里点书签会提示「没找到代码框」，这是正常的。")

h2(doc, "点一下书签，面板弹出来", step="③")
para(doc, "在书签栏上点刚才装的那个书签，屏幕中央会弹出一个深紫色的面板。")
figure(doc, "02_面板弹出.png", "图 4　面板弹出。它盖在页面上，但不会挡住你的代码框之外的任何东西，也不会自己点按钮。")

para(doc, "再点一次书签 = 把面板关掉。这个很方便，不用去找右上角的 ×。")

h2(doc, "把代码粘到面板里（注意是面板，不是代码框）", step="④")
para(doc, "这一步是最容易搞错的地方：")
rich(doc, [("要粘的是", {}), ("面板里那个大黑框", {"b": True, "color": PURPLE}),
           ("，不是右边 PTA 的代码框。", {})], indent=0.4)
para(doc, "面板里的框没有禁粘贴，Ctrl+V 正常能用。")
figure(doc, "03_粘入代码.png", "图 5　代码已经粘进面板。缩进、空行都原样保留。")

h2(doc, "点「写进代码框」（或者按 Ctrl+Enter）", step="⑤")
para(doc, "点那个紫色的「写进代码框」按钮，或者直接在面板里按 Ctrl+Enter。")
figure(doc, "04_写入成功.png", "图 6　面板底部变成绿色的「✓ 已写入 99 个字符（CodeMirror）」。看到绿字就是成功了。")

para(doc, "这句话的意思是：它已经把代码写进去了，而且写完还读回来跟原文对了一遍，一模一样。"
          "如果对不上，它会显示红字让你自己看一眼 —— 不会假装成功。")

h2(doc, "关掉面板，确认代码真的在里面", step="⑥")
para(doc, "点「关闭」，或者再点一次书签。面板消失，右边代码框里就是你刚才那段代码。")
figure(doc, "05_关掉面板看代码.png", "图 7　代码在 PTA 自己的代码框里，可以正常编辑、可以运行测试。")

h2(doc, "自己点「测试用例」跑一下", step="⑦")
para(doc, "接下来这一步跟工具无关，是 PTA 自己的功能。点右上角的「测试用例」。")
figure(doc, "06_点测试用例.png", "图 8　点右上角「测试用例」，PTA 会用题目的样例数据跑一遍你的代码。")

h2(doc, "全部通过之后，自己点「提交本题作答」", step="⑧")
figure(doc, "07_测试通过.png", "图 9　测试点全部通过。最后那一下「提交本题作答」，由你自己点。")

tip(doc, "bad", "重要：", "工具只写字，不点保存、不点提交。提交这一步永远是你自己按的 —— 因为要交哪一道、什么时候交，只有你知道。")

# ---------- 5 ----------
h1(doc, "5", "面板上每个控件是干什么的")

table(doc, [
    ["控件", "作用", "备注"],
    ["大黑框", "粘代码的地方", "Ctrl+V 直接粘，不禁粘贴"],
    ["写进代码框", "把框里的内容写进 PTA 代码框", "等于 Ctrl+Enter"],
    ["关闭", "关掉面板", "再点一次书签也一样"],
    ["状态行（最下面一行）", "灰字＝等待；绿字＝成功；红字＝失败原因", "成功了会写清写了多少个字符"],
    ["点面板外面", "关掉面板", "和点「关闭」一样"],
], widths=[3.6, 6.4, 6.2])

para(doc, "", space_after=8)
para(doc, "面板可以拖动吗？不需要 —— 它只在你要粘代码的那几秒存在，粘完就关掉。")

# ---------- 6 ----------
h1(doc, "6", "出问题了怎么查")

para(doc, "先看面板最下面那行字，它是唯一可靠的判断依据。").paragraph_format.keep_with_next = True

table(doc, [
    ["你看到什么", "原因", "怎么办"],
    ["红字「没找到代码框 —— 先打开一道编程题（函数题）」",
     "当前页面没有答题区。可能是单选题 / 填空题页，或者函数题还没打开",
     "切到「函数题」标签，点开一道题，再点书签"],
    ["红字「框里是空的」", "面板里什么都没写", "先把代码复制过来，粘进面板"],
    ["红字「写进去了但读回来对不上」", "极少见，通常是页面刚好在刷新", "自己看一眼代码框，把不对的地方改掉"],
    ["绿字成功了，但代码框还是空的", "页面上有两个代码框，写到了另一个", "刷新页面重来一次；如果反复这样，改用方案 B（exe）"],
    ["点书签没反应", "书签装的时候网址没粘全", "删掉重装：Ctrl+Shift+O → 找到它 → 编辑 → 重新粘网址"],
    ["点书签打开了新页面 / 显示一串代码", "书签的网址被浏览器当成普通网址打开了", "确认网址是以 javascript: 开头的，不是 http"],
    ["页面提示「不要粘贴」并拒绝了", "你粘到了 PTA 的代码框里，不是面板里", "粘到面板里 —— 面板是工具自己的框，不禁粘贴"],
    ["面板挡住题目了", "正常现象", "点面板外面关掉它，代码已经写进去了，不会丢"],
    ["粘贴进面板，缩进变成两倍", "代码本身带 Tab 又带空格", "在编辑器里统一成 4 个空格再复制"],
    ["exe 敲完缩进全乱了", "代码框不是 PTA 那种会自动缩进的编辑器", "把「PTA 模式」的勾去掉，改用普通模式（见第 1 章）"],
], widths=[5.4, 4.8, 5.4])

tip(doc, "ok", "这个设计的意义：", "宁可报错，也不猜。它有十来种可能选错代码框的情况（比如「测试用例」面板里也有输入框），"
                                 "所以只在能确认是答题区的时候才写，确认不了就停下来告诉你 —— "
                                 "那次它会显示「没找到代码框 —— 先打开一道编程题（函数题）」，一个字都不会乱写。")

# ---------- 7 ----------
h1(doc, "7", "方案 B：exe（不装扩展、不装脚本）", newpage=True)

para(doc, "如果你连浏览器扩展都不想装，用这个。它是一个独立的窗口程序，双击就开，不用安装。")

table(doc, [
    ["界面上有什么", "作用"],
    ["大文本框", "粘代码的地方"],
    ["速度", "每个字之间等多久。默认「快 (8 毫秒)」，一般不用改"],
    ["等待 [3] 秒", "点「开始敲」之后给你几秒切回浏览器。默认 3 秒，可以自己改（0～60）"],
    ["先全选清空代码框", "勾上＝先把 PTA 代码框里的旧内容清掉再写"],
    ["PTA 模式", "勾上＝利用网页自己补的缩进，少敲一些空格（默认开，详见第 1 章）"],
    ["置顶", "窗口永远在最前面，不被题目挡住（默认开，Ctrl+T 切换）"],
    ["开始敲 / 停止", "开始 / 中途停下（已经敲进去的不会撤销）"],
], widths=[4.2, 11.4])

para(doc, "", space_after=6)
para(doc, "用法四步：")
rich(doc, [("① ", {"b": True, "color": PURPLE}), ("把代码粘进 exe 的框里（框空着也行 —— 它会自己去读剪贴板）", {})], indent=0.3)
rich(doc, [("② ", {"b": True, "color": PURPLE}), ("点「开始敲」", {})], indent=0.3)
rich(doc, [("③ ", {"b": True, "color": PURPLE}), ("倒计时结束前切回浏览器，用鼠标点一下代码框，让光标在里面", {})], indent=0.3)
rich(doc, [("④ ", {"b": True, "color": PURPLE}), ("等它敲完，然后自己点「测试用例」和「提交本题作答」", {})], indent=0.3)

tip(doc, "warn", "它会先检查前台窗口：",
    "如果最前面的程序不是浏览器（Chrome / Edge / Firefox 等），它会直接取消并提示「一个字都没发出去」。"
    "这是为了防止你切错窗口，把代码敲到别的地方去。")

tip(doc, "info", "名字有点奇怪？", "这个 exe 叫「哇嘞哇嘞大雷猪」，就是随手起的名字，不影响功能。"
                                "第一次运行 Windows 可能弹「已保护你的电脑」，点「更多信息」→「仍要运行」。")

# ---------- 8 ----------
h1(doc, "8", "方案 C：油猴脚本")

para(doc, "已经装了 Tampermonkey（油猴）的话，这是最省事的：装一次，以后每道题都自动弹出面板。")

rich(doc, [("① ", {"b": True, "color": PURPLE}), ("装 Tampermonkey（Edge 商店 / Chrome 商店搜「Tampermonkey」）", {})], indent=0.3)
rich(doc, [("② ", {"b": True, "color": PURPLE}), ("双击 ", {}), ("一键安装.bat", {"mono": True}),
           ("，浏览器会跳到油猴的安装页，点绿色「安装」", {})], indent=0.3)
rich(doc, [("③ ", {"b": True, "color": PURPLE}), ("打开 PTA 的函数题页面 —— 面板会自己弹出来，不用点书签", {})], indent=0.3)

para(doc, "")
para(doc, "和方案 A 的区别只有一个：方案 A 要点书签，方案 C 自动弹。代码写入的原理完全一样。")

# ---------- 9 ----------
h1(doc, "9", "它不会做什么 · 原理一句话")

table(doc, [
    ["不会做的事", "说明"],
    ["不点「提交」", "提交这一步永远是你自己按"],
    ["不动剪贴板", "不读、不写系统剪贴板（exe 例外：框空着时读一次，为了省你一步粘贴）"],
    ["不联网", "书签版和 exe 版都是零网络请求，代码不出你的电脑"],
    ["不改题目 / 不改答案", "它只往代码框里写字，别的一概不碰"],
    ["不绕过任何检测", "它没有假装成正常输入去骗过什么 —— 它就是正常输入"],
], widths=[4.6, 11.0])

para(doc, "", space_after=4)
tip(doc, "info", "原理一句话：",
    "PTA 拦的是「粘贴」这个事件，而工具做的是「往代码框里写入文字」，两件事不一样。"
    "书签版调的是编辑器自己的接口（CodeMirror 的 view.dispatch），exe 版发的是真实的键盘消息（SendInput）。"
    "两条路都不经过剪贴板，所以「禁止粘贴」对它没有意义。")

p = para(doc, "— 完 —　截图均为虚构演示页，不含真实学校名称、教师姓名、学号或账号信息。",
         size=9, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=12)

doc.save(OUT)
print("saved:", OUT, os.path.getsize(OUT), "bytes")
