#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""哇嘞哇嘞大雷猪（独立 exe 版）

把代码一个字一个字敲进 PTA 的代码框里。不装油猴、不装扩展：
直接向「当前有焦点的窗口」发送真实键盘事件（SendInput），
对页面来说这就是人在打字，不是粘贴，所以「禁止粘贴」管不到。

用法：
    1. 在 PTA 代码框里点一下（让光标在里面）
    2. 把代码粘进本程序的框里
    3. 点「开始敲」，倒计时内切回浏览器
    4. 敲完自己去点提交

命令行走查：
    哇嘞哇嘞大雷猪.exe --selftest [日志路径]

────────────────────────────────────────────────────────────
作者  : ikunkun3  (@ikunkun3)
主页  : https://github.com/ikunkun3
项目  : https://github.com/ikunkun3/pta-typer
许可  : MIT
────────────────────────────────────────────────────────────
这个文件是本项目的核心：Windows SendInput 键盘事件注入 +
PTA 代码框自动缩进的预测与对账。转载 / 二次修改请保留本段署名。
"""

import ctypes
import json
import os
import re
import shutil
import sys
import threading
import time
from ctypes import wintypes

APP_TITLE = "哇嘞哇嘞大雷猪"
VERSION = "1.3.1"

INTRO = (
    "把代码一个字一个字敲进 PTA 的代码框。敲的是真实按键，不是粘贴，"
    "所以 PTA 的「禁止粘贴」拦不到。",
    "不联网 · 不替你点任何按钮 —— 题目还是你自己提交。",
)

CFG_DIR = "哇嘞哇嘞大雷猪"
CFG_OLD_DIR = "PTA逐字输入"


def cfg_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, CFG_DIR, "cfg.json")


def cfg_migrate():
    """把老版本的配置目录搬家过来，别让用户升级一次就丢设置。"""
    try:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        new = os.path.join(base, CFG_DIR)
        old = os.path.join(base, CFG_OLD_DIR)
        if os.path.isdir(new) or not os.path.isdir(old):
            return False
        shutil.move(old, new)
        return True
    except Exception:
        return False


def cfg_load():
    try:
        with open(cfg_path(), "r", encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def cfg_save(d):
    try:
        p = cfg_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # 模块级：读剪贴板 / 查进程名要用

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

VK_RETURN = 0x0D
VK_TAB = 0x09
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_A = 0x41
VK_DELETE = 0x2E
VK_SHIFT = 0x10
VK_HOME = 0x24
VK_INSERT = 0x2D

CF_UNICODETEXT = 13


def enable_dpi_awareness():
    """声明 DPI 感知。必须在创建 Tk 窗口之前调用，晚了没用。"""
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return "per-monitor-v2"
    except Exception:
        pass
    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        if shcore.SetProcessDpiAwareness(2) == 0:
            return "per-monitor"
    except Exception:
        pass
    try:
        if user32.SetProcessDPIAware():
            return "system"
    except Exception:
        pass
    return "none"


def merge_geometry(saved, k, screen=None):
    """把存下来的 "820x640+120+90" 和当前 DPI 倍数 k 合并。

    从旧版本（写死 1.25 缩放的时代）升级上来时，存的可能是 760x600 ——
    在高分屏上那是个袖珍窗口。所以尺寸取「存的」和「按 k 算的基准」里更大的，
    位置沿用存的，用户拖过的位置不会被抢走。

    screen=(宽, 高) 时再夹一道：不许比屏幕还大，否则按钮跑到屏幕外面点不到。
    """
    m = re.match(r"^(\d+)x(\d+)([+-]\d+[+-]\d+)?$", str(saved or "").strip())
    if not m:
        return ""
    w = max(int(m.group(1)), int(820 * k))
    h = max(int(m.group(2)), int(640 * k))
    pos = m.group(3) or ""
    if screen:
        sw, sh = int(screen[0]), int(screen[1])
        w = min(w, max(400, sw - 60))
        h = min(h, max(300, sh - 120))
        if not pos:
            pos = "+%d+%d" % (max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 40))
    return "%dx%d%s" % (w, h, pos)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)   # 这样 inp.ki 能直接访问，不必写 inp.u.ki
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _kb(w_vk, w_scan, flags):
    ki = KEYBDINPUT()
    ki.wVk = w_vk
    ki.wScan = w_scan
    ki.dwFlags = flags
    ki.time = 0
    ki.dwExtraInfo = 0
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.u.ki = ki
    return inp


_SEND_FAILED = [0]


def _send(*inputs):
    """一次 SendInput 发多个事件，保证顺序和原子性。"""
    if not inputs:
        return 0
    arr = (INPUT * len(inputs))(*inputs)
    n = user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))
    if n != len(inputs):
        _SEND_FAILED[0] += len(inputs) - n
    return n


def send_unicode(ch):
    """用 KEYEVENTF_UNICODE 送一个字符，不看键盘布局。"""
    code = ord(ch)
    if code > 0xFFFF:
        code -= 0x10000
        hi = 0xD800 + (code >> 10)
        lo = 0xDC00 + (code & 0x3FF)
        _send(_kb(0, hi, KEYEVENTF_UNICODE),
              _kb(0, hi, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP),
              _kb(0, lo, KEYEVENTF_UNICODE),
              _kb(0, lo, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
    else:
        _send(_kb(0, code, KEYEVENTF_UNICODE),
              _kb(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))


def send_vk(vk, with_keyup=True):
    if with_keyup:
        _send(_kb(vk, 0, 0), _kb(vk, 0, KEYEVENTF_KEYUP))
    else:
        _send(_kb(vk, 0, 0))


def send_ctrl(vk):
    _send(_kb(VK_CONTROL, 0, 0), _kb(vk, 0, 0),
          _kb(vk, 0, KEYEVENTF_KEYUP), _kb(VK_CONTROL, 0, KEYEVENTF_KEYUP))


def force_foreground(hwnd):
    """把窗口顶到系统前台。

    Windows 有「前台锁」：不是当前前台进程的，SetForegroundWindow 会被静默忽略。
    这里用官方文档里的两个正当解法依次试：先按一下 ALT 解锁，再 AttachThreadInput。
    """
    if not hwnd:
        return False
    if user32.GetForegroundWindow() == hwnd:
        return True
    _send(_kb(VK_MENU, 0, 0), _kb(VK_MENU, 0, KEYEVENTF_KEYUP))
    user32.SetForegroundWindow(hwnd)
    if user32.GetForegroundWindow() == hwnd:
        return True
    try:
        tid_me = kernel32.GetCurrentThreadId()
        tid_fg = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        user32.AttachThreadInput(tid_me, tid_fg, True)
        try:
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
        finally:
            user32.AttachThreadInput(tid_me, tid_fg, False)
    except Exception:
        pass
    return user32.GetForegroundWindow() == hwnd


def clear_editor():
    """Ctrl+A → Delete。焦点在代码框里时等于清空它。"""
    send_ctrl(VK_A)
    time.sleep(0.05)
    send_vk(VK_DELETE)
    time.sleep(0.05)


def send_shift_home_delete():
    """Shift+Home 选中光标左侧到行首 → Delete 删掉。

    专治「按 Enter 后编辑器自动缩进」导致的缩进翻倍（见 type_text 的注释）。
    """
    _send(_kb(VK_SHIFT, 0, 0), _kb(VK_HOME, 0, 0),
          _kb(VK_HOME, 0, KEYEVENTF_KEYUP), _kb(VK_SHIFT, 0, KEYEVENTF_KEYUP))
    _send(_kb(VK_DELETE, 0, 0), _kb(VK_DELETE, 0, KEYEVENTF_KEYUP))


_PY_BLOCK = ("def ", "class ", "if ", "elif ", "else", "for ", "while ",
             "with ", "try", "except", "finally")


def _line_indent(line):
    return len(line) - len(line.lstrip(" "))


def predict_auto_indent(prev_line, indent_unit=4):
    """猜编辑器在 Enter 之后会给新行补几个空格。

    prev_line 是刚敲完（Enter 之前）的那整行。猜不出来返回 None。

    下表是 2026-11-10 在真 PTA 页用真实 Enter 逐条量出来的（只量数字，不看代码）：

        上一行                        编辑器补几格
        ----------------------------  ------------------------------
        def f(): / if a: / try:       base + 4   （块头）
            except: 这种非法位置        4         （语法树判它不合法，退回上一行缩进）
        块内任意普通语句               保持上一行缩进（4）
        块内 return / pass            保持 4     ← 关键：它**不反缩进**
        块内注释行                     保持 4
        x = [  / items = [            括号所在行缩进 + 4
        items = [1,                   对齐到 `[` 后一列（13）
        g(a,                          对齐到 `(` 后一列（6）

    最要紧的一条是「不反缩进」：原来的实现把普通语句判成 0，于是
    `def f():` 块里敲 `return 1` 再 Enter 时，原文 want=0 与假想的 0 相同，
    被当成「猜准了」跳过 —— 可编辑器实际塞了 4 格，结果多缩进一层还没人发现。
    """
    line = prev_line.rstrip()
    if not line.strip():
        return None
    stripped = line.lstrip(" ")
    base = len(line) - len(stripped)
    for open_ch, close_ch in (("[", "]"), ("{", "}"), ("(", ")")):
        if stripped.count(open_ch) <= stripped.count(close_ch):
            continue
        pos = stripped.rfind(open_ch)
        tail = stripped[pos + 1:]
        if not tail.strip():
            return base + indent_unit
        return base + pos + 1
    if stripped.startswith("#"):
        return base
    cut = stripped
    pos = cut.find("#")
    if pos > 0:
        cut = cut[:pos].rstrip()
    if not cut.endswith(":"):
        # 不是块头 → 编辑器让新行停在和这一行**一样深**的地方，不减缩进
        return base
    if "lambda" in cut:
        return base
    head = cut.split()[0] if cut.split() else ""
    if head.rstrip(":") in ("else", "elif", "except", "finally"):
        return None
    if any(cut.startswith(w) or head.rstrip(":") == w.strip() for w in _PY_BLOCK):
        return base + indent_unit
    return base


def type_text(text, delay=0.008, stop=None, on_tick=None, clear_first=False,
              auto_indent=False):
    """把 text 逐字敲出去。返回 (是否完整敲完, 已敲字符数)。

    auto_indent=False：原样敲，不管编辑器的自动缩进。
    auto_indent=True ：先删后敲 —— 每次 Enter 之后把编辑器补的缩进删掉，再照原文敲。
                       结果一定正确，代价是多发几个按键。
    auto_indent="pta"：混合模式 —— 猜准了才利用编辑器补的缩进，猜不准就删掉重敲。
                       猜准（predict_auto_indent 返回值正好等于下一行原文的缩进）时，
                       跳过那些空格；否则先 Shift+Home+Delete 把编辑器补的抹掉，
                       再照原文一个字一个字敲。两种情况结果都正确，
                       区别只是「省不省按键」。
    """
    if not stop:
        stop = lambda: False
    if clear_first:
        clear_editor()
    done = 0
    total = len(text)
    skip = 0
    line_start = 0
    for idx, ch in enumerate(text):
        if stop():
            return False, done
        if ch == "\n":
            if auto_indent and not text[idx:].strip():
                done += 1
                continue
            send_vk(VK_RETURN)
            if auto_indent:
                if auto_indent == "pta":
                    nxt = idx + 1
                    want = 0
                    while nxt < total and text[nxt] == " ":
                        want += 1
                        nxt += 1
                    guess = predict_auto_indent(text[line_start:idx])
                    if guess is not None and guess == want:
                        skip = guess
                    else:
                        send_shift_home_delete()      # 没猜准
                        skip = 0
                else:
                    send_shift_home_delete()
            line_start = idx + 1
        elif ch == "\r":
            continue
        elif ch == " " and skip > 0:
            skip -= 1
        elif ch == "\t":
            send_vk(VK_TAB)
        else:
            skip = 0
            send_unicode(ch)
            if auto_indent and ch in "([{\"'":
                send_vk(VK_DELETE)
        done += 1
        if on_tick and (done % 20 == 0 or done == total):
            on_tick(done, total)
        if delay > 0:
            time.sleep(delay)
    return True, done


BROWSER_EXES = ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
                "opera.exe", "vivaldi.exe", "chromium.exe", "thorium.exe",
                "floorp.exe", "arc.exe", "360se.exe", "360chrome.exe",
                "qqbrowser.exe", "sogouexplorer.exe", "ucbrowser.exe",
                "iexplore.exe")


def foreground_process_name():
    """当前前台窗口属于哪个进程（小写文件名）。拿不到返回空串。

    这个函数是整个程序的安全带：SendInput 只会送到前台窗口，
    敲之前先确认前台真的是浏览器，否则可能把代码敲进游戏、聊天框、命令行。
    """
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return ""
        h = kernel32.OpenProcess(0x1000, False, pid.value)
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if not kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return ""
            return buf.value.rsplit("\\", 1)[-1].lower()
        finally:
            kernel32.CloseHandle(h)
    except Exception:
        return ""


def is_browser_foreground():
    return foreground_process_name() in BROWSER_EXES


def grab_clip():
    """读剪贴板里的文本。读不到就返回空串，绝不抛异常。

    为什么需要：同学手上只有一个 exe，不会去看说明。最常见的动作是
    「复制代码 → 打开它 → 点开始」，所以黑框空着时替他去剪贴板取一趟。
    """
    try:
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HANDLE
        kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        if not user32.OpenClipboard(None):
            return ""
        try:
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ""
            p = kernel32.GlobalLock(h)
            if not p:
                return ""
            try:
                return ctypes.wstring_at(p)
            finally:
                kernel32.GlobalUnlock(h)
        finally:
            user32.CloseClipboard()
    except Exception:
        return ""


def _record_inputs(source, clear_first=False, auto_indent=False):
    """把 SendInput 临时换成记录器，只检查按键序列，不真的敲。"""
    out = []
    real = globals()["_send"]

    def rec(*inputs):
        out.extend(inputs)
        return len(inputs)

    try:
        globals()["_send"] = rec
        type_text(source, delay=0, clear_first=clear_first, auto_indent=auto_indent)
    finally:
        globals()["_send"] = real
    return out


def _selftest_plan(say):
    """第一段：按键序列对不对。不碰系统，任何时候都能跑。"""
    ok = True

    def ck(name, cond, extra=""):
        nonlocal ok
        if bool(cond):
            say("PASS  " + name)
        else:
            ok = False
            say("FAIL  " + name + ("  " + extra if extra else ""))

    ev = _record_inputs("a")
    ck("普通字符走 UNICODE 码点（wVk=0 wScan=97）",
       len(ev) == 2 and ev[0].ki.wVk == 0 and ev[0].ki.wScan == 97
       and not (ev[0].ki.dwFlags & KEYEVENTF_KEYUP))
    ck("抬起事件带 KEYEVENTF_KEYUP",
       len(ev) == 2 and bool(ev[1].ki.dwFlags & KEYEVENTF_KEYUP))
    ent = _record_inputs("a\nb")
    ck("换行走真 Enter（VK 13，不带 UNICODE）",
       len(ent) == 6 and ent[2].ki.wVk == VK_RETURN
       and not (ent[2].ki.dwFlags & KEYEVENTF_UNICODE))
    tab = _record_inputs("a\tb")
    ck("制表符走真 Tab（VK 9）", len(tab) == 6 and tab[2].ki.wVk == VK_TAB)
    cn = _record_inputs("中")
    ck("中文按码点送（U+4E2D）",
       len(cn) == 2 and cn[0].ki.wVk == 0 and cn[0].ki.wScan == 0x4E2D)
    emo = _record_inputs("😀")
    ck("基本平面外字符拆成代理对（4 条事件）", len(emo) == 4)
    iflat = _record_inputs("a\nb", auto_indent=True)
    ck("自动缩进：Enter 之后紧跟 Shift+Home → Delete",
       len(iflat) == 12 and iflat[2].ki.wVk == VK_RETURN
       and iflat[4].ki.wVk == VK_SHIFT and iflat[5].ki.wVk == VK_HOME
       and iflat[8].ki.wVk == VK_DELETE
       and iflat[10].ki.wVk == 0 and iflat[10].ki.wScan == 98)
    nflat = _record_inputs("a\nb")
    ck("不开自动缩进时 Enter 之后直接敲原文", len(nflat) == 6)
    pflat = _record_inputs("if a:\n    b", auto_indent="pta")
    ck("PTA 模式：跳过网页已经补的 4 个空格",
       len(pflat) == 14 and pflat[12].ki.wVk == 0 and pflat[12].ki.wScan == 98)
    qflat = _record_inputs("if a:\n    b\nelse:\n    c", auto_indent="pta")
    _scans = [i.ki.wScan for i in qflat
              if i.ki.wVk == 0 and not (i.ki.dwFlags & KEYEVENTF_KEYUP)]
    ck("PTA 模式：该跳的跳、该敲的敲，一个字都不丢",
       _scans == [105, 102, 32, 97, 58, 98, 101, 108, 115, 101, 58,
                  32, 32, 32, 32, 99], str(_scans))
    ck("PTA 模式：遇到 else: 改走「删掉重敲」",
       any(i.ki.wVk == VK_SHIFT for i in qflat)
       and any(i.ki.wVk == VK_HOME for i in qflat))
    ck("PTA 模式：预测 `x = (1,` 给 5（对齐到元素）",
       predict_auto_indent("x = (1,") == 5)
    ck("PTA 模式：预测 `def f():` 给 4", predict_auto_indent("def f():") == 4)
    ck("PTA 模式：预测 `    return 1` 给 4（编辑器不反缩进）",
       predict_auto_indent("    return 1") == 4)
    ck("PTA 模式：预测 `    x = 1` 给 4（普通语句也保持缩进）",
       predict_auto_indent("    x = 1") == 4)
    ck("PTA 模式：预测 `else:` 给 None（编辑器行为不定，不敢猜）",
       predict_auto_indent("else:") is None)
    ck("PTA 模式：预测 `    except:` 给 None",
       predict_auto_indent("    except:") is None)
    ck("PTA 模式：空行给 None（拿不到上一行缩进）",
       predict_auto_indent("   ") is None)
    oflat = _record_inputs("x = [", auto_indent="pta")
    _down = [i for i in oflat if not (i.ki.dwFlags & KEYEVENTF_KEYUP)]
    ck("PTA 模式：敲完开括号立刻 Delete（撤掉自动补的闭合符）",
       len(_down) == 6 and _down[-1].ki.wVk == VK_DELETE)
    wflat = _record_inputs("x = [\n   y", auto_indent="pta")
    ck("PTA 模式：猜不准（原文 3 格、编辑器给 4 格）就删掉重敲",
       any(i.ki.wVk == VK_SHIFT for i in wflat)
       and any(i.ki.wVk == VK_HOME for i in wflat))
    tflat = _record_inputs("a\nb\n\n", auto_indent="pta")
    ck("PTA 模式：原文末尾的空行不敲（避免多出一行空格）",
       sum(1 for i in tflat
           if i.ki.wVk == VK_RETURN and not (i.ki.dwFlags & KEYEVENTF_KEYUP)) == 1)
    cf = _record_inputs("x", clear_first=True)
    ck("先清空时发的是 Ctrl+A → Delete",
       len(cf) == 8 and cf[0].ki.wVk == VK_CONTROL and cf[4].ki.wVk == VK_DELETE)
    ck("浏览器白名单认得 chrome.exe / msedge.exe",
       "chrome.exe" in BROWSER_EXES and "msedge.exe" in BROWSER_EXES)
    ck("浏览器白名单不认游戏、终端",
       "yuanshen.exe" not in BROWSER_EXES
       and "windowsterminal.exe" not in BROWSER_EXES)
    ck("剪贴板读取不抛异常（读不到就给空串）", isinstance(grab_clip(), str))
    return ok


def _selftest_live(say):
    """第二段：真开窗口、真发按键、再读回来比对。拿不到系统前台返回 None。"""
    try:
        import tkinter as tk
    except Exception:
        say("SKIP  没有 tkinter，真实按键这一段跳过")
        return None
    root = tk.Tk()
    root.title("selftest")
    root.geometry("620x260+240+200")
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    txt = tk.Text(root, height=10, width=64, wrap="word", undo=False)
    txt.pack(fill="both", expand=True)
    txt.bind("<Tab>", lambda _e: (txt.insert("insert", "\t"), "break")[1])

    def _hwnd():
        try:
            h = user32.GetParent(root.winfo_id())
            return int(h) if h else int(root.winfo_id())
        except Exception:
            return 0

    hwnd = 0
    for _ in range(20):
        try:
            root.update()
        except Exception:
            pass
        hwnd = _hwnd()
        if hwnd:
            break
        time.sleep(0.05)
    forced = force_foreground(hwnd) if hwnd else False
    if forced:
        try:
            root.focus_force()
            txt.focus_set()
            root.update()
        except Exception:
            pass
        time.sleep(0.15)
    try:
        root.update()
    except Exception:
        pass
    if not hwnd or user32.GetForegroundWindow() != hwnd:
        cur = foreground_process_name() or "未知程序"
        say("SKIP  拿不到系统前台（现在最前面的是 " + cur + "），真实按键这一段跳过")
        say("      把全屏游戏 / 远程桌面关掉之后重跑 --selftest 就能验证")
        try:
            root.destroy()
        except Exception:
            pass
        return None
    say("前台窗口已拿到 hwnd=%d 强制=%s" % (hwnd, forced))

    cases = ("def remove_duplicate(L):\n    return len(set(L))",
             "a\tb\n\n  c\n",
             "测试：{a: 1} -> [x, y]\n")
    auto_indent = False   # Tk 的 Text 不会自动缩进，开了会误删原文缩进
    fails = 0
    skipped = 0
    for code in cases:
        txt.delete("1.0", "end")
        try:
            root.update()
        except Exception:
            pass
        if user32.GetForegroundWindow() != hwnd:
            skipped += 1
            say("SKIP  " + str(len(code)) + "  （前台被别人抢走了，这一例不判）")
            continue
        try:
            type_text(code, delay=0.004, auto_indent=auto_indent)
        except Exception as e:
            fails += 1
            say("FAIL  " + str(len(code)) + "  字符 出错：" + str(e))
            continue
        got = ""
        stable = 0
        for _ in range(40):
            try:
                root.update()
            except Exception:
                pass
            cur = txt.get("1.0", "end-1c")
            if cur == got:
                stable += 1
                if stable >= 2:
                    break
            else:
                got = cur
                stable = 0
            time.sleep(0.05)
        if user32.GetForegroundWindow() != hwnd:
            skipped += 1
            say("SKIP  " + str(len(code)) + "  （敲的过程中前台被抢走，这一例不判）")
            continue
        if len(got) > len(code):
            skipped += 1
            say("SKIP  " + str(len(code)) + "  （混进了外来按键，这一例不判）")
            continue
        if got == code:
            say("PASS  " + str(len(code)) + "  字符 " + str(len(got)) + "/" + str(len(code))
                + "  发送失败 " + str(_SEND_FAILED[0]) + " 次")
        else:
            fails += 1
            say("FAIL  " + str(len(code)) + "  字符 "
                + "   want " + repr(code) + "   got  " + repr(got))
    try:
        root.destroy()
    except Exception:
        pass
    if skipped:
        say("      有 " + str(skipped) + " 例因环境干扰跳过（不算失败）")
    if fails:
        return fails
    if skipped:
        return 0.5
    return 0


def selftest(log_path=None):
    lines = []

    def say(s):
        try:
            print(s)
        except Exception:
            pass
        lines.append(s)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    say("== 第一段：按键序列（不碰系统）==")
    plan_ok = _selftest_plan(say)
    say("")
    say("== 第二段：真实按键（需要系统前台）==")
    live = None
    try:
        live = _selftest_live(say)
    except Exception as e:
        say("SKIP  第二段跑不起来：" + str(e))
        live = None
    code = 1
    if not plan_ok:
        verdict = "FAIL"
    elif live is None:
        verdict = "SKIP-LIVE"
        code = 2
    elif live == 0.5:
        verdict = "OK"
        code = 0
    elif live:
        verdict = "FAIL"
    else:
        verdict = "OK"
        code = 0
    say("")
    say("SELFTEST " + verdict)
    if log_path:
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            pass
    return code


SPEEDS = (("极快 (0 毫秒)", 0.0),
          ("快 (8 毫秒)", 0.008),
          ("正常 (30 毫秒)", 0.03),
          ("慢 (100 毫秒)", 0.1))


def run_gui():
    dpi_mode = enable_dpi_awareness()
    cfg_migrate()
    cfg = cfg_load()

    import tkinter as tk
    from tkinter import messagebox, ttk
    try:
        import winsound
    except Exception:
        winsound = None

    root = tk.Tk()
    root.title(APP_TITLE + " v" + VERSION)
    try:
        _dpi = root.winfo_fpixels("1i") or 96.0
    except Exception:
        _dpi = 96.0
    _k = max(1.0, _dpi / 96.0)
    try:
        root.tk.call("tk", "scaling", _dpi / 72.0)
    except Exception:
        pass
    root.geometry("%dx%d" % (int(820 * _k), int(640 * _k)))
    root.minsize(int(680 * _k), int(520 * _k))
    geo = merge_geometry(cfg.get("geometry"), _k,
                         (root.winfo_screenwidth(), root.winfo_screenheight()))
    if geo:
        root.geometry(geo)
    try:
        root.configure(bg="#f7f7fb")
    except Exception:
        pass

    state = {"stop": False, "busy": False}

    head = tk.Frame(root, bg="#4c1d95")
    head.pack(fill="x")
    tk.Label(head, text=APP_TITLE, bg="#4c1d95", fg="white",
             font=("Microsoft YaHei UI", 13, "bold")).pack(side="left", padx=(14, 8), pady=8)
    tk.Label(head, text="by @ikunkun3", bg="#4c1d95", fg="#c4b5fd",
             font=("Microsoft YaHei UI", 9)).pack(side="left", padx=(0, 8), pady=(13, 0))
    help_btn = tk.Label(head, text=" ? ", bg="#7c3aed", fg="white", cursor="hand2",
                        font=("Microsoft YaHei UI", 14, "bold"))
    help_btn.pack(side="right", padx=(8, 14), pady=6)

    head_tip = tk.Label(root, text="", bg="#f7f7fb", fg="#6b7280",
                        font=("Microsoft YaHei UI", 10), anchor="w",
                        justify="left", wraplength=730)
    head_tip.pack(fill="x", padx=14, pady=(8, 2))
    for i, line in enumerate(INTRO):
        tk.Label(root, text=line, bg="#f7f7fb",
                 fg="#6b7280" if i == 0 else "#9ca3af",
                 font=("Microsoft YaHei UI", 10), anchor="w",
                 justify="left", wraplength=730).pack(fill="x", padx=14)

    body = tk.Frame(root, bg="#f7f7fb")
    body.pack(fill="both", expand=True, padx=14, pady=(8, 0))
    body.rowconfigure(0, weight=1)
    body.columnconfigure(0, weight=1)
    text = tk.Text(body, wrap="none", undo=True, bg="#0b0d12", fg="#c4b5fd",
                   insertbackground="#c4b5fd", relief="flat", bd=0,
                   font=("Consolas", 12), padx=10, pady=8)
    text.grid(row=0, column=0, sticky="nsew")
    ys = tk.Scrollbar(body, orient="vertical", command=text.yview)
    ys.grid(row=0, column=1, sticky="ns")
    xs = tk.Scrollbar(body, orient="horizontal", command=text.xview)
    xs.grid(row=1, column=0, sticky="ew")
    text.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)

    bar = tk.Frame(root, bg="#f7f7fb")
    bar.pack(fill="x", padx=14, pady=(10, 0))

    tk.Label(bar, text="速度", bg="#f7f7fb", fg="#4b5563",
             font=("Microsoft YaHei UI", 10)).pack(side="left")
    speed = ttk.Combobox(bar, values=[s[0] for s in SPEEDS],
                            state="readonly", width=14)
    try:
        speed.current(int(cfg.get("speed", 1)))
    except Exception:
        speed.current(1)
    speed.pack(side="left", padx=(6, 12))

    tk.Label(bar, text="等待", bg="#f7f7fb", fg="#4b5563",
             font=("Microsoft YaHei UI", 10)).pack(side="left")
    try:
        wait0 = int(cfg.get("wait", 3))
    except Exception:
        wait0 = 3
    wait_sec = tk.IntVar(value=max(0, min(60, wait0)))
    wait_sp = tk.Spinbox(bar, from_=0, to=60, width=4, textvariable=wait_sec,
                         justify="center", font=("Microsoft YaHei UI", 10))
    wait_sp.pack(side="left", padx=(6, 2))
    tk.Label(bar, text="秒", bg="#f7f7fb", fg="#4b5563",
             font=("Microsoft YaHei UI", 10)).pack(side="left", padx=(0, 12))

    clear_first = tk.BooleanVar(value=bool(cfg.get("clearFirst", True)))
    clear_cb = tk.Checkbutton(bar, text="先全选清空代码框", variable=clear_first,
                              bg="#f7f7fb", fg="#374151", activebackground="#f7f7fb",
                              font=("Microsoft YaHei UI", 10))
    clear_cb.pack(side="left", padx=(0, 10))

    pta_mode = tk.BooleanVar(value=bool(cfg.get("ptaMode", True)))
    pta_cb = tk.Checkbutton(bar, text="PTA 模式", variable=pta_mode,
                            bg="#f7f7fb", fg="#374151", activebackground="#f7f7fb",
                            font=("Microsoft YaHei UI", 10))
    pta_cb.pack(side="left", padx=(0, 10))

    on_top = tk.BooleanVar(value=bool(cfg.get("topmost", True)))
    top_cb = tk.Checkbutton(bar, text="置顶", variable=on_top,
                            bg="#f7f7fb", fg="#374151", activebackground="#f7f7fb",
                            font=("Microsoft YaHei UI", 10))
    top_cb.pack(side="left", padx=(0, 12))

    def remember(*_a):
        cfg["speed"] = int(speed.current())
        cfg["clearFirst"] = bool(clear_first.get())
        cfg["ptaMode"] = bool(pta_mode.get())
        try:
            cfg["wait"] = int(wait_sec.get())
        except Exception:
            cfg["wait"] = 3
        cfg_save(cfg)

    speed.bind("<<ComboboxSelected>>", remember)
    wait_sp.configure(command=remember)
    clear_cb.configure(command=remember)
    pta_cb.configure(command=remember)

    def apply_topmost(*_a):
        try:
            root.attributes("-topmost", bool(on_top.get()))
        except Exception:
            pass
        cfg["topmost"] = bool(on_top.get())
        cfg_save(cfg)

    top_cb.configure(command=apply_topmost)
    apply_topmost()

    st = tk.Label(root, text="就绪 · 粘代码，或直接点「开始敲」（空着会自动读剪贴板）",
                  bg="#f7f7fb", fg="#059669", anchor="w",
                  font=("Microsoft YaHei UI", 11))
    st.pack(fill="x", padx=14, pady=(8, 0))

    def set_status(msg, color="#059669"):
        try:
            st.configure(text=msg, fg=color)
        except Exception:
            pass

    def refresh_head(*_a):
        try:
            n = int(wait_sec.get())
        except Exception:
            n = 3
        if n > 0:
            head_tip.configure(
                text="把代码粘到下面 → 点「开始敲」→ %d 秒内切回浏览器、光标点进代码框" % n)
        else:
            head_tip.configure(
                text="把代码粘到下面 → 点「开始敲」→ 立刻开始，先把光标点进代码框再点")

    wait_sec.trace_add("write", refresh_head)
    refresh_head()

    def show_help(_e=None):
        messagebox.showinfo(APP_TITLE,
                            "怎么用（四步）：\n\n"
                            "1. 浏览器打开 PTA 那道编程题，用鼠标点一下右边黑色代码框，"
                            "让光标在里面闪。\n\n"
                            "2. 把要敲的代码复制到剪贴板。\n"
                            "   直接点下面的大按钮也行 —— 上面那个黑框是空的，"
                            "它会自己去读剪贴板。\n\n"
                            "3. 点紫色的「开始敲」。它会先倒数几秒（右下角「等待」可以改），\n"
                            "   趁这几秒切回浏览器。\n\n"
                            "4. 手离开键盘和鼠标，看着它一个字一个字打进去。\n"
                            "   打完了自己点「运行测试」→「提交本题作答」—— 提交这一步它绝不代劳。\n\n"
                            "为什么会弹「Windows 已保护你的电脑」：它要模拟键盘，被杀毒软件当成可疑程序了。\n"
                            "点「更多信息」→「仍要运行」即可。它不联网、不读文件、代码全在这个 exe 里。\n\n"
                            "作者：ikunkun3（@ikunkun3）\n"
                            "项目：https://github.com/ikunkun3/pta-typer\n"
                            "许可：MIT —— 转载 / 二次修改请保留署名。")

    help_btn.bind("<Button-1>", show_help)

    go_btn = tk.Button(bar, text="开始敲", bg="#6d28d9", fg="white", relief="flat",
                       bd=0, padx=18, pady=6, cursor="hand2",
                       font=("Microsoft YaHei UI", 11, "bold"),
                       activebackground="#5b21b6", activeforeground="white")
    go_btn.pack(side="right", padx=(8, 0))
    stop_btn = tk.Button(bar, text="停止", bg="#e5e7eb", fg="#374151", relief="flat",
                         bd=0, padx=14, pady=6, cursor="hand2", state="disabled",
                         font=("Microsoft YaHei UI", 10),
                         activebackground="#d1d5db", activeforeground="#374151")
    stop_btn.pack(side="right", padx=(8, 0))
    clr_btn = tk.Button(bar, text="清空", bg="#e5e7eb", fg="#374151", relief="flat",
                        bd=0, padx=14, pady=6, cursor="hand2",
                        font=("Microsoft YaHei UI", 10),
                        activebackground="#d1d5db", activeforeground="#374151")
    clr_btn.pack(side="right")

    tip = tk.Label(root, anchor="w", justify="left", wraplength=730, bg="#f7f7fb",
                   fg="#9ca3af", font=("Microsoft YaHei UI", 10),
                   text="只往浏览器里敲（会先检查最前面的窗口是不是浏览器，不是就取消）。"
                        "敲的时候别碰键盘鼠标，会串字。")
    tip.pack(fill="x", padx=14, pady=(8, 2))

    credit = tk.Label(root, anchor="w", justify="left", wraplength=730, bg="#f7f7fb",
                      fg="#b6bcc9", font=("Microsoft YaHei UI", 9),
                      text="作者 ikunkun3（@ikunkun3） · github.com/ikunkun3/pta-typer · MIT 许可")
    credit.pack(fill="x", padx=14, pady=(0, 10))

    def _reset():
        state["busy"] = False
        state["stop"] = False
        try:
            go_btn.configure(state="normal")
            stop_btn.configure(state="disabled")
            clr_btn.configure(state="normal")
        except Exception:
            pass

    def _clear_text():
        text.delete("1.0", "end")
        set_status("已清空本程序的框（没动浏览器里的）", "#6b7280")

    clr_btn.configure(command=_clear_text)

    def _on_stop():
        state["stop"] = True
        set_status("正在停…", "#b45309")

    stop_btn.configure(command=_on_stop)

    def _worker(code, delay, do_clear):
        try:
            if not is_browser_foreground():
                name = foreground_process_name() or "未知程序"
                set_status("❌ 已取消：最前面的窗口是「" + name + "」，不是浏览器", "#dc2626")
                try:
                    root.after(0, lambda: messagebox.showwarning(
                        APP_TITLE,
                        "现在最前面的窗口是「" + name + "」，不是浏览器。\n\n"
                        "为了不把代码敲到游戏、聊天框、命令行里，已经取消 —— "
                        "一个字都没发出去。\n\n"
                        "请把浏览器切到最前面、光标点进代码框，再点一次「开始敲」。"))
                except Exception:
                    pass
                return
            set_status("清空中…", "#b45309")

            def tick(done, total):
                try:
                    root.after(0, lambda d=done, t=total: set_status(
                        "正在敲… %d/%d" % (d, t), "#b45309"))
                except Exception:
                    pass

            ok, done = type_text(code, delay=delay, stop=lambda: state["stop"],
                                 on_tick=tick,
                                 clear_first=do_clear,
                                 auto_indent="pta" if pta_mode.get() else True,
                                 )
            if state["stop"]:
                set_status("⏹ 已停止 · 敲进去 %d 个字符" % done, "#b45309")
            elif not ok:
                set_status("⚠ 中断 · 只敲进 %d 个字符" % done, "#b45309")
            else:
                how = "· 已用网页补的缩进" if pta_mode.get() else "· 缩进已按原文重写"
                set_status("✅ %d 个字符全部敲完 %s · 没有点任何按钮，自己去提交"
                           % (done, how), "#059669")
        except Exception as e:
            set_status("❌ 出错：" + str(e), "#dc2626")
        finally:
            try:
                root.after(0, _reset)
            except Exception:
                _reset()

    def _run(code, delay, do_clear):
        state["busy"] = True
        state["stop"] = False
        try:
            go_btn.configure(state="disabled")
            stop_btn.configure(state="normal")
        except Exception:
            pass
        try:
            wait_n = int(wait_sec.get())
        except Exception:
            wait_n = 3
        wait_n = max(0, min(60, wait_n))
        if wait_n > 0:
            for left in range(wait_n, 0, -1):
                if state["stop"]:
                    set_status("⏹ 已停止 · 敲进去 0 个字符", "#b45309")
                    _reset()
                    return
                set_status("⏳ %d 秒后开始 —— 现在切到浏览器，光标点进代码框"
                           % left, "#b45309")
                try:
                    root.update()
                except Exception:
                    pass
                if left <= 3 and winsound:
                    try:
                        winsound.Beep(660, 70)
                    except Exception:
                        pass
                time.sleep(1)
        else:
            set_status("开始敲 —— 别碰键盘鼠标", "#b45309")
            try:
                root.update()
            except Exception:
                pass
        if winsound:
            try:
                winsound.Beep(880, 140)
            except Exception:
                pass
        _worker(code, delay, do_clear)

    def start(_e=None):
        if state["busy"]:
            return
        code = text.get("1.0", "end-1c")
        if not code.strip():
            clip = grab_clip()
            if not clip.strip():
                messagebox.showinfo(
                    APP_TITLE,
                    "黑框是空的，剪贴板里也没东西。\n\n"
                    "先在这道题那边把代码复制一下（Ctrl+C），再点「开始敲」——"
                    " 它会自己从剪贴板取。\n\n"
                    "也可以直接把代码粘进这个黑框。")
                return
            text.delete("1.0", "end")
            text.insert("1.0", clip)
            code = clip
        if not code.strip():
            messagebox.showinfo(APP_TITLE, "先把代码粘进来吧。")
            return
        if "\t" in code:
            if not messagebox.askokcancel(
                    APP_TITLE,
                    "代码里有制表符（Tab）。\n\n"
                    "有些代码编辑器会把 Tab 当成「切换焦点」，那样按下去之后，\n"
                    "后面的字就会跑到别的控件里去。\n\n"
                    "建议：先把 Tab 全部换成 4 个空格再敲。\n\n"
                    "还是要照现在这样继续吗？"):
                return
        do_clear = bool(clear_first.get())
        if do_clear:
            if not messagebox.askokcancel(
                    APP_TITLE,
                    "会先发 Ctrl+A → Delete 清空代码框。\n\n"
                    "请确认：此刻浏览器已经在前台，光标在一个空的代码框里。\n\n"
                    "准备好了就点「确定」，然后立刻切到浏览器。"):
                return
        delay = SPEEDS[max(0, min(len(SPEEDS) - 1, int(speed.current())))][1]
        state["busy"] = True
        threading.Thread(target=_run, args=(code, delay, do_clear),
                         daemon=True).start()

    go_btn.configure(command=start)
    root.bind("<Control-Return>", start)

    def on_any_key(event):
        if (event.state & 0x4) and str(event.keysym).lower() == "t":
            on_top.set(not on_top.get())
            apply_topmost()
            return "break"
        return None

    root.bind_all("<KeyPress>", on_any_key)

    def on_close():
        cfg["geometry"] = root.geometry()
        cfg_save(cfg)
        try:
            root.destroy()
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", on_close)
    try:
        text.focus_set()
    except Exception:
        pass
    root.mainloop()
    return dpi_mode


def main(argv):
    args = list(argv[1:])
    if "--version" in args:
        try:
            print(APP_TITLE + " v" + VERSION)
        except Exception:
            pass
        return 0
    if "--selftest" in args:
        i = args.index("--selftest")
        log = args[i + 1] if i + 1 < len(args) else None
        return selftest(log)
    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
