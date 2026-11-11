// ==UserScript==
// @name         PTA 逐字输入（禁粘贴也能进）
// @author       ikunkun3 (@ikunkun3) — https://github.com/ikunkun3/pta-typer
// @namespace    pta-typer
// @version      1.1.0
// @description  把代码一个字符一个字符"打"进 PTA 的代码编辑器。全程不经过剪贴板，所以「禁止粘贴」拦不住。打开答题页面板会自己弹出。纯本地运行，不联网、不提交、不点任何按钮。
// @license      MIT
// @match        https://pintia.cn/*
// @match        https://www.pintia.cn/*
// @grant        GM_addStyle
// @run-at       document-idle
// ==/UserScript==

/*

怎么用
------
1. 打开 PTA 某道编程题的答题页（能看到代码编辑器那一页）。
2. 右下角点「逐字输入」打开面板。
3. 把代码粘进面板里那个大框（这个框是我们自己的，PTA 拦不到）。
4. 点「敲进去」。看着它自己一个字一个字打进去。
5. 打完自己去点「提交本题作答」——这个脚本**绝不会**替你点。

为什么「禁止粘贴」拦不住
------------------------
PTA 拦的是 paste 事件 + clipboardData。这个脚本压根不碰剪贴板：

  ① CodeMirror 6 的 view.dispatch()  —— 直接改编辑器自己的文档模型
  ② document.execCommand('insertText') —— 走浏览器自己的编辑管线
  ③ 原生 setter + 派发 input/change   —— 最土的兜底

三条路都不产生粘贴事件。注意副作用：**合成出来的键盘事件不会真的插入文字**
（浏览器对 isTrusted=false 的按键不执行默认行为），所以"模拟键盘"能做的只是
"看起来在敲"，真正把字放进去的是上面三条。因此本脚本默认不发假按键，
只把字一个一个字放进去——效果一样，还少一层可能出岔子的地方。


作者与许可
----------
作者：ikunkun3（@ikunkun3）
项目：https://github.com/ikunkun3/pta-typer
许可：MIT —— 转载 / 二次修改请保留本段署名。

*/

(function () {
  'use strict';

  // ============================ 常量 ============================

  var PANEL_ID = 'pta-typer';
  var STORE_KEY = 'pta_typer_cfg_v1';
  var LAST_KEY = 'pta_typer_last_v1';

  var DELAYS = [
    { label: '极快 (0ms)', v: 0 },
    { label: '快 (8ms)', v: 8 },
    { label: '正常 (30ms)', v: 30 },
    { label: '慢 (100ms)', v: 100 },
  ];

  // ============================ 小工具 ============================

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }
  function sleep(ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
  }
  function clean(s) {
    return String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
  }

  /**
   * 代码比对用的归一化。换行、不间断空格、行尾空白、末尾多余空行
   * 这几样在 DOM 里跟原文长得不一样，但它们不影响代码含义。
   */
  function normCode(s) {
    var t = String(s == null ? '' : s);
    t = t.replace(/\r\n?/g, '\n');
    t = t.replace(/[\u00a0\u2007\u202f]/g, ' ');
    t = t.split('\n').map(function (l) { return l.replace(/[ \t]+$/, ''); }).join('\n');
    t = t.replace(/\n{2,}$/, '\n');
    return t.replace(/^\n+/, '').replace(/\s+$/, '');
  }

  // ============================ 找编辑器 ============================

  /**
   * 找到"答题用的"那个编辑器。
   *
   * 真 PTA 页面上有 9~10 个 .cm-editor，只有一个在答题表单里。判据是
   * closest('[class*="AnswerForm"]')——注意那个 class 带构建哈希
   * （CodingProblemAnswerForm_JoDvx），只能用带 * 的子串匹配，不能写死。
   *
   * 绝对不能取"最后一个 contenteditable"：一打开「测试用例」面板，
   * 最后一个就变成面板里的输入框了，会把代码写到测试数据里去。
   */
  function findEditor() {
    var all = $$('.cm-content[contenteditable="true"]');
    var fallback = null;
    for (var i = 0; i < all.length; i++) {
      var c = all[i];
      if (c.closest('#' + PANEL_ID)) continue;
      if (c.getBoundingClientRect().width === 0) continue;
      if (c.closest('[class*="AnswerForm"]')) return c;   // 就是它
      if (!fallback) fallback = c;
    }
    if (fallback) return fallback;

    var ts = $$('textarea');
    for (var j = 0; j < ts.length; j++) {
      var t = ts[j];
      if (t.closest('#' + PANEL_ID)) continue;
      if (t.offsetParent === null) continue;
      return t;
    }
    return null;
  }

  /**
   * 取 CodeMirror 6 的 EditorView。
   *
   * 真 PTA 上它挂在 **.cm-content 元素的 cmTile.view** 上（实测：
   * Object.getOwnPropertyNames(el) 只有 ['cmTile']；el.cmView / el.cmProps 都不存在）。
   * 某些版本/自建场景在 .cmView.view 上，一并认。
   */
  function viewOf(c) {
    if (!c) return null;
    if (c.cmTile && c.cmTile.view) return c.cmTile.view;
    if (c.cmView && c.cmView.view) return c.cmView.view;
    return null;
  }

  /**
   * 读编辑器里当前的文字。
   * 有 CM view 就读文档模型（唯一真相）；没有才退到 DOM。
   * **不用 innerText** —— 它是渲染结果，white-space: normal 会把行首空格
   * 折叠掉，导致"内容明明对、比对却说错"。
   */
  function readEditor(c) {
    if (!c) return '';
    var v = viewOf(c);
    if (v) return v.state.doc.toString();
    if (typeof c.value === 'string') return c.value;
    return domText(c);
  }

  function domText(node) {
    var out = '';
    (function walk(n) {
      for (var i = 0; i < n.childNodes.length; i++) {
        var ch = n.childNodes[i];
        if (ch.nodeType === 3) { out += ch.nodeValue; continue; }
        if (ch.nodeType !== 1) continue;
        var tag = ch.tagName;
        if (tag === 'BR') { out += '\n'; continue; }
        if (tag === 'SCRIPT' || tag === 'STYLE') continue;
        var block = /^(DIV|P|LI|TR|PRE|BLOCKQUOTE)$/.test(tag);
        if (block && out && !/\n$/.test(out)) out += '\n';
        walk(ch);
        if (block && out && !/\n$/.test(out)) out += '\n';
      }
    })(node);
    return out.replace(/\n{3,}/g, '\n\n');
  }

  function selectAll(c) {
    var r = document.createRange();
    r.selectNodeContents(c);
    var s = window.getSelection();
    s.removeAllRanges();
    s.addRange(r);
  }

  function alive(c) {
    return !!(c && c.isConnected && document.contains(c));
  }

  // ============================ 三种写入法 ============================

  /** ① CodeMirror 6 事务：直接改文档模型，一次一个字符。 */
  async function typeByCM(c, code, delay, ctx) {
    var v = viewOf(c);
    if (!v) return { ok: false, how: 'cm', msg: '没有 EditorView' };

    c.focus();
    try {
      v.dispatch({ changes: { from: 0, to: v.state.doc.length, insert: '' } });
    } catch (e) {
      return { ok: false, how: 'cm', msg: '清空失败：' + e.message };
    }

    for (var i = 0; i < code.length; i++) {
      if (ctx.stop) return { ok: false, how: 'cm', msg: '已手动停止', stopped: true };
      var end = v.state.doc.length;
      try {
        v.dispatch({ changes: { from: end, to: end, insert: code[i] } });
      } catch (e) {
        return { ok: false, how: 'cm', msg: '第 ' + (i + 1) + ' 个字符写失败：' + e.message };
      }
      ctx.tick(i + 1, code.length);
      if (delay > 0) await sleep(delay);
      else if (i % 50 === 49) await sleep(0);
    }

    var got = v.state.doc.toString();
    return {
      ok: normCode(got) === normCode(code),
      how: 'cm',
      got: got,
      msg: '逐字符写入了 ' + code.length + ' 个字符',
    };
  }

  /**
   * ② execCommand：走浏览器自己的编辑管线（跟输入法/键盘最终落地是同一段代码），
   * 但不产生按键事件、不碰剪贴板。
   *
   * 两个实测的坑：
   *   1. execCommand('insertText', false, '\n') 返回 true 却什么都不插 → 换行必须走
   *      insertLineBreak（不行再退 insertParagraph）。
   *   2. 返回值不可信 → 一律靠调用方回读比对。
   */
  async function typeByExec(c, code, delay, ctx) {
    c.focus();
    selectAll(c);
    try { document.execCommand('delete'); } catch (e) { /* 空的就是空 */ }

    for (var i = 0; i < code.length; i++) {
      if (ctx.stop) return { ok: false, how: 'exec', msg: '已手动停止', stopped: true };
      var ch = code[i];
      try {
        if (ch === '\n') {
          if (!document.execCommand('insertLineBreak')) {
            document.execCommand('insertParagraph');
          }
        } else {
          document.execCommand('insertText', false, ch);
        }
      } catch (e) { /* 这一字符失败就跳过，最后靠回读判定 */ }
      ctx.tick(i + 1, code.length);
      if (delay > 0) await sleep(delay);
    }

    var got = readEditor(c);
    return {
      ok: normCode(got) === normCode(code),
      how: 'exec',
      got: got,
      msg: '逐字符写入了 ' + code.length + ' 个字符',
    };
  }

  /** ③ 最土的兜底：整个塞进去 + 派发 input/change。CodeMirror 不认，别的编辑器可能认。 */
  async function typeBySet(c, code) {
    c.focus();
    try {
      if (typeof c.value === 'string') {
        var proto = c.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        var desc = Object.getOwnPropertyDescriptor(proto, 'value');
        if (desc && desc.set) desc.set.call(c, code); else c.value = code;
      } else {
        c.textContent = code;
      }
      c.dispatchEvent(new Event('input', { bubbles: true }));
      c.dispatchEvent(new Event('change', { bubbles: true }));
    } catch (e) {
      return { ok: false, how: 'set', msg: '写入失败：' + e.message };
    }
    await sleep(60);
    var got = readEditor(c);
    return { ok: normCode(got) === normCode(code), how: 'set', got: got, msg: '整体塞入' };
  }

  // ============================ 主入口 ============================

  var running = false;
  var stopFlag = false;

  /**
   * 把 code 一个字一个字写进当前答题编辑器。
   * 返回 { ok, how, len, got, msg, trace }
   */
  async function typeCode(code, opts) {
    opts = opts || {};
    code = String(code == null ? '' : code).replace(/\r\n?/g, '\n');
    if (!code) return { ok: false, how: 'empty', msg: '没有内容' };
    if (opts.delayMs === undefined) opts.delayMs = 8;

    var trace = ['src=' + code.length];
    var c = opts.el || findEditor();
    if (!c) return { ok: false, how: 'no-editor', msg: '没找到代码编辑器，先确认自己在答题页', trace: trace };

    var ctx = {
      stop: false,
      tick: typeof opts.onTick === 'function' ? opts.onTick : function () {},
      getStopped: function () { return stopFlag; },
    };
    // 让 ctx.stop 跟着全局 stopFlag 走
    var iv = setInterval(function () { if (stopFlag) ctx.stop = true; }, 60);

    var res = null;
    try {
      if (viewOf(c)) {
        res = await typeByCM(c, code, opts.delayMs, ctx);
        trace.push('cm=' + normCode(res.got || '').length + (res.ok ? '/ok' : '/bad'));
      } else {
        trace.push('cm=none');
      }

      if (!res || !res.ok) {
        if (res && res.stopped) return res;
        if (!alive(c)) c = findEditor();
        if (c) {
          var r2 = await typeByExec(c, code, opts.delayMs, ctx);
          trace.push('exec=' + normCode(r2.got || '').length + (r2.ok ? '/ok' : '/bad'));
          if (r2.ok) res = r2; else if (r2.stopped) return r2;
        }
      }

      if (!res || !res.ok) {
        if (!alive(c)) c = findEditor();
        if (c) {
          var r3 = await typeBySet(c, code);
          trace.push('set=' + normCode(r3.got || '').length + (r3.ok ? '/ok' : '/bad'));
          if (r3.ok) res = r3;
        }
      }
    } finally {
      clearInterval(iv);
    }

    if (!res) res = { ok: false, how: 'failed', msg: '三条路都没走通' };
    res.len = code.length;
    res.trace = trace;
    if (!res.ok && !res.msg) res.msg = '写进去了但回读对不上';
    if (!res.ok && !res.stopped) {
      var gotLen = normCode(res.got || '').length;
      res.msg = '写进去 ' + gotLen + ' 字，原文 ' + code.length + ' 字，对不上';
    }
    return res;
  }

  // ============================ 面板 ============================

  var CSS = [
    '#' + PANEL_ID + '{position:fixed;right:18px;bottom:18px;width:360px;z-index:2147483000;',
    'font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;',
    'color:#111827;background:#fff;border:1px solid #d1d5db;border-radius:10px;',
    'box-shadow:0 8px 30px rgba(0,0,0,.18);display:none;flex-direction:column;overflow:hidden}',
    '#' + PANEL_ID + '.open{display:flex}',
    '#' + PANEL_ID + ' .hd{display:flex;align-items:center;justify-content:space-between;',
    'padding:8px 10px;background:#7c3aed;color:#fff;font-weight:600;font-size:12px;cursor:move}',
    '#' + PANEL_ID + ' .hd button{background:transparent;border:0;color:#fff;font-size:16px;',
    'line-height:1;cursor:pointer;padding:0 2px}',
    '#' + PANEL_ID + ' .bd{padding:10px;display:flex;flex-direction:column;gap:8px}',
    '#' + PANEL_ID + ' textarea{width:100%;box-sizing:border-box;height:150px;resize:vertical;',
    'font:12px/1.45 Consolas,Monaco,"Courier New",monospace;padding:8px;',
    'border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;color:#111827}',
    '#' + PANEL_ID + ' .row{display:flex;gap:6px;align-items:center}',
    '#' + PANEL_ID + ' .row.wrap{flex-wrap:wrap}',
    '#' + PANEL_ID + ' button.btn{padding:6px 12px;border-radius:6px;border:1px solid #d1d5db;',
    'background:#f3f4f6;color:#111827;cursor:pointer;font-size:12px}',
    '#' + PANEL_ID + ' button.btn:hover{background:#e5e7eb}',
    '#' + PANEL_ID + ' button.go{background:#7c3aed;border-color:#7c3aed;color:#fff;font-weight:600}',
    '#' + PANEL_ID + ' button.go:hover{background:#6d28d9}',
    '#' + PANEL_ID + ' button.stop{background:#dc2626;border-color:#dc2626;color:#fff}',
    '#' + PANEL_ID + ' button.stop:hover{background:#b91c1c}',
    '#' + PANEL_ID + ' button.btn:disabled{opacity:.45;cursor:not-allowed}',
    '#' + PANEL_ID + ' select{padding:5px 6px;border:1px solid #d1d5db;border-radius:6px;',
    'background:#f9fafb;font-size:12px;color:#111827}',
    '#' + PANEL_ID + ' .stat{font-size:12px;color:#4b5563;min-height:18px}',
    '#' + PANEL_ID + ' .stat.err{color:#dc2626}',
    '#' + PANEL_ID + ' .stat.ok{color:#059669}',
    '#' + PANEL_ID + ' .bar{height:4px;background:#e5e7eb;border-radius:2px;overflow:hidden}',
    '#' + PANEL_ID + ' .bar > i{display:block;height:100%;width:0;background:#7c3aed;',
    'transition:width .08s linear}',
    '#' + PANEL_ID + ' .tip{font-size:11px;color:#6b7280;line-height:1.6}',
    '#' + PANEL_ID + ' .tip b{color:#7c3aed}',
    '#pta-typer-fab{position:fixed;right:18px;bottom:18px;z-index:2147482999;',
    'padding:8px 14px;border-radius:20px;border:0;background:#7c3aed;color:#fff;',
    'font:600 13px/1 -apple-system,"Microsoft YaHei",sans-serif;cursor:pointer;',
    'box-shadow:0 4px 14px rgba(124,58,237,.45)}',
    '#pta-typer-fab.hide{display:none}',
  ].join('');

  var el = {};
  var userClosed = false;   // 用户手动点过 × 之后，本页不再自己弹

  function addStyle(css) {
    try {
      if (typeof GM_addStyle === 'function') { GM_addStyle(css); return; }
    } catch (e) { /* 往下走 */ }
    var s = document.createElement('style');
    s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
  }

  function loadCfg() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        var o = JSON.parse(raw);
        return { delay: Number(o.delay) || 0 };
      }
    } catch (e) { /* ignore */ }
    return { delay: 8 };
  }

  function saveCfg(cfg) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(cfg)); } catch (e) { /* ignore */ }
  }

  function setStat(text, kind) {
    if (!el.stat) return;
    el.stat.textContent = text || '';
    el.stat.className = 'stat' + (kind ? ' ' + kind : '');
  }

  function setProgress(cur, total) {
    if (!el.bar) return;
    var p = total ? Math.min(100, Math.round((cur / total) * 100)) : 0;
    el.bar.style.width = p + '%';
  }

  function setBusy(b) {
    if (el.go) el.go.disabled = b;
    if (el.stop) el.stop.disabled = !b;
  }

  /**
   * 我们自己的面板里的粘贴要能正常用。
   * PTA 的禁粘贴可能是挂在 document 上的捕获监听——那样连我们这个框也会被
   * preventDefault 掉。所以在面板上自己接管 paste：读到文本、自己插进光标处。
   */
  function ownPaste(e) {
    var ta = el.ta;
    if (!ta) return;
    var t = '';
    try {
      t = (e.clipboardData || window.clipboardData).getData('text') || '';
    } catch (err) { t = ''; }
    if (!t) return;
    e.preventDefault();
    e.stopPropagation();
    insertAtCaret(ta, t);
  }

  function insertAtCaret(ta, text) {
    var s = ta.selectionStart;
    var en = ta.selectionEnd;
    var v = ta.value;
    ta.value = v.slice(0, s) + text + v.slice(en);
    var pos = s + text.length;
    ta.selectionStart = ta.selectionEnd = pos;
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  }

  async function run() {
    if (running) return;
    var code = el.ta.value;
    if (!clean(code)) { setStat('框里是空的，先粘代码进来', 'err'); return; }

    var cfg = { delay: Number(el.delay.value) || 0 };
    saveCfg(cfg);
    try { localStorage.setItem(LAST_KEY, code); } catch (e) { /* ignore */ }

    running = true;
    stopFlag = false;
    setBusy(true);
    setProgress(0, code.length);
    setStat('开始，共 ' + code.length + ' 个字符…');

    var t0 = Date.now();
    var res;
    try {
      res = await typeCode(code, {
        delayMs: cfg.delay,
        onTick: function (i, total) {
          setProgress(i, total);
          if (i % 200 === 0) setStat('已写入 ' + i + ' / ' + total + ' 个字符…');
        },
      });
    } catch (e) {
      res = { ok: false, how: 'crash', msg: '出错：' + (e && e.message) };
    } finally {
      running = false;
      setBusy(false);
      setProgress(0, 0);
    }

    var secs = ((Date.now() - t0) / 1000).toFixed(1);
    if (res.ok) {
      setStat('✅ ' + res.len + ' 个字符全部写入（' + res.how + ' 路线 · ' + secs + 's）· 未点任何按钮', 'ok');
    } else if (res.stopped) {
      setStat('⏹ 已停止 · ' + secs + 's', 'err');
    } else {
      setStat('❌ ' + (res.msg || '失败') + (res.trace ? '  [' + res.trace.join(' ') + ']' : ''), 'err');
      // 失败时把原文打到控制台，方便手动复制
      try { console.log('[pta-typer] 没敲进去，原文如下：\n' + code); } catch (e) { /* ignore */ }
    }
  }

  function buildPanel() {
    if (document.getElementById(PANEL_ID)) return;

    var fab = document.createElement('button');
    fab.id = 'pta-typer-fab';
    fab.textContent = '⌨ 逐字输入';
    document.body.appendChild(fab);

    var wrap = document.createElement('div');
    wrap.id = PANEL_ID;
    wrap.innerHTML =
      '<div class="hd"><span>⌨ PTA 逐字输入</span><button class="close" title="收起">×</button></div>' +
      '<div class="bd">' +
        '<textarea spellcheck="false" placeholder="把代码粘到这里（这个框是我们自己的，PTA 拦不到）"></textarea>' +
        '<div class="row wrap">' +
          '<select class="delay"></select>' +
          '<button class="btn go">敲进去</button>' +
          '<button class="btn stop" disabled>停止</button>' +
          '<button class="btn read">读一下</button>' +
          '<button class="btn clear">清空</button>' +
        '</div>' +
        '<div class="bar"><i></i></div>' +
        '<div class="stat"></div>' +
        '<div class="tip">只写字，<b>不会</b>点提交 / 保存 / 交卷。写完自己去点提交。<br>' +
          '快捷键：面板里 <b>Ctrl+Enter</b> 开始。</div>' +
      '</div>';
    document.body.appendChild(wrap);

    el.wrap = wrap;
    el.fab = fab;
    el.ta = $('textarea', wrap);
    el.delay = $('.delay', wrap);
    el.go = $('.go', wrap);
    el.stop = $('.stop', wrap);
    el.read = $('.read', wrap);
    el.clear = $('.clear', wrap);
    el.stat = $('.stat', wrap);
    el.bar = $('.bar > i', wrap);

    // 间隔下拉
    var cfg = loadCfg();
    var picked = false;
    DELAYS.forEach(function (d) {
      var o = document.createElement('option');
      o.value = String(d.v);
      o.textContent = d.label;
      if (!picked && d.v === cfg.delay) { o.selected = true; picked = true; }
      el.delay.appendChild(o);
    });
    if (!picked) el.delay.value = '8';

    // 上次的内容
    try {
      var last = localStorage.getItem(LAST_KEY);
      if (last) el.ta.value = last;
    } catch (e) { /* ignore */ }

    /**
     * 面板自己弹出来，省掉「找按钮」这一步。
     * PTA 是 React Router，切题不刷新页面，所以用轮询而不是只听 load：
     * 只要页面上出现了答题编辑器、面板又被关着，就弹出来。
     * 用户手动点过 × 之后就不弹了（本页内），点右下角按钮能再叫出来。
     */
    function watchEditor() {
      var opened = false;
      setInterval(function () {
        if (opened || userClosed) return;
        if (el.wrap.classList.contains('open')) { opened = true; return; }
        if (!findEditor()) return;
        opened = true;
        el.open();
        setStat('已就绪 · 把代码粘进来，点「敲进去」');
      }, 700);
    }

    el.open = function () {
      wrap.classList.add('open');
      fab.classList.add('hide');
    };
    el.close = function () {
      wrap.classList.remove('open');
      fab.classList.remove('hide');
    };

    fab.onclick = function () {
      userClosed = false;
      el.open();
      el.ta.focus();
    };
    $('.close', wrap).onclick = function () {
      userClosed = true;
      el.close();
    };

    watchEditor();

    el.go.onclick = run;
    el.stop.onclick = function () {
      stopFlag = true;
      setStat('正在停止…', 'err');
    };
    el.read.onclick = function () {
      var c = findEditor();
      if (!c) { setStat('没找到编辑器', 'err'); return; }
      var t = readEditor(c);
      var v = viewOf(c);
      setStat('当前编辑器 ' + t.length + ' 字符（' + (v ? 'CM view' : '纯 DOM') + '）：' +
        JSON.stringify(t.slice(0, 60)));
    };
    el.clear.onclick = function () { el.ta.value = ''; setStat(''); setProgress(0, 0); };

    el.ta.addEventListener('paste', ownPaste, true);
    el.ta.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        run();
      }
    });

    // 拖动
    (function drag() {
      var hd = $('.hd', wrap);
      var dragging = false, sx = 0, sy = 0, ox = 0, oy = 0;
      hd.addEventListener('mousedown', function (e) {
        if (e.target.tagName === 'BUTTON') return;
        dragging = true;
        var r = wrap.getBoundingClientRect();
        wrap.style.left = r.left + 'px';
        wrap.style.top = r.top + 'px';
        wrap.style.right = 'auto';
        wrap.style.bottom = 'auto';
        sx = e.clientX; sy = e.clientY; ox = r.left; oy = r.top;
        e.preventDefault();
      });
      document.addEventListener('mousemove', function (e) {
        if (!dragging) return;
        wrap.style.left = (ox + e.clientX - sx) + 'px';
        wrap.style.top = (oy + e.clientY - sy) + 'px';
      });
      document.addEventListener('mouseup', function () { dragging = false; });
    })();

    setStat('点「敲进去」开始。');
  }

  // ============================ 启动 ============================

  function boot() {
    addStyle(CSS);
    if (document.body) buildPanel();
    else document.addEventListener('DOMContentLoaded', buildPanel, { once: true });
  }

  // 暴露给离线测试用
  window.__PTA_TYPER__ = {
    findEditor: findEditor,
    viewOf: viewOf,
    readEditor: readEditor,
    domText: domText,
    normCode: normCode,
    typeCode: typeCode,
    typeByCM: typeByCM,
    typeByExec: typeByExec,
    typeBySet: typeBySet,
    insertAtCaret: insertAtCaret,
    DELAYS: DELAYS,
  };

  boot();
})();
