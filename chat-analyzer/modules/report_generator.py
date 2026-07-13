"""生成综合 HTML 报告，包含聊天记录、评分、总结、阶段分析的完整单页。"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml


class ReportGenerator:
    """综合 HTML 报告生成器。"""

    def __init__(self, config_path: str | Path = "config.yaml"):
        self.config_path = Path(config_path).resolve()
        self.config = self._load_config(config_path)
        self.proj_dir = self.config_path.parent

    def _resolve_path(self, rel_path: str) -> Path:
        """将配置中的相对路径解析为绝对路径。"""
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return (self.proj_dir / p).resolve()

    def _load_config(self, path: str | Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def generate(self) -> str:
        """生成完整 HTML 报告。"""
        contact = self.config.get("contact_name", "")
        scores = self._load_scores()
        daily_data = self._load_all_daily_data(scores)
        summaries = self._load_diary_summaries()
        portrait = self._load_portrait()
        stats = self._calc_stats(daily_data)
        stage_report = self._load_stage_report()

        # 把总结合并到 daily 数据中
        merged_daily = {}
        for d in daily_data:
            merged_daily[d] = self._sanitize_daily(daily_data[d])
            merged_daily[d]["summary"] = summaries.get(d, "")

        # 构建嵌入数据
        report_data = {
            "contact": contact,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "date_range": f"{scores[0]['date']} ~ {scores[-1]['date']}",
            "total_days": len(scores),
            "total_messages": sum(d["message_count"] for d in daily_data.values()),
            "avg_score": round(sum(s["overall"] for s in scores) / len(scores), 1),
            "scores": scores,
            "daily": merged_daily,
            "portrait": portrait,
            "stats": stats,
            "stage_report": stage_report,
        }

        data_json = json.dumps(report_data, ensure_ascii=False)
        html = HTML_TEMPLATE.replace("{{DATA}}", data_json)
        html = html.replace("{{CONTACT}}", contact)
        return html

    def _sanitize_daily(self, data: dict) -> dict:
        """只保留 HTML 渲染需要的字段，截断消息内容。"""
        msgs = []
        for m in data.get("messages", []):
            content = m.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            msgs.append({
                "time": m["time"][-8:] if len(m["time"]) > 10 else m["time"],
                "sender": m["sender"],
                "content": content,
                "type": m.get("type", "text"),
            })
        return {
            "contact": data.get("contact", ""),
            "message_count": data.get("message_count", 0),
            "messages": msgs,
        }

    def _load_diary_summaries(self) -> dict[str, str]:
        """从 output/diary/ 目录读取每日总结。"""
        diary_dir = self.proj_dir / self.config.get("paths", {}).get("output_dir", "output") / "diary"
        summaries = {}
        if not diary_dir.exists():
            return summaries

        import re
        for f in sorted(diary_dir.glob("*.md")):
            date = f.stem  # "2026-07-04"
            content = f.read_text(encoding="utf-8")
            # 提取 ## 总结 部分
            m = re.search(r"## 总结\n+(.*?)(?=\n## |\Z)", content, re.DOTALL)
            if m:
                text = m.group(1).strip()
                if text:
                    summaries[date] = text
        return summaries

    def _load_scores(self) -> list:
        sp = self.proj_dir / self.config.get("paths", {}).get("output_dir", "output") / "scores.json"
        if not sp.exists():
            return []
        scores = json.loads(sp.read_text(encoding="utf-8"))
        scores.sort(key=lambda x: x["date"])
        return scores

    def _load_all_daily_data(self, scores: list) -> dict:
        result = {}
        parsed_dir = self._resolve_path(self.config["paths"].get("parsed_logs", "data/chat_logs/parsed"))
        for s in scores:
            date = s["date"]
            fpath = parsed_dir / f"{date}.json"
            if fpath.exists():
                result[date] = json.loads(fpath.read_text(encoding="utf-8"))
            else:
                result[date] = {"contact": "", "message_count": 0, "messages": []}
        return result

    def _load_portrait(self) -> dict[str, list[str]]:
        """从画像文件提取分类信息。"""
        portrait_path = self.proj_dir / self.config.get("paths", {}).get("output_dir", "output") / "portrait.md"
        result = {}
        if not portrait_path.exists():
            return result

        import re
        content = portrait_path.read_text(encoding="utf-8")
        for cat in ["爱好", "信息", "愿望", "过去"]:
            heading = f"## {cat}"
            if heading not in content:
                continue
            cat_pos = content.index(heading)
            after_cat = content[cat_pos + len(heading):]
            next_h2 = re.search(r"\n## ", after_cat)
            block = after_cat[:next_h2.start()] if next_h2 else after_cat
            items = re.findall(r"^- (.+)$", block, re.MULTILINE)
            if items:
                result[cat] = items
        return result

    def _calc_stats(self, daily_data: dict) -> dict:
        """计算消息统计数据。"""
        stats = {"daily_msgs": {}, "sender_ratio": [0, 0], "hourly": [0]*24, "initiations": [0, 0]}

        for date, data in sorted(daily_data.items()):
            msgs = data.get("messages", [])
            stats["daily_msgs"][date] = len(msgs)

            for m in msgs:
                sender = m.get("sender", "")
                time_str = m.get("time", "")
                if sender == "我":
                    stats["sender_ratio"][0] += 1
                else:
                    stats["sender_ratio"][1] += 1

                # 提取小时
                if len(time_str) >= 13:
                    try:
                        hour = int(time_str[11:13])
                        if 0 <= hour < 24:
                            stats["hourly"][hour] += 1
                    except ValueError:
                        pass

        # 计算主动发起：每天第一条非我的消息前的"我"消息不算发起
        for date, data in sorted(daily_data.items()):
            msgs = data.get("messages", [])
            total = len(msgs)
            if total == 0:
                continue
            if msgs[0].get("sender") == "我":
                stats["initiations"][0] += 1
            else:
                stats["initiations"][1] += 1

        return stats

    def _load_stage_report(self) -> str:
        """找到最新的阶段报告。"""
        out_dir = self._resolve_path(self.config["paths"].get("reports", "output"))
        candidates = sorted(out_dir.glob("stage_report_*.md"), reverse=True)
        if candidates:
            text = candidates[0].read_text(encoding="utf-8")
            # 简单 markdown → HTML 转换
            return self._md_to_html(text)
        return "尚未生成阶段报告"

    def _md_to_html(self, text: str) -> str:
        """极简 markdown → HTML。"""
        lines = text.split("\n")
        html_lines = []
        in_list = False
        for line in lines:
            line = line.rstrip()
            if not line:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                continue
            if line.startswith("# "):
                if in_list: html_lines.append("</ul>"); in_list = False
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith("## "):
                if in_list: html_lines.append("</ul>"); in_list = False
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith("### "):
                if in_list: html_lines.append("</ul>"); in_list = False
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f'<p class="bold-line">{line[2:-2]}</p>')
            elif "**" in line:
                line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
                if "**" in line:
                    line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append(f"<p>{line}</p>")
        if in_list:
            html_lines.append("</ul>")
        return "\n".join(html_lines)

    def save(self, html: str) -> Path:
        out_dir = self._resolve_path(self.config["paths"].get("reports", "output"))
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"full_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        path.write_text(html, encoding="utf-8")
        return path


# ---- HTML 模板 ----
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{CONTACT}} - 聊天分析报告</title>
<style>
:root {
  --bg: #0d1117; --card: #161b22; --border: #30363d;
  --text: #c9d1d9; --dim: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --orange: #d2991d; --red: #f85149;
  --score-high: #238636; --score-mid: #9e6a03; --score-low: #da3633;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
header { background: var(--card); border-bottom: 1px solid var(--border); padding: 24px 32px; position: sticky; top: 0; z-index: 10; }
header h1 { font-size: 20px; color: var(--accent); }
header .meta { color: var(--dim); font-size: 13px; margin-top: 4px; }
.overview { display: flex; gap: 16px; padding: 24px 32px; flex-wrap: wrap; }
.overview-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px 24px; min-width: 120px; text-align: center; }
.overview-card .value { font-size: 28px; font-weight: 700; color: var(--accent); }
.overview-card .label { font-size: 12px; color: var(--dim); margin-top: 4px; }
.score-trend { padding: 0 32px 24px; overflow-x: auto; }
.score-trend h2 { font-size: 16px; margin-bottom: 12px; color: var(--dim); }
.trend-bars { display: flex; align-items: flex-end; gap: 8px; height: 160px; min-width: 540px; }
.trend-bar { flex: 1; display: flex; flex-direction: column; align-items: center; }
.trend-bar .bar { width: 100%; max-width: 48px; border-radius: 4px 4px 0 0; transition: height .3s; }
.trend-bar .bar.high { background: var(--score-high); } .trend-bar .bar.mid { background: var(--score-mid); } .trend-bar .bar.low { background: var(--score-low); }
.trend-bar .label { font-size: 11px; color: var(--dim); margin-top: 6px; }
.trend-bar .val { font-size: 13px; font-weight: 600; }
.tabs { display: flex; gap: 0; padding: 0 32px; border-bottom: 1px solid var(--border); overflow-x: auto; }
.tab-btn { padding: 10px 16px; background: none; border: none; color: var(--dim); cursor: pointer; font-size: 13px; border-bottom: 2px solid transparent; white-space: nowrap; }
.tab-btn:hover, .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-content { display: none; padding: 24px 32px; }
.tab-content.active { display: block; }
.day-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 900px) { .day-layout { grid-template-columns: 1fr; } }
.chat-box { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; max-height: 75vh; overflow-y: auto; }
.chat-msg { padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,.04); font-size: 13px; }
.chat-msg .t { color: var(--dim); font-size: 11px; }
.chat-msg .s-me { color: var(--accent); }
.chat-msg .s-other { color: var(--green); }
.chat-msg .c { margin-top: 2px; word-break: break-word; }
.chat-msg .c.sticker, .chat-msg .c.image { color: var(--dim); font-style: italic; }
.analysis-box { display: flex; flex-direction: column; gap: 16px; }
.score-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.score-card h3 { font-size: 14px; color: var(--accent); margin-bottom: 8px; }
.score-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 13px; }
.score-row { display: flex; justify-content: space-between; padding: 4px 8px; background: rgba(255,255,255,.03); border-radius: 4px; }
.score-bar-bg { width: 60px; height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle; }
.score-bar-fill { height: 100%; border-radius: 4px; }
.portrait-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
.portrait-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.portrait-card h3 { font-size: 14px; color: var(--accent); margin-bottom: 8px; }
.portrait-card li { font-size: 13px; color: var(--text); margin: 3px 0; padding-left: 4px; list-style: none; }
.portrait-card li::before { content: '· '; color: var(--dim); }
.summary-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.summary-card h3 { font-size: 14px; color: var(--accent); margin-bottom: 8px; }
.summary-card p { font-size: 13px; line-height: 1.7; }
.overall-badge { display: inline-block; font-size: 36px; font-weight: 700; padding: 8px 16px; border-radius: 8px; }
.overall-badge.high { color: var(--green); background: rgba(63,185,80,.1); }
.overall-badge.mid { color: var(--orange); background: rgba(210,153,29,.1); }
.overall-badge.low { color: var(--red); background: rgba(248,81,73,.1); }
.stage-section { padding: 24px 32px; }
.stage-section h2 { font-size: 18px; color: var(--accent); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.stage-content { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 24px; font-size: 13px; line-height: 1.8; }
.stage-content h1 { font-size: 18px; color: var(--accent); margin: 24px 0 12px; }
.stage-content h2 { font-size: 15px; color: var(--accent); margin: 20px 0 10px; border: none; padding: 0; }
.stage-content h3 { font-size: 14px; color: var(--text); margin: 16px 0 8px; }
.stage-content ul { padding-left: 20px; }
.stage-content li { margin: 4px 0; }
.stage-content .bold-line { font-weight: 600; color: var(--text); margin: 12px 0 4px; }
.stage-content b { color: var(--accent); }
.methodology { padding: 24px 32px; margin-top: 24px; border-top: 1px solid var(--border); }
.methodology h2 { font-size: 18px; color: var(--accent); margin-bottom: 16px; }
.methodology-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.method-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.method-card h3 { font-size: 14px; color: var(--accent); margin-bottom: 8px; }
.method-card p, .method-card li { font-size: 13px; color: var(--dim); }
.method-card ul { padding-left: 16px; }
.method-card li { margin: 2px 0; }
.chat-filter { margin-bottom: 12px; display: flex; gap: 8px; }
.chat-filter button { padding: 4px 12px; font-size: 12px; border: 1px solid var(--border); border-radius: 14px; background: var(--card); color: var(--dim); cursor: pointer; }
.chat-filter button.on { background: var(--accent); color: #fff; border-color: var(--accent); }
footer { text-align: center; padding: 32px; color: var(--dim); font-size: 12px; border-top: 1px solid var(--border); margin-top: 32px; }
</style>
</head>
<body>

<header>
  <h1>{{CONTACT}} - 聊天记录分析报告</h1>
  <div class="meta">
    报告生成时间: <span id="meta-time"></span> &nbsp;|&nbsp;
    分析周期: <span id="meta-range"></span> &nbsp;|&nbsp;
    总消息: <span id="meta-msgs"></span> 条
  </div>
</header>

<div class="overview" id="overview"></div>

<div class="portrait-section" id="portrait-section" style="padding:0 32px 24px;">
  <h2 style="font-size:16px;color:var(--dim);margin-bottom:12px;">人物画像</h2>
  <div class="portrait-grid" id="portrait-grid"></div>
</div>

<div class="score-trend">
  <h2>综合评分趋势</h2>
  <div class="trend-bars" id="trend-bars"></div>
</div>

<div class="tabs" id="tabs"></div>
<div id="tab-contents"></div>

<div class="stage-section" id="stage-section">
  <h2>阶段性分析报告</h2>
  <div class="stage-content" id="stage-content"></div>
</div>

<div class="methodology">
  <h2>评分模型与分析流程</h2>
  <div class="methodology-grid">
    <div class="method-card">
      <h3>1. 数据获取</h3>
      <p>通过 WeChatMsg 工具导出微信聊天记录的 JSON 文件，包含时间戳、发送者、消息内容、消息类型等字段。</p>
    </div>
    <div class="method-card">
      <h3>2. 数据解析</h3>
      <p>Parser 模块解析 JSON，将 Unix 时间戳转换为 ISO 时间，发送者 "me" 映射为 "我"，过滤系统消息，非文本消息转换为描述标签（如 [图片]、[表情]）。按日期分组存储为结构化 JSON。</p>
    </div>
    <div class="method-card">
      <h3>3. 每日总结生成</h3>
      <p>调用 DeepSeek Chat API (deepseek-chat 模型)，输入当日全部聊天记录，以第一人称日记体生成 200-300 字总结。Prompt 要求记录关键话题、对方展现的特质、自身表现的亮点和失误。</p>
    </div>
    <div class="method-card">
      <h3>4. 多维度评分</h3>
      <p>调用 DeepSeek Chat API，对当日聊天进行 5 维度评估（每项 1-10 分），评分时参考客观统计数据（消息数、回复间隔、消息均长、主动发起次数）：</p>
      <ul>
        <li><b>互动质量</b> — 话题是否有深度和广度</li>
        <li><b>对方投入度</b> — 情绪表达、回复速度、延伸话题意愿</li>
        <li><b>自我暴露</b> — 对方主动分享个人信息的程度</li>
        <li><b>节奏感</b> — 我方的聊天频率和推进节奏</li>
        <li><b>关系进展</b> — 关系阶段是否有推进</li>
      </ul>
      <p style="margin-top:8px;">综合分 = 加权平均（对方投入度权重最高 2.0）。评分校准：传入前3日历史评分作为参考。</p>
    </div>
    <div class="method-card">
      <h3>5. 人物画像提取</h3>
      <p>从聊天记录中提取对方新信息，按爱好、客观信息、愿望、过去经历四个分类存储。自动去重，避免重复记录已知信息。</p>
    </div>
    <div class="method-card">
      <h3>6. 阶段性分析</h3>
      <p>汇总所有日期的评分数据和每日总结，调用 DeepSeek Chat API 生成跨天综合分析，包括关系轨迹、对方画像、我方表现评估、风险提示和下阶段建议。</p>
    </div>
    <div class="method-card">
      <h3>7. 技术实现</h3>
      <p>Python 3 + DeepSeek API (OpenAI 兼容格式)。评分温度 0.3（确保稳定），总结温度 0.7（增加自然度）。max_tokens: 总结 1000、评估 800、阶段分析 2000。</p>
    </div>
  </div>
</div>

<footer>
  Chat Analyzer &mdash; 基于 DeepSeek Chat API 的自动分析系统 &mdash; {{CONTACT}}
</footer>

<script>
const D = {{DATA}};

// Helpers
function scoreClass(s) { return s >= 7.5 ? 'high' : s >= 5.5 ? 'mid' : 'low'; }
function fmtDate(d) { return d.slice(5); }

// Meta
document.getElementById('meta-time').textContent = D.generated;
document.getElementById('meta-range').textContent = D.date_range;
document.getElementById('meta-msgs').textContent = D.total_messages;

// Overview cards
const ov = document.getElementById('overview');
[
  ['总天数', D.total_days],
  ['总消息', D.total_messages],
  ['平均评分', D.avg_score + '/10'],
  ['最高评分', Math.max(...D.scores.map(s=>s.overall)) + '/10'],
  ['最低评分', Math.min(...D.scores.map(s=>s.overall)) + '/10'],
].forEach(([label, value]) => {
  ov.innerHTML += `<div class="overview-card"><div class="value">${value}</div><div class="label">${label}</div></div>`;
});

// Portrait
const portraitGrid = document.getElementById('portrait-grid');
const catNames = { '爱好': '爱好', '信息': '基本信息', '愿望': '愿望', '过去': '过去经历' };
if (D.portrait && Object.keys(D.portrait).length) {
  Object.entries(D.portrait).forEach(([cat, items]) => {
    if (!items.length) return;
    let html = '<div class="portrait-card"><h3>' + (catNames[cat]||cat) + '</h3><ul>';
    items.forEach(item => { html += '<li>' + escHtml(item) + '</li>'; });
    html += '</ul></div>';
    portraitGrid.innerHTML += html;
  });
} else {
  document.getElementById('portrait-section').style.display = 'none';
}

// Stats
const statsCards = document.getElementById('overview');
// sender ratio
const sr = D.stats.sender_ratio;
const sTotal = sr[0] + sr[1];
const mePct = sTotal ? Math.round(sr[0]/sTotal*100) : 50;
const initTotal = D.stats.initiations[0] + D.stats.initiations[1];
const meInit = initTotal ? Math.round(D.stats.initiations[0]/initTotal*100) : 50;
statsCards.innerHTML += '<div class="overview-card"><div class="value">' + mePct + '%</div><div class="label">我发言占比</div></div>';
statsCards.innerHTML += '<div class="overview-card"><div class="value">' + Math.round(sTotal/D.total_days) + '</div><div class="label">日均消息</div></div>';
statsCards.innerHTML += '<div class="overview-card"><div class="value">' + meInit + '%</div><div class="label">我主动发起</div></div>';

// Hourly heatmap
const maxH = Math.max(...D.stats.hourly);
let hourHtml = '<h2 style="font-size:16px;color:var(--dim);margin:0 0 12px 0;">消息时段分布</h2><div style="display:flex;gap:2px;height:40px;align-items:flex-end;">';
D.stats.hourly.forEach((count, h) => {
  const pct = maxH ? count/maxH : 0;
  const color = pct > 0.7 ? 'var(--green)' : pct > 0.3 ? 'var(--accent)' : '#21262d';
  hourHtml += '<div style="flex:1;background:' + color + ';height:' + Math.max(pct*40, 2) + 'px;border-radius:2px 2px 0 0;" title="' + h + '时: ' + count + '条"></div>';
});
hourHtml += '</div><div style="display:flex;justify-content:space-between;font-size:10px;color:var(--dim);margin-top:4px;">';
[0,4,8,12,16,20,23].forEach(h => { hourHtml += '<span>' + h + 'h</span>'; });
hourHtml += '</div>';
document.querySelector('.score-trend').insertAdjacentHTML('beforebegin', '<div style="padding:0 32px 24px;">' + hourHtml + '</div>');

// Trend bars
const tb = document.getElementById('trend-bars');
D.scores.forEach(s => {
  const h = s.overall * 15;
  tb.innerHTML += `<div class="trend-bar"><div class="bar ${scoreClass(s.overall)}" style="height:${h}px"></div><div class="val">${s.overall}</div><div class="label">${fmtDate(s.date)}</div></div>`;
});

// Tabs
const tabsEl = document.getElementById('tabs');
const contentsEl = document.getElementById('tab-contents');
const dates = Object.keys(D.daily).sort();

dates.forEach((date, i) => {
  tabsEl.innerHTML += `<button class="tab-btn${i===0?' active':''}" onclick="switchTab('${date}')">${fmtDate(date)}</button>`;

  const data = D.daily[date];
  const score = D.scores.find(s => s.date === date) || {};
  const dims = score.scores || {};
  const dimLabels = ['互动质量','对方投入度','自我暴露','节奏感','关系进展'];

  let chatHtml = `<div class="chat-filter"><button class="on" onclick="filterChat('${date}','all',this)">全部</button><button onclick="filterChat('${date}','me',this)">我</button><button onclick="filterChat('${date}','other',this)">对方</button></div><div class="chat-box" id="chat-${date}">`;
  data.messages.forEach(m => {
    const isMe = m.sender === '我';
    const sClass = isMe ? 's-me' : 's-other';
    const cClass = m.type !== 'text' ? ' ' + m.type : '';
    chatHtml += `<div class="chat-msg" data-sender="${isMe?'me':'other'}"><span class="t">${m.time}</span> <span class="${sClass}">${m.sender}</span><div class="c${cClass}">${escHtml(m.content)}</div></div>`;
  });
  chatHtml += '</div>';

  let scoreHtml = '<div class="score-card"><h3>综合评分</h3>';
  const ovScore = score.overall || 0;
  scoreHtml += `<div class="overall-badge ${scoreClass(ovScore)}">${ovScore}/10</div>`;
  const signals = score.signals || [];
  if (signals.length) {
    scoreHtml += '<p style="margin-top:8px;font-size:13px;">';
    if (signals[0]) scoreHtml += '<span style="color:var(--green);">✓ ' + escHtml(signals[0]) + '</span><br>';
    if (signals[1]) scoreHtml += '<span style="color:var(--orange);">⚠ ' + escHtml(signals[1]) + '</span>';
    scoreHtml += '</p>';
  } else if (score.comment) scoreHtml += '<p style="margin-top:8px;color:var(--dim);font-size:13px;">' + escHtml(score.comment) + '</p>';
  scoreHtml += '</div>';

  scoreHtml += '<div class="score-card"><h3>各维度评分</h3><div class="score-grid">';
  dimLabels.forEach(dim => {
    const v = dims[dim] || 0;
    const color = v >= 7 ? 'var(--score-high)' : v >= 5 ? 'var(--score-mid)' : 'var(--score-low)';
    scoreHtml += `<div class="score-row"><span>${dim}</span><span>${v} <span class="score-bar-bg"><span class="score-bar-fill" style="width:${v*10}%;background:${color}"></span></span></span></div>`;
  });
  scoreHtml += '</div></div>';

  // Diary summary (embedded in daily data)
  const summary = data.summary || '';
  if (summary) {
    scoreHtml += '<div class="summary-card"><h3>日记总结</h3><p>' + escHtml(summary).replace(/\n/g, '<br>') + '</p></div>';
  }

  contentsEl.innerHTML += `<div class="tab-content${i===0?' active':''}" id="tab-${date}"><div class="day-layout"><div>${chatHtml}</div><div class="analysis-box">${scoreHtml}</div></div></div>`;
});

function switchTab(date) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + date).classList.add('active');
}

function filterChat(date, type, btn) {
  btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  const box = document.getElementById('chat-' + date);
  box.querySelectorAll('.chat-msg').forEach(m => {
    if (type === 'all') m.style.display = '';
    else m.style.display = m.dataset.sender === type ? '' : 'none';
  });
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Stage report
document.getElementById('stage-content').innerHTML = D.stage_report || '<p>尚未生成阶段报告。请先运行 python main.py stage。</p>';
</script>
</body>
</html>"""


def main():
    gen = ReportGenerator()
    html = gen.generate()
    path = gen.save(html)
    print(f"报告已生成: {path}")
    print(f"文件大小: {len(html):,} 字节")
    print(f"可直接在浏览器中打开: file://{path}")


if __name__ == "__main__":
    main()
