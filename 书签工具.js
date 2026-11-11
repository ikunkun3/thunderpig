// PTA 逐字输入 —— 书签小工具（bookmarklet）
// 作者：ikunkun3（@ikunkun3）  https://github.com/ikunkun3/thunderpig
// 许可：MIT —— 转载 / 二次修改请保留本段署名。
// 用法：在 PTA 编程题页面点一下这个书签，弹框，粘代码，Ctrl+Enter。
// 不装扩展、不联网、不碰剪贴板事件、不点任何按钮。
// 图标来自 Lucide（ISC 许可），内联成 SVG path，不加载任何外部资源。
(function () {
  'use strict';

  var ID = 'pta-bm';

  // 再点一次书签 = 关掉浮层
  var prev = document.getElementById(ID);
  if (prev) { prev.parentNode.removeChild(prev); return; }

  // Lucide 图标（https://lucide.dev，ISC）：只取 path/line/rect，包一层 svg
  var P = {
    paste: '<path d="M11 14h10"/><path d="M16 4h2a2 2 0 0 1 2 2v1.344"/>'
      + '<path d="m17 18 4-4-4-4"/><path d="M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2'
      + 'h12a2 2 0 0 0 1.793-1.113"/><rect x="8" y="2" width="8" height="4" rx="1"/>',
    close: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    ok: '<circle cx="12" cy="12" r="10"/><path d="m16 9-5.5 5.5L8 12"/>',
    bad: '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/>'
      + '<line x1="12" x2="12.01" y1="16" y2="16"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    key: '<path d="M10 8h.01"/><path d="M12 12h.01"/><path d="M14 8h.01"/><path d="M16 12h.01"/>'
      + '<path d="M18 8h.01"/><path d="M6 8h.01"/><path d="M7 16h10"/><path d="M8 12h.01"/>'
      + '<rect width="20" height="16" x="2" y="4" rx="2"/>'
  };
  function svg(d, size) {
    return '<svg viewBox="0 0 24 24" width="' + size + '" height="' + size + '" fill="none" '
      + 'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
      + 'aria-hidden="true">' + d + '</svg>';
  }

  var CSS = [
    '#pta-bm{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;',
    'justify-content:center;background:rgba(8,8,14,.66);-webkit-backdrop-filter:blur(7px);',
    'backdrop-filter:blur(7px);animation:pta-bm-in .16s ease-out}',

    '#pta-bm .box{position:relative;width:780px;max-width:92vw;overflow:hidden;',
    'background:linear-gradient(180deg,#201748 0%,#160f30 62%,#120c28 100%);',
    'border:1px solid rgba(139,92,246,.42);border-radius:18px;',
    'box-shadow:0 32px 80px -12px rgba(0,0,0,.8),0 0 0 1px rgba(255,255,255,.04) inset,',
    '0 1px 0 rgba(255,255,255,.09) inset;',
    'font:14px/1.62 "Microsoft YaHei",system-ui,-apple-system,sans-serif;color:#ece7ff;',
    'animation:pta-bm-pop .18s cubic-bezier(.2,.9,.3,1.1)}',
    '#pta-bm .box::before{content:"";position:absolute;left:0;right:0;top:0;height:2px;',
    'background:linear-gradient(90deg,#7c3aed,#a78bfa 42%,#22d3ee 100%);opacity:.95}',

    '#pta-bm .hd{display:flex;align-items:center;gap:11px;padding:15px 15px 12px 16px}',
    '#pta-bm .ico{display:flex;align-items:center;justify-content:center;flex:0 0 36px;',
    'width:36px;height:36px;border-radius:11px;color:#fff;',
    'background:linear-gradient(145deg,#8b5cf6,#6d28d9);',
    'box-shadow:0 6px 16px -4px rgba(124,58,237,.75),0 1px 0 rgba(255,255,255,.28) inset}',
    '#pta-bm .ttl{flex:1;min-width:0}',
    '#pta-bm .ttl b{display:block;font-size:15px;line-height:1.3;font-weight:600;',
    'letter-spacing:.2px;color:#f4f0ff}',
    '#pta-bm .ttl i{display:block;font-style:normal;font-size:11.5px;line-height:1.4;',
    'color:#9b93c4;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',

    '#pta-bm .x{display:flex;align-items:center;justify-content:center;flex:0 0 30px;',
    'width:30px;height:30px;padding:0;border:0;border-radius:9px;cursor:pointer;',
    'background:rgba(255,255,255,.05);color:#b9b1de;transition:background .14s,color .14s}',
    '#pta-bm .x:hover{background:rgba(255,255,255,.12);color:#fff}',

    '#pta-bm textarea{display:block;width:calc(100% - 32px);margin:0 16px;height:40vh;',
    'min-height:180px;box-sizing:border-box;padding:12px 13px;resize:vertical;outline:none;',
    'background:#0a0c12;color:#c9bbff;border:1px solid #362a63;border-radius:12px;',
    'font:13px/1.62 Consolas,"Cascadia Mono",monospace;',
    'box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 10px 26px -18px #000 inset;',
    'transition:border-color .14s,box-shadow .14s}',
    '#pta-bm textarea::placeholder{color:#635c86}',
    '#pta-bm textarea:focus{border-color:#8b5cf6;',
    'box-shadow:0 0 0 3px rgba(124,58,237,.22),0 10px 26px -18px #000 inset}',

    '#pta-bm .row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:12px 16px 0}',
    '#pta-bm button{font:inherit}',
    '#pta-bm .go{display:inline-flex;align-items:center;gap:7px;border:0;cursor:pointer;',
    'padding:9px 17px 9px 14px;border-radius:10px;font-size:14px;font-weight:600;color:#fff;',
    'background:linear-gradient(180deg,#8b5cf6,#7134e0);',
    'box-shadow:0 6px 16px -6px rgba(124,58,237,.9),0 1px 0 rgba(255,255,255,.3) inset;',
    'transition:transform .1s,box-shadow .14s,filter .14s}',
    '#pta-bm .go:hover{filter:brightness(1.08);box-shadow:0 8px 22px -6px rgba(124,58,237,1),',
    '0 1px 0 rgba(255,255,255,.32) inset}',
    '#pta-bm .go:active{transform:translateY(1px)}',
    '#pta-bm .go svg{opacity:.95}',

    '#pta-bm .kbd{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;',
    'border-radius:8px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.08);',
    'color:#a9a1cf;font-size:11.5px;white-space:nowrap}',
    '#pta-bm .kbd code{font:11.5px Consolas,monospace;color:#d6ccff}',
    '#pta-bm .hint{color:#7b749c;font-size:11.5px;margin-left:auto;white-space:nowrap}',

    '#pta-bm .st{display:flex;align-items:center;gap:7px;margin:10px 16px 14px;padding:9px 12px;',
    'border-radius:10px;font-size:12px;line-height:1.5;color:#a49cc6;',
    'background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);',
    'transition:color .14s,background .14s,border-color .14s}',
    '#pta-bm .st svg{flex:0 0 15px;width:15px;height:15px}',
    '#pta-bm .stx{min-width:0}',
    '#pta-bm .st.ok{color:#6ee7b7;background:rgba(16,185,129,.11);border-color:rgba(16,185,129,.3)}',
    '#pta-bm .st.bad{color:#fca5a5;background:rgba(239,68,68,.11);border-color:rgba(239,68,68,.3)}',
    '#pta-bm .crd{padding:0 16px 12px;font-size:11px;color:#5e5880;letter-spacing:.2px}',
    '#pta-bm .crd b{color:#8b83b5;font-weight:600}',

    '@keyframes pta-bm-in{from{opacity:0}to{opacity:1}}',
    '@keyframes pta-bm-pop{from{opacity:0;transform:translateY(10px) scale(.985)}',
    'to{opacity:1;transform:none}}',
    '@media (prefers-reduced-motion:reduce){#pta-bm,#pta-bm .box{animation:none}}'
  ].join('');

  // 反复点书签会重复注入，样式只留一份
  if (!document.getElementById('pta-bm-style')) {
    var style = document.createElement('style');
    style.id = 'pta-bm-style';
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  var wrap = document.createElement('div');
  wrap.id = ID;
  wrap.setAttribute('role', 'dialog');
  wrap.setAttribute('aria-label', '把代码写进 PTA 代码框');
  wrap.innerHTML = '<div class="box">'
    + '<div class="hd"><span class="ico">' + svg(P.paste, 19) + '</span>'
    + '<div class="ttl"><b>PTA 逐字输入</b><i>把代码粘进来，它替你一个字一个字写进去</i></div>'
    + '<button class="x" type="button" title="关闭（Esc）">' + svg(P.close, 16) + '</button></div>'
    + '<textarea spellcheck="false" placeholder="把代码粘到这里（Ctrl+V），然后按 Ctrl+Enter"></textarea>'
    + '<div class="row"><button class="go" type="button">' + svg(P.paste, 15) + '写进代码框</button>'
    + '<span class="kbd">' + svg(P.key, 13) + '<code>Ctrl</code>+<code>Enter</code></span>'
    + '<span class="hint">只写字，不点保存、不点提交</span></div>'
    + '<div class="st"><span class="sic">' + svg(P.info, 15) + '</span>'
    + '<span class="stx">粘完按 Ctrl+Enter 直接写</span></div>'
    + '<div class="crd">by <b>@ikunkun3</b> · MIT · github.com/ikunkun3/thunderpig</div>'
    + '</div>';
  document.body.appendChild(wrap);

  var ta = wrap.querySelector('textarea');
  var status = wrap.querySelector('.st');
  var statusIco = wrap.querySelector('.sic');
  var statusTxt = wrap.querySelector('.stx');

  function say(text, cls) {
    statusTxt.textContent = text;
    status.className = 'st' + (cls ? ' ' + cls : '');
    statusIco.innerHTML = svg(cls === 'ok' ? P.ok : cls === 'bad' ? P.bad : P.info, 15);
  }

  function close() { if (wrap.parentNode) wrap.parentNode.removeChild(wrap); }

  // 页面上有十来个 .cm-editor，只有答题区在 *AnswerForm* 里面。
  // 绝不能取"最后一个 contenteditable" —— 打开「测试用例」面板后最后一个变成面板里的输入框。
  // 也绝不能"取第一个能用的"兜底 —— 测试用例面板里的输入框会顶上来，
  // 结果是代码写进了测试数据里，用户以为写对了。宁可报"没找到"。
  function findEditor() {
    var all = [].slice.call(document.querySelectorAll('.cm-content[contenteditable="true"]'));
    for (var i = 0; i < all.length; i++) {
      var c = all[i];
      if (c.closest('#' + ID)) continue;
      if (!c.getBoundingClientRect().width) continue;
      if (c.closest('[class*="AnswerForm"]')) return c;
    }
    // 没有 CodeMirror 的旧版式：只在答题表单里找 textarea
    var areas = [].slice.call(document.querySelectorAll('[class*="AnswerForm"] textarea'));
    for (var j = 0; j < areas.length; j++) {
      if (!areas[j].closest('#' + ID)) return areas[j];
    }
    return null;
  }

  // 真 PTA 的 EditorView 挂在 cmTile.view 上（不是 cmView）
  function viewOf(c) {
    if (c.cmTile && c.cmTile.view) return c.cmTile.view;
    if (c.cmView && c.cmView.view) return c.cmView.view;
    return null;
  }

  // contenteditable 的兜底：逐行 execCommand，换行必须走 insertLineBreak。
  // 末尾的空行不要自己补 —— 编辑器本来就会留一个结尾换行，再补就多一个。
  function writeByExec(c, code) {
    c.focus();
    execute('selectAll');
    document.execCommand('delete', false, null);
    var lines = code.split('\n');
    while (lines.length > 1 && lines[lines.length - 1] === '') lines.pop();
    for (var i = 0; i < lines.length; i++) {
      if (i) {
        if (!document.execCommand('insertLineBreak', false, null)) {
          document.execCommand('insertParagraph', false, null);
        }
      }
      if (lines[i]) document.execCommand('insertText', false, lines[i]);
    }
    c.dispatchEvent(new Event('input', { bubbles: true }));
    // contenteditable 不保留文件末尾的换行，而用户代码常常以换行结尾。
    // 末尾空行对判题没影响，比对时两边都过 norm() 抹平，别在这里硬凑。
    return c.textContent || '';
  }

  function execute(cmd) {
    try { document.execCommand(cmd, false, null); } catch (e) { /* 无所谓 */ }
  }

  // 比对用：去掉 \r、把不换行空格还原、去行尾空白、去末尾多余空行
  function norm(s) {
    return String(s || '')
      .replace(/\r\n?/g, '\n')
      .replace(/[\u00a0\u2007\u202f]/g, ' ')
      .split('\n').map(function (l) { return l.replace(/\s+$/, ''); })
      .join('\n').replace(/\n{2,}$/, '\n').replace(/^\n+|\n+$/g, '');
  }

  function write(code) {
    code = String(code || '').replace(/\r\n?/g, '\n');
    if (!code.trim()) { say('框里是空的', 'bad'); return; }

    var c = findEditor();
    if (!c) { say('没找到代码框 —— 先打开一道编程题（函数题）', 'bad'); return; }

    var view = viewOf(c);
    if (view) {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: code } });
      var got = view.state.doc.toString();
      if (norm(got) === norm(code)) {
        say('✓ 已写入 ' + code.length + ' 个字符（CodeMirror）', 'ok');
        return;
      }
    }

    var dom = writeByExec(c, code);
    if (norm(dom) === norm(code)) {
      say('✓ 已写入 ' + code.length + ' 个字符（编辑器兜底）', 'ok');
      return;
    }
    say('写进去了但读回来对不上，请自己看一眼代码框（' + norm(dom).length + '/' + norm(code).length + '）', 'bad');
  }

  wrap.querySelector('.go').onclick = function () { write(ta.value); };
  wrap.querySelector('.x').onclick = close;
  wrap.onclick = function (e) { if (e.target === wrap) close(); };

  ta.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      write(ta.value);
    }
  });

  document.addEventListener('keydown', function esc(e) {
    if (e.key === 'Escape' && wrap.parentNode) {
      document.removeEventListener('keydown', esc);
      close();
    }
  });

  ta.focus();
})();
