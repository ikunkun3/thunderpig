# -*- coding: utf-8 -*-
"""从 书签工具.js 生成 安装书签.html。

书签工具.js 是唯一真相；安装页里那个可拖动的按钮、以及「点这里复制」按钮
都从它生成。改了 .js 之后重跑这个脚本，不然安装页里嵌的还是旧代码。

图标：Lucide（https://lucide.dev，ISC 许可），内联 SVG，零外部请求。

用法：
    python 生成安装页.py
"""
import io
import os
import re
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "书签工具.js")
OUT = os.path.join(HERE, "安装书签.html")


def minify(src):
    """去掉块注释和整行的 // 注释，再压掉多余空白。"""
    s = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    keep = []
    for line in s.split("\n"):
        t = line.strip()
        if not t or t.startswith("//"):
            continue
        keep.append(t)
    return "\n".join(keep)


# Lucide 图标（ISC）。只存内部节点，用 _i() 包成 svg。
ICON = {
    "bookmark": '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>',
    "bar": '<path d="M3 6h18"/><path d="M3 12h18"/><path d="M3 18h9"/>',
    "clipboard": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
                 '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6'
                 'a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "code": '<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>',
    "keyboard": '<path d="M10 8h.01"/><path d="M12 12h.01"/><path d="M14 8h.01"/>'
                '<path d="M16 12h.01"/><path d="M18 8h.01"/><path d="M6 8h.01"/>'
                '<path d="M7 16h10"/><path d="M8 12h.01"/>'
                '<rect width="20" height="16" x="2" y="4" rx="2"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m16 9-5.5 5.5L8 12"/>',
    "alert": '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/>'
             '<line x1="12" x2="12.01" y1="16" y2="16"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6'
              'a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5'
              'a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "mouse": '<path d="M14 4.1 12 6"/><path d="m5.1 8-2.9-.8"/><path d="m6 12-1.9 2"/>'
             '<path d="M7.2 2.2 8 5.1"/><path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5'
             'a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>',
    "sparkles": '<path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594'
                'l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558'
                'a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051'
                'a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"/>'
                '<path d="M20 2v4"/><path d="M22 4h-4"/><circle cx="4" cy="20" r="2"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
            '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
}


def _i(name, size=18, sw=2):
    return ('<svg class="i" viewBox="0 0 24 24" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-width="%s" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">%s</svg>' % (size, size, sw, ICON[name]))


HTML = u"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>装一个书签 · PTA 逐字输入</title>
<style>
:root{
  --bg:#0a0b10; --card:#12141d; --card2:#0f1119; --line:#232636; --line2:#2e3348;
  --fg:#eceef5; --fg2:#a8aec2; --fg3:#767d94;
  --vi:#8b5cf6; --vi2:#7134e0; --vi3:#c4b5fd;
  --ok:#34d399; --warn:#fbbf24; --bad:#f87171;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
     font:15px/1.72 "Microsoft YaHei",system-ui,-apple-system,"Segoe UI",sans-serif;
     background-image:radial-gradient(900px 420px at 50% -160px,rgba(124,58,237,.22),transparent 70%);}
.wrap{max-width:790px;margin:0 auto;padding:54px 24px 80px}

.hero{display:flex;align-items:center;gap:16px;margin:0 0 6px}
.hero .mark{display:flex;align-items:center;justify-content:center;flex:0 0 52px;
  width:52px;height:52px;border-radius:15px;color:#fff;
  background:linear-gradient(145deg,#8b5cf6,#6d28d9);
  box-shadow:0 12px 30px -10px rgba(124,58,237,.9),0 1px 0 rgba(255,255,255,.3) inset}
h1{font-size:27px;line-height:1.25;margin:0;letter-spacing:.2px}
.sub{color:var(--fg2);margin:14px 0 36px;font-size:14.5px}
.sub b{color:var(--vi3);font-weight:600}

.step{background:linear-gradient(180deg,var(--card),var(--card2));
  border:1px solid var(--line);border-radius:16px;padding:22px 24px 20px;margin:0 0 16px;
  position:relative;box-shadow:0 18px 40px -32px #000}
.step::after{content:"";position:absolute;left:24px;right:24px;top:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.1),transparent)}
.step h2{font-size:17px;margin:0 0 12px;display:flex;align-items:center;gap:11px;
  font-weight:600;letter-spacing:.2px}
.n{display:inline-flex;width:27px;height:27px;border-radius:9px;color:#fff;
  align-items:center;justify-content:center;font-size:13.5px;font-weight:700;flex:0 0 27px;
  background:linear-gradient(145deg,#8b5cf6,#6d28d9);
  box-shadow:0 5px 14px -6px rgba(124,58,237,.95),0 1px 0 rgba(255,255,255,.26) inset}
p{margin:9px 0}

.drag{display:inline-flex;align-items:center;gap:10px;color:#fff;text-decoration:none;
  padding:14px 28px;border-radius:12px;font-size:16px;font-weight:700;cursor:grab;
  background:linear-gradient(180deg,#8b5cf6,#7134e0);
  box-shadow:0 14px 34px -12px rgba(124,58,237,1),0 1px 0 rgba(255,255,255,.32) inset;
  transition:transform .12s,filter .15s;margin:8px 0 12px}
.drag:hover{filter:brightness(1.07)}
.drag:active{cursor:grabbing;transform:translateY(1px)}
.drag .i{opacity:.95}

.bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:14px 0 0;
  padding:13px 15px;background:rgba(255,255,255,.025);border:1px dashed var(--line2);
  border-radius:12px}
.bar .txt{color:var(--fg3);font-size:13px;flex:1;min-width:220px}
button{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.07);
  color:#dfe3ec;border:1px solid rgba(255,255,255,.09);border-radius:10px;padding:9px 15px;
  font:14px "Microsoft YaHei",sans-serif;cursor:pointer;transition:background .14s,border-color .14s}
button:hover{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.16)}
button.done{background:rgba(16,185,129,.14);border-color:rgba(16,185,129,.4);color:var(--ok)}

.note{display:flex;gap:10px;align-items:flex-start;padding:11px 14px;border-radius:0 10px 10px 0;
  margin:13px 0;font-size:13.5px;line-height:1.62}
.note .i{flex:0 0 17px;margin-top:2px}
.note.ok{background:rgba(16,185,129,.09);border-left:3px solid var(--ok);color:#b7e6cd}
.note.ok .i{color:var(--ok)}
.note.stop{background:rgba(239,68,68,.09);border-left:3px solid var(--bad);color:#f2c2c2}
.note.stop .i{color:var(--bad)}
.note.warn{background:rgba(251,191,36,.09);border-left:3px solid var(--warn);color:#f3dcae}
.note.warn .i{color:var(--warn)}
.note.info{background:rgba(139,92,246,.11);border-left:3px solid var(--vi);color:#d5ccf8}
.note.info .i{color:var(--vi3)}

code{background:#1a1f2e;padding:2px 6px;border-radius:5px;font:12.5px Consolas,"Cascadia Mono",monospace;
  color:var(--vi3);border:1px solid rgba(255,255,255,.05)}
.kbd{display:inline-flex;gap:4px;align-items:center}
.kbd code{background:rgba(255,255,255,.07);color:#ddd6fe;border-color:rgba(255,255,255,.1)}

table{width:100%;border-collapse:collapse;font-size:13.5px;margin:14px 0 4px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--fg3);font-weight:600;font-size:12.5px;letter-spacing:.3px}
tr:last-child td{border-bottom:0}
td:first-child{color:var(--fg)}

ul{margin:10px 0 0;padding-left:0;list-style:none}
li{position:relative;padding-left:22px;margin:9px 0;color:var(--fg2)}
li::before{content:"";position:absolute;left:6px;top:.72em;width:5px;height:5px;
  border-radius:50%;background:var(--vi);box-shadow:0 0 0 3px rgba(124,58,237,.18)}
li b{color:var(--fg)}

.mono{font-family:Consolas,"Cascadia Mono",monospace}
.foot{color:var(--fg3);font-size:12.5px;text-align:center;margin:36px 0 0}
</style></head><body><div class="wrap">

<div class="hero">
  <span class="mark">__I_BOOKMARK__</span>
  <h1>装一个书签就够了</h1>
</div>
<p class="sub">不用装扩展、不用装软件、不用管理员权限。<b>整个工具就是一个书签。</b></p>

<div class="step">
  <h2><span class="n">1</span>把书签栏打开</h2>
  <p>按 <span class="kbd"><code>Ctrl</code><code>Shift</code><code>B</code></span>。浏览器上方会多出一条横栏，那就是书签栏。</p>
  <div class="note ok">__I_CHECK__<span><b>看到浏览器上方出现一条横栏</b>（或者本来就有书签）—— 这一步就成了。</span></div>
</div>

<div class="step">
  <h2><span class="n">2</span>把下面这个紫色按钮拖到书签栏上</h2>
  <p>按住它别松手，拖到刚才那条横栏上，然后松手。</p>
  <p><a class="drag" href="__URL__" draggable="true" onclick="return false">__I_CLIPBOARD__写代码</a></p>
  <p>拖完之后，书签栏里会多出一个书签。<b>名字随便改</b>（双击它，或右键 → 修改），名字不影响功能。</p>
  <p style="color:var(--fg3);font-size:13px">拖动的时候鼠标要一直按着，拖到书签栏上再松手。松手早了会变成「打开这个链接」，那就再拖一次。</p>
  <div class="bar">
    <button id="cp">__I_COPY__拖不动？点这里复制</button>
    <span class="txt">复制后：<code>Ctrl</code>+<code>Shift</code>+<code>O</code> 打开书签管理器 → 右上「⋮」→ 添加新书签 → 名称随便填，<b>网址粘进去</b> → 保存</span>
  </div>
  <div class="note ok">__I_CHECK__<span>书签栏里出现了那个书签 —— <b>装完了，以后不用再回来这个页面</b>。</span></div>
</div>

<div class="step">
  <h2><span class="n">3</span>用：打开 PTA 题目 → 点书签 → 粘代码 → 回车</h2>
  <p>在 PTA 的编程题页面上，<b>点一下书签栏里那个书签</b>，会弹出一个紫色的面板。<br>
     把代码粘进面板里（<span class="kbd"><code>Ctrl</code><code>V</code></span>，这个面板是自己的，不禁粘贴），按 <span class="kbd"><code>Ctrl</code><code>Enter</code></span>。</p>
  <div class="note ok">__I_CHECK__<span>面板底部出现绿色的「<b>✓ 已写入 N 个字符</b>」，右边代码框里就是你的代码了，缩进和换行都对。</span></div>
  <div class="note stop">__I_ALERT__<span>它只往代码框里写字。<b>不会</b>点保存、<b>不会</b>点提交、<b>不会</b>点交卷。写完你自己看一眼，自己点「运行测试」和「提交本题作答」。</span></div>
</div>

<div class="step">
  <h2><span class="n">?</span>几个要知道的</h2>
  <ul>
    <li><b>为什么这个不算「粘贴」</b>：它直接用编辑器自己的接口把文字放进去（CodeMirror 的 <span class="mono">dispatch</span>），根本不产生粘贴事件。实测过：往这个代码框里派一个真的 <span class="mono">paste</span> 事件，PTA 会把它 <span class="mono">preventDefault</span> 掉、一个字都进不去 —— 所以只能走这条路。</li>
    <li><b>再点一次书签会关掉面板</b>，按 <code>Esc</code> 或点面板外的灰色区域也能关。</li>
    <li><b>会覆盖代码框里原有的内容</b>，不是往后追加 —— 想换一版就直接再写一次。</li>
    <li><b>只对能写代码的题有用</b>（函数题 / 编程题）。选择题、填空题点书签会提示「没找到代码框」。</li>
    <li><b>换电脑怎么办</b>：书签跟着浏览器账号同步（登录 Chrome / Edge 账号就会同步过去）；没同步就把这个页面拷过去再拖一次。</li>
  </ul>
  <table>
    <tr><th style="width:36%">你看到的</th><th>怎么办</th></tr>
    <tr><td>拖不动，或者拖上去没反应</td><td>用上面「拖不动？点这里复制」，然后照提示手动加一个书签</td></tr>
    <tr><td>点书签没任何反应</td><td>确认点的是<b>书签栏里的那个书签</b>，不是这个页面上的按钮</td></tr>
    <tr><td>提示「没找到代码框」</td><td>当前不是编程题，或者题目还在加载。等一秒再点</td></tr>
    <tr><td>提示「写进去了但读回来对不上」</td><td>自己看一眼右边代码框，缺什么补什么。这种情况很少见</td></tr>
  </table>
</div>

<div class="step" style="background:linear-gradient(180deg,#0f1119,#0c0e15)">
  <h2><span class="n">i</span>它到底是什么</h2>
  <p>一个「书签」而已。普通书签存的是网址，这个存的是<b>一小段代码</b>。点它的时候浏览器就在当前页面上执行这段代码 —— 所以你不需要装任何扩展，也不需要运行任何 exe。</p>
  <div class="note info">__I_SHIELD__<span>全部代码都在这个书签里，<b>不联网、不上传、不读你的题目、不碰别的网站</b>。图标来自 Lucide 开源图标库（ISC 许可），内联在页面里，不加载任何外部资源。</span></div>
</div>

<p class="foot">__I_SPARKLES__　书签面板的源码在 <span class="mono">书签工具.js</span>，可自行审阅</p>
<p class="foot" style="margin-top:10px">作者 <b style="color:var(--fg2)">ikunkun3</b> · <span class="mono">github.com/ikunkun3/pta-typer</span> · MIT 许可</p>

</div>
<script>
document.getElementById("cp").onclick = function () {
  var btn = this;
  var url = document.querySelector(".drag").getAttribute("href");
  function done(okText) {
    btn.className = "done";
    btn.innerHTML = okText;
  }
  function fallback() {
    var ta = document.createElement("textarea");
    ta.value = url;
    ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;left:-9999px;top:0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    if (ok) { done('\\u2713 已复制，去书签管理器新建一个'); }
    else {
      btn.className = "";
      btn.innerHTML = '请手动复制：点下面紫色按钮右键 → 复制链接地址';
    }
  }
  try {
    navigator.clipboard.writeText(url).then(function () {
      done('\\u2713 已复制，去书签管理器新建一个');
    }, fallback);
  } catch (e) { fallback(); }
};
</script>
</body></html>
"""


def build():
    code = minify(io.open(SRC, encoding="utf-8").read())
    url = "javascript:" + urllib.parse.quote("void(function(){" + code + "\n})()", safe="")
    html = HTML.replace("__URL__", url)
    for name in ICON:
        html = html.replace("__I_%s__" % name.upper(), _i(name, 18))
    # 图标尺寸微调：标题里的稍大、行内注释里的稍小
    html = html.replace('<span class="mark">' + _i("bookmark", 18),
                        '<span class="mark">' + _i("bookmark", 24))
    html = html.replace('<a class="drag" href="' + url + '" draggable="true" onclick="return false">'
                        + _i("clipboard", 18),
                        '<a class="drag" href="' + url + '" draggable="true" onclick="return false">'
                        + _i("clipboard", 19))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(html)
    print("源码 %d 字符 → 书签串 %d 字符" % (len(code), len(url)))
    print("%s  %d 字节" % (os.path.basename(OUT), len(html.encode("utf-8"))))
    left = re.findall(r"__I_[A-Z]+__", html)
    assert not left, "还有没替换的图标占位符: %s" % left


if __name__ == "__main__":
    build()
