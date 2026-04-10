#!/usr/bin/env python3
"""
《解密 Claude Code》HTML 构建脚本
每章生成独立页面，左侧固定目录 + 右侧章节内容
"""

import re, os, sys, html as H, shutil

# ── 章节列表 ────────────────────────────────────────────────

CHAPTERS = [
    ("cover",      "cover.md",      "封面"),
    ("preface",    "preface.md",    "前言"),
    ("ch01",       "chapter01.md",  "第1章 欢迎来到 Claude Code 的世界"),
    ("ch02",       "chapter02.md",  "第2章 源码全景地图"),
    ("ch03",       "chapter03.md",  "第3章 从零理解 TypeScript 与 React"),
    ("ch04",       "chapter04.md",  "第4章 程序的大门——入口文件解析"),
    ("ch05",       "chapter05.md",  "第5章 终端里的 React——Ink 框架揭秘"),
    ("ch06",       "chapter06.md",  "第6章 状态管理——程序的\u201c记忆\u201d"),
    ("ch07",       "chapter07.md",  "第7章 命令系统——斜杠的魔法"),
    ("ch08",       "chapter08.md",  "第8章 与 AI 对话的秘密——消息系统"),
    ("ch09",       "chapter09.md",  "第9章 查询引擎——大脑中枢"),
    ("ch10",       "chapter10.md",  "第10章 流式响应——逐字显示的魔法"),
    ("ch11",       "chapter11.md",  "第11章 上下文管理——有限的记忆"),
    ("ch12",       "chapter12.md",  "第12章 工具的世界——从设计到实现"),
    ("ch13",       "chapter13.md",  "第13章 Bash 工具——最强大也最危险"),
    ("ch14",       "chapter14.md",  "第14章 文件三剑客——Read、Write、Edit"),
    ("ch15",       "chapter15.md",  "第15章 搜索双雄——Grep 与 Glob"),
    ("ch16",       "chapter16.md",  "第16章 Agent 工具——AI 的分身术"),
    ("ch17",       "chapter17.md",  "第17章 权限系统——信任的层级"),
    ("ch18",       "chapter18.md",  "第18章 安全防线——危险命令检测"),
    ("ch19",       "chapter19.md",  "第19章 沙箱机制——隔离的艺术"),
    ("ch20",       "chapter20.md",  "第20章 MCP 协议——工具的万能接口"),
    ("ch21",       "chapter21.md",  "第21章 Hook 系统——可编程的钩子"),
    ("ch22",       "chapter22.md",  "第22章 IDE 桥接——编辑器中的 AI"),
    ("ch23",       "chapter23.md",  "第23章 插件与技能——无限扩展"),
    ("ch24",       "chapter24.md",  "第24章 多智能体——AI 的团队协作"),
    ("ch25",       "chapter25.md",  "第25章 性能优化——毫秒必争"),
    ("ch26",       "chapter26.md",  "第26章 持久化记忆——跨会话的智慧"),
    ("ch27",       "chapter27.md",  "第27章 配置系统——千人千面"),
    ("ch28",       "chapter28.md",  "第28章 架构之美——设计模式总结"),
    ("ch29",       "chapter29.md",  "第29章 从源码到产品——工程实践启示"),
    ("ch30",       "chapter30.md",  "第30章 你的下一步——成为更好的程序员"),
    ("appendix-a", "appendix-a.md", "附录 A 术语表"),
    ("appendix-b", "appendix-b.md", "附录 B 源码关键文件索引"),
    ("appendix-c", "appendix-c.md", "附录 C 全书知识地图"),
    ("about",      "about-author.md", "关于本书"),
]

TOC_GROUPS = [
    (None, ["cover", "preface"]),
    ("第一部分 起步篇", ["ch01", "ch02", "ch03"]),
    ("第二部分 核心架构篇", ["ch04", "ch05", "ch06", "ch07"]),
    ("第三部分 对话引擎篇", ["ch08", "ch09", "ch10", "ch11"]),
    ("第四部分 工具系统篇", ["ch12", "ch13", "ch14", "ch15", "ch16"]),
    ("第五部分 安全与权限篇", ["ch17", "ch18", "ch19"]),
    ("第六部分 扩展与集成篇", ["ch20", "ch21", "ch22", "ch23"]),
    ("第七部分 高级话题篇", ["ch24", "ch25", "ch26", "ch27"]),
    ("第八部分 总结篇", ["ch28", "ch29", "ch30"]),
    ("附录", ["appendix-a", "appendix-b", "appendix-c", "about"]),
]

# ── Markdown → HTML ─────────────────────────────────────────

def inline(s):
    s = H.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    return s

def md_to_html(text, sid):
    lines = text.split("\n")
    out, hcount = [], 0
    in_code = in_table = in_list = False
    list_tag = None

    def _close_list():
        nonlocal in_list, list_tag
        if in_list: out.append(f"</{list_tag}>"); in_list = False; list_tag = None
    def _close_table():
        nonlocal in_table
        if in_table: out.append("</tbody></table>"); in_table = False

    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            _close_list(); _close_table()
            if in_code: out.append("</code></pre>"); in_code = False
            else:
                lang = s[3:].strip()
                c = f' class="language-{lang}"' if lang else ""
                out.append(f"<pre><code{c}>"); in_code = True
            continue
        if in_code: out.append(H.escape(line)); continue
        if re.match(r"^\|[\s\-:|]+\|$", s): continue
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if not in_table:
                _close_list()
                out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue
        else: _close_table()
        m = re.match(r"^(#{1,4})\s+(.+)$", s)
        if m:
            _close_list(); lv = len(m.group(1)); hcount += 1
            out.append(f'<h{lv} id="{sid}-h{hcount}">{inline(m.group(2))}</h{lv}>'); continue
        if s in ("---", "***"): _close_list(); out.append("<hr/>"); continue
        if s.startswith("> "): _close_list(); out.append(f"<blockquote><p>{inline(s[2:])}</p></blockquote>"); continue
        if re.match(r"^[-*]\s", s):
            if not in_list or list_tag != "ul": _close_list(); out.append("<ul>"); in_list = True; list_tag = "ul"
            out.append(f"<li>{inline(re.sub(r'^[-*]\\s+', '', s))}</li>"); continue
        if re.match(r"^\d+\.\s", s):
            if not in_list or list_tag != "ol": _close_list(); out.append("<ol>"); in_list = True; list_tag = "ol"
            out.append(f"<li>{inline(re.sub(r'^\\d+\\.\\s+', '', s))}</li>"); continue
        if s == "": _close_list(); out.append(""); continue
        # HTML 标签直通（如 <div>, <img>, <br/>, </div> 等）
        if re.match(r"^</?[a-zA-Z][\s\S]*>$", s):
            _close_list(); out.append(s); continue
        _close_list(); out.append(f"<p>{inline(s)}</p>")
    _close_list(); _close_table()
    if in_code: out.append("</code></pre>")
    return "\n".join(out)

# ── 侧边栏 HTML ─────────────────────────────────────────────

def build_sidebar(active_id, chapters_map):
    parts = []
    for group_name, ids in TOC_GROUPS:
        if group_name:
            parts.append(f'<div class="toc-group">{H.escape(group_name)}</div>')
        for cid in ids:
            if cid not in chapters_map: continue
            title = chapters_map[cid]
            cls = "toc-item active" if cid == active_id else "toc-item"
            # data-cid 用于 JS 标记已读
            parts.append(
                f'<a class="{cls}" href="{cid}.html" data-cid="{cid}">'
                f'<span class="read-dot" data-cid="{cid}"></span>'
                f'{H.escape(title)}</a>'
            )
    return "\n".join(parts)

# ── 页面模板 ─────────────────────────────────────────────────

PAGE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title} - 解密 Claude Code</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4EGRH2BGC6"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-4EGRH2BGC6');
</script>
<style>
:root {{
  --sidebar-w:300px; --bg:#101418; --bg-side:#141a1e; --fg:#d4dde0;
  --fg-dim:#8899a6; --accent:#00d4ff; --accent2:#20b2aa;
  --code-bg:#181e24; --border:#283038; --hover:#1c2428; --radius:6px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
  background:var(--bg);color:var(--fg);line-height:1.85;font-size:15px;
}}

/* ── 布局 ── */
.layout{{display:flex;min-height:100vh}}
.sidebar{{
  position:fixed;top:0;left:0;width:var(--sidebar-w);height:100vh;
  background:var(--bg-side);border-right:1px solid var(--border);
  overflow-y:auto;z-index:100;display:flex;flex-direction:column;
}}
.sidebar-header{{padding:1.4rem 1.2rem .8rem;border-bottom:1px solid var(--border);flex-shrink:0}}
.sidebar-header h1{{font-size:1.05rem;color:var(--accent);margin:0;font-weight:700}}
.sidebar-header p{{font-size:.72rem;color:var(--fg-dim);margin-top:.25rem}}
.sidebar-search{{padding:.7rem 1.2rem;border-bottom:1px solid var(--border);flex-shrink:0}}
.sidebar-search input{{
  width:100%;padding:.4rem .7rem;background:var(--code-bg);
  border:1px solid var(--border);border-radius:var(--radius);
  color:var(--fg);font-size:.8rem;outline:none;
}}
.sidebar-search input:focus{{border-color:var(--accent)}}
.sidebar-search input::placeholder{{color:var(--fg-dim)}}
.toc{{padding:.5rem 0;overflow-y:auto;flex:1}}
.toc-group{{
  padding:.85rem 1.2rem .25rem;font-size:.68rem;font-weight:700;
  color:var(--accent2);text-transform:uppercase;letter-spacing:.8px;
}}
.toc-item{{
  display:block;padding:.3rem 1.2rem .3rem 1.5rem;font-size:.8rem;
  color:var(--fg-dim);text-decoration:none;border-left:3px solid transparent;
  transition:all .15s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.toc-item:hover{{color:var(--fg);background:var(--hover)}}
.toc-item.active{{color:var(--accent);border-left-color:var(--accent);background:var(--hover);font-weight:600}}
.toc-item.hidden{{display:none}}
.toc-item .read-dot{{
  display:inline-block;width:6px;height:6px;border-radius:50%;
  margin-right:6px;flex-shrink:0;background:transparent;vertical-align:middle;
}}
.toc-item .read-dot.done{{background:#4ade80}}

/* ── 阅读进度面板 ── */
.progress-panel{{
  border-top:1px solid var(--border);padding:.9rem 1.2rem;flex-shrink:0;
}}
.progress-panel .progress-title{{
  display:flex;justify-content:space-between;align-items:center;
  font-size:.72rem;color:var(--fg-dim);margin-bottom:.45rem;
}}
.progress-panel .progress-title button{{
  background:none;border:none;color:var(--fg-dim);font-size:.68rem;
  cursor:pointer;padding:0;text-decoration:underline;
}}
.progress-panel .progress-title button:hover{{color:var(--accent)}}
.progress-track{{
  width:100%;height:6px;background:var(--code-bg);border-radius:3px;overflow:hidden;
}}
.progress-track .progress-fill{{
  height:100%;border-radius:3px;transition:width .4s;
  background:linear-gradient(90deg,var(--accent),var(--accent2));
}}
.progress-panel .progress-text{{
  font-size:.7rem;color:var(--fg-dim);margin-top:.35rem;text-align:center;
}}
.progress-panel .last-read{{
  font-size:.68rem;color:var(--fg-dim);margin-top:.5rem;padding-top:.45rem;
  border-top:1px solid var(--border);
}}
.progress-panel .last-read a{{
  color:var(--accent);font-size:.72rem;
}}

/* ── 内容 ── */
.content{{margin-left:var(--sidebar-w);flex:1;min-width:0}}
.chapter{{max-width:820px;margin:0 auto;padding:2.5rem 3rem 3rem}}

/* ── 排版 ── */
h1{{font-size:1.8rem;color:var(--accent);margin:1.5rem 0 1rem;padding-bottom:.5rem;border-bottom:2px solid var(--accent);line-height:1.3}}
h2{{font-size:1.3rem;color:#7ec8e3;margin:2rem 0 .7rem;padding-bottom:.3rem;border-bottom:1px solid var(--border)}}
h3{{font-size:1.08rem;color:#a8d8ea;margin:1.5rem 0 .5rem}}
h4{{font-size:1rem;color:#b8c8d0;margin:1.2rem 0 .4rem}}
p{{margin:.7rem 0}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
strong{{color:#fff;font-weight:600}}
em{{color:#a0b4be}}

/* ── 代码 ── */
code{{
  background:var(--code-bg);padding:.14em .42em;border-radius:4px;
  font-size:.87em;font-family:"JetBrains Mono","Fira Code","SF Mono",Menlo,monospace;color:#e0c080;
}}
pre{{
  background:var(--code-bg);padding:1rem 1.2rem;border-radius:var(--radius);
  overflow-x:auto;margin:1rem 0;border:1px solid var(--border);line-height:1.55;
}}
pre code{{background:none;padding:0;color:var(--fg);font-size:.84em}}

/* ── 表格 ── */
table{{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.9em}}
th,td{{border:1px solid var(--border);padding:.45rem .75rem;text-align:left}}
th{{background:var(--code-bg);color:var(--accent);font-weight:600;font-size:.86em}}
tr:hover td{{background:rgba(255,255,255,.02)}}

/* ── 引用 / 列表 / 其他 ── */
blockquote{{border-left:4px solid var(--accent2);padding:.4rem 1rem;margin:1rem 0;color:var(--fg-dim);background:rgba(32,178,170,.08);border-radius:0 var(--radius) var(--radius) 0}}
blockquote p{{margin:.25rem 0}}
ul,ol{{padding-left:1.5rem;margin:.5rem 0}}
li{{margin:.25rem 0}}
hr{{border:none;border-top:1px solid var(--border);margin:2.5rem 0}}
img{{max-width:100%;border-radius:var(--radius)}}

/* ── 下载按钮 ── */
.download-buttons{{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;margin:1rem 0}}
.dl-btn{{
  display:inline-block;padding:.65rem 1.8rem;border-radius:var(--radius);
  font-size:.95rem;font-weight:600;text-decoration:none;transition:all .2s;
  border:2px solid var(--border);
}}
.dl-btn:hover{{text-decoration:none}}
.dl-start{{background:var(--accent);color:#000;border-color:var(--accent)}}
.dl-start:hover{{background:#00bfe0;border-color:#00bfe0;color:#000}}
.dl-pdf{{background:transparent;color:var(--fg);border-color:var(--accent)}}
.dl-pdf:hover{{background:var(--accent);border-color:var(--accent);color:#000}}
.dl-epub{{background:transparent;color:var(--fg);border-color:var(--border)}}
.dl-epub:hover{{border-color:var(--accent);color:var(--accent)}}
.version-info{{font-size:.8rem;color:var(--fg-dim)}}

/* ── 翻页导航 ── */
.page-nav{{
  display:flex;justify-content:space-between;align-items:center;gap:1rem;
  margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--border);
}}
.page-nav a{{
  display:inline-flex;align-items:center;gap:.4rem;
  padding:.55rem 1.1rem;border-radius:var(--radius);
  background:var(--code-bg);border:1px solid var(--border);
  color:var(--fg);font-size:.85rem;text-decoration:none;transition:all .2s;
  max-width:45%;
}}
.page-nav a:hover{{border-color:var(--accent);color:var(--accent)}}
.page-nav a span{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.page-nav .spacer{{flex:1}}

/* ── 进度条 ── */
.progress-bar{{position:fixed;top:0;left:var(--sidebar-w);right:0;height:3px;z-index:110}}
.progress-bar .bar{{height:100%;width:0%;background:linear-gradient(90deg,var(--accent),var(--accent2));transition:width .1s}}

/* ── 回到顶部 ── */
.back-top{{
  position:fixed;bottom:2rem;right:2rem;width:2.4rem;height:2.4rem;border-radius:50%;
  background:var(--accent2);color:#fff;border:none;font-size:1rem;cursor:pointer;
  opacity:0;transition:opacity .3s;display:flex;align-items:center;justify-content:center;z-index:80;
}}
.back-top.show{{opacity:.8}}
.back-top:hover{{opacity:1}}

/* ── 移动端 ── */
.menu-btn{{
  display:none;position:fixed;top:.7rem;left:.7rem;z-index:200;
  background:var(--bg-side);border:1px solid var(--border);border-radius:var(--radius);
  color:var(--accent);font-size:1.2rem;width:2.4rem;height:2.4rem;cursor:pointer;
  align-items:center;justify-content:center;
}}
.overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:90}}
@media(max-width:900px){{
  :root{{--sidebar-w:270px}}
  .chapter{{padding:2rem 1.5rem 2.5rem}}
}}
@media(max-width:700px){{
  .sidebar{{transform:translateX(-100%);transition:transform .3s}}
  .sidebar.open{{transform:translateX(0)}}
  .content{{margin-left:0}}
  .menu-btn{{display:flex}}
  .overlay.show{{display:block}}
  .chapter{{padding:3.2rem 1.1rem 2.5rem}}
  .progress-bar{{left:0}}
  h1{{font-size:1.45rem}} h2{{font-size:1.15rem}}
}}
</style>
</head>
<body>

<button class="menu-btn" onclick="toggleSidebar()">&#9776;</button>
<div class="overlay" onclick="toggleSidebar()"></div>
<div class="progress-bar"><div class="bar"></div></div>

<div class="layout">
  <nav class="sidebar">
    <div class="sidebar-header">
      <h1><a href="/" style="color:inherit;text-decoration:none">解密 Claude Code</a></h1>
      <p>AI 编程助手的源码之旅</p>
    </div>
    <div class="sidebar-search">
      <input type="text" placeholder="搜索章节..." oninput="filterToc(this.value)">
    </div>
    <div class="toc">{sidebar}</div>
    <div class="progress-panel">
      <div class="progress-title">
        <span>阅读进度</span>
        <button onclick="clearProgress()">清除记录</button>
      </div>
      <div class="progress-track"><div class="progress-fill" id="readFill"></div></div>
      <div class="progress-text" id="readText">0 / 0 章</div>
      <div class="last-read" id="lastRead"></div>
    </div>
  </nav>

  <main class="content">
    <article class="chapter">
{body}
    </article>
    <nav class="chapter page-nav">
      {prev_link}
      <span class="spacer"></span>
      {next_link}
    </nav>
  </main>
</div>

<button class="back-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">&#8593;</button>

<script>
// ── 基础交互 ──
function toggleSidebar(){{
  document.querySelector('.sidebar').classList.toggle('open');
  document.querySelector('.overlay').classList.toggle('show');
}}
function filterToc(q){{
  q=q.toLowerCase();
  document.querySelectorAll('.toc-item').forEach(a=>{{
    a.classList.toggle('hidden',q&&!a.textContent.toLowerCase().includes(q));
  }});
}}
window.addEventListener('scroll',()=>{{
  const h=document.documentElement;
  const pct=(h.scrollTop/(h.scrollHeight-h.clientHeight))*100;
  document.querySelector('.progress-bar .bar').style.width=pct+'%';
  document.querySelector('.back-top').classList.toggle('show',h.scrollTop>400);
}},{{passive:true}});
document.addEventListener('keydown',e=>{{
  if(e.target.tagName==='INPUT')return;
  if(e.key==='ArrowLeft'){{ const a=document.querySelector('.page-nav a[data-dir=prev]'); if(a) a.click(); }}
  if(e.key==='ArrowRight'){{ const a=document.querySelector('.page-nav a[data-dir=next]'); if(a) a.click(); }}
}});

// ── 阅读进度（localStorage）──
const STORAGE_KEY = 'dcc_read_progress';
const CURRENT_CID = '{current_cid}';
const ALL_CIDS = {all_cids_json};
const TOTAL = ALL_CIDS.length;

function getProgress(){{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {{}}; }}
  catch {{ return {{}}; }}
}}
function saveProgress(p){{
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}}

// 标记当前章节为已读
function markRead(){{
  const p = getProgress();
  if(!p[CURRENT_CID]){{
    p[CURRENT_CID] = new Date().toISOString();
    saveProgress(p);
  }}
  renderProgress();
}}

// 清除全部进度
function clearProgress(){{
  if(!confirm('确定要清除所有阅读记录吗？')) return;
  localStorage.removeItem(STORAGE_KEY);
  renderProgress();
}}

// 渲染进度 UI
function renderProgress(){{
  const p = getProgress();
  const readCount = ALL_CIDS.filter(id => p[id]).length;
  const pct = TOTAL ? Math.round(readCount / TOTAL * 100) : 0;

  // 进度条
  const fill = document.getElementById('readFill');
  const text = document.getElementById('readText');
  if(fill) fill.style.width = pct + '%';
  if(text) text.textContent = readCount + ' / ' + TOTAL + ' 章（' + pct + '%）';

  // 侧边栏已读标记
  document.querySelectorAll('.read-dot').forEach(dot => {{
    dot.classList.toggle('done', !!p[dot.dataset.cid]);
  }});

  // 上次阅读
  const lastEl = document.getElementById('lastRead');
  if(lastEl){{
    const entries = Object.entries(p).sort((a,b) => b[1].localeCompare(a[1]));
    if(entries.length > 0){{
      const [lastCid, lastTime] = entries[0];
      const link = document.querySelector('.toc-item[data-cid="'+lastCid+'"]');
      const title = link ? link.textContent.trim() : lastCid;
      const d = new Date(lastTime);
      const timeStr = d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')
        +' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
      lastEl.innerHTML = '上次阅读：<a href="'+lastCid+'.html">'+title+'</a><br><span style="font-size:.65rem">'+timeStr+'</span>';
    }} else {{
      lastEl.innerHTML = '<span style="color:var(--fg-dim)">还没有阅读记录</span>';
    }}
  }}

  // 如果全部读完，显示庆祝
  if(readCount === TOTAL && TOTAL > 0 && fill){{
    fill.style.background = 'linear-gradient(90deg,#4ade80,#22d3ee)';
  }}
}}

// 滚动到底部 80% 自动标记已读
let _marked = false;
window.addEventListener('scroll', ()=>{{
  if(_marked) return;
  const h = document.documentElement;
  const scrollPct = h.scrollTop / (h.scrollHeight - h.clientHeight);
  if(scrollPct > 0.8){{
    _marked = true;
    markRead();
  }}
}}, {{passive:true}});

// 页面加载后也立即标记（对于短内容页面）
window.addEventListener('load', ()=>{{
  const h = document.documentElement;
  if(h.scrollHeight <= h.clientHeight * 1.3){{
    // 内容不长，直接标记
    setTimeout(()=>{{ markRead(); }}, 2000);
  }}
  renderProgress();
}});
</script>
</body>
</html>
"""

# ── 主流程 ───────────────────────────────────────────────────

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "."
    out = sys.argv[2] if len(sys.argv) > 2 else "build"
    os.makedirs(out, exist_ok=True)

    # 1) 读取所有章节
    loaded = []  # [(cid, title, html_body)]
    cmap = {}    # cid → title
    for cid, fname, dtitle in CHAPTERS:
        path = os.path.join(src, fname)
        if not os.path.isfile(path):
            print(f"  [SKIP] {fname}"); continue
        md = open(path, encoding="utf-8").read()
        body = md_to_html(md, cid)
        cmap[cid] = dtitle
        loaded.append((cid, dtitle, body))
        print(f"  [OK]   {fname}")

    # 2) 为每个章节生成独立 HTML
    import json
    all_cids_json = json.dumps([c[0] for c in loaded])

    for i, (cid, title, body) in enumerate(loaded):
        prev_link = ""
        next_link = ""
        if i > 0:
            pid, pt = loaded[i-1][0], loaded[i-1][1]
            prev_link = f'<a href="{pid}.html" data-dir="prev"><span>&#8592;</span> <span>{H.escape(pt)}</span></a>'
        if i < len(loaded) - 1:
            nid, nt = loaded[i+1][0], loaded[i+1][1]
            next_link = f'<a href="{nid}.html" data-dir="next"><span>{H.escape(nt)}</span> <span>&#8594;</span></a>'

        sidebar = build_sidebar(cid, cmap)
        html = PAGE.format(
            page_title=H.escape(title),
            sidebar=sidebar,
            body=body,
            prev_link=prev_link,
            next_link=next_link,
            current_cid=cid,
            all_cids_json=all_cids_json,
        )
        p = os.path.join(out, f"{cid}.html")
        open(p, "w", encoding="utf-8").write(html)
        # 封面页同时生成为 index.html
        if cid == "cover":
            open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)

    # 4) 复制图片资源
    for img in ["cover.jpg", "wx.png"]:
        p = os.path.join(src, img)
        if os.path.isfile(p): shutil.copy2(p, os.path.join(out, img))

    print(f"\n  => {len(loaded)} 个页面已生成到 {out}/")

if __name__ == "__main__":
    main()
