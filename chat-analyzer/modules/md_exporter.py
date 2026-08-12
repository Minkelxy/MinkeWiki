"""将分析结果导出为 markdown 文件集合。"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml


class MdExporter:
    """Markdown 报告导出器。"""

    def __init__(self, config_path: str | Path = "config.yaml"):
        self.config_path = Path(config_path).resolve()
        self.config = self._load_config()
        self.proj_dir = self.config_path.parent
        self.out_dir = self.proj_dir / self.config.get("paths", {}).get("output_dir", "output")

    def _load_config(self) -> dict:
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def export(self, target_dir: str | Path) -> Path:
        """导出全部分析结果为 md 文件。"""
        p = Path(target_dir)
        target = p if p.is_absolute() else (self.proj_dir / p).resolve()
        target.mkdir(parents=True, exist_ok=True)

        scores = self._load_json("scores.json")
        portrait = self._load_md("portrait.md")
        todos = self._load_json("todos.json")

        # 1. 首页
        self._write_index(target, scores)

        # 2. 每日日记
        diary_src = self.out_dir / "diary"
        diary_dst = target / "日记"
        if diary_src.exists():
            diary_dst.mkdir(exist_ok=True)
            for f in sorted(diary_src.glob("*.md")):
                (diary_dst / f.name).write_text(f.read_text(encoding="utf-8"))

        # 3. 评分总表
        self._write_scores_table(target / "评分总表.md", scores)

        # 4. 人物画像
        if portrait:
            (target / "人物画像.md").write_text(portrait, encoding="utf-8")

        # 5. 待跟进
        self._write_todos(target / "待跟进.md", todos)

        # 6. 阶段报告
        stage_files = sorted(self.out_dir.glob("stage_report_*.md"), reverse=True)
        if stage_files:
            (target / "阶段分析.md").write_text(stage_files[0].read_text(encoding="utf-8"))

        return target

    def _write_index(self, target: Path, scores: list) -> None:
        """生成首页。"""
        if not scores:
            (target / "README.md").write_text("# 暂无分析数据", encoding="utf-8")
            return

        contact = self.config.get("contact_name", "")
        days = len(scores)
        avg = round(sum(s["overall"] for s in scores) / days, 1) if days else 0

        lines = [
            f"# {contact} - 聊天分析报告",
            "",
            f"**分析周期**: {scores[0]['date']} ~ {scores[-1]['date']}（{days} 天）",
            f"**平均评分**: {avg}/10",
            "",
            "## 文件索引",
            "",
            f"| 文件 | 内容 |",
            f"|------|------|",
            f"| [评分总表](评分总表.md) | 每日 5 维度评分 + 正向/风险信号 |",
            f"| [日记/](日记/) | 每日 AI 生成的日记总结与计划 |",
            f"| [人物画像](人物画像.md) | 对方画像（爱好/信息/愿望/过去） |",
            f"| [待跟进](待跟进.md) | 聊天中的承诺和约定 |",
            f"| [阶段分析](阶段分析.md) | 长周期综合分析报告 |",
            "",
            "## 评分趋势",
            "",
            "| 日期 | 评分 | 互动质量 | 对方投入度 | 自我暴露 | 节奏感 | 关系进展 |",
            "|------|------|----------|-----------|---------|--------|---------|",
        ]

        dims = ["互动质量", "对方投入度", "自我暴露", "节奏感", "关系进展"]
        for s in scores:
            sc = s.get("scores", {})
            dim_vals = " | ".join(str(sc.get(d, "-")) for d in dims)
            lines.append(f"| {s['date']} | {s['overall']} | {dim_vals} |")

        (target / "README.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_scores_table(self, path: Path, scores: list) -> None:
        """生成评分总表。"""
        dims = ["互动质量", "对方投入度", "自我暴露", "节奏感", "关系进展"]
        lines = [
            "# 评分总表",
            "",
            "| 日期 | 综合 | " + " | ".join(dims) + " | 正向信号 | 风险信号 |",
            "|------|------|" + "|".join("---" for _ in dims) + "|---------|---------|",
        ]
        for s in scores:
            sc = s.get("scores", {})
            dim_vals = " | ".join(str(sc.get(d, "-")) for d in dims)
            signals = s.get("signals", [s.get("comment", ""), ""])
            pos = signals[0] if isinstance(signals, list) and len(signals) > 0 else ""
            neg = signals[1] if isinstance(signals, list) and len(signals) > 1 else ""
            lines.append(f"| {s['date']} | **{s['overall']}** | {dim_vals} | {pos} | {neg} |")

        # 统计表
        lines.append("")
        lines.append("## 消息统计")
        lines.append("")
        lines.append("| 日期 | 消息数 | 我% | 对方间隔 | 对方发起 | 均长-我 | 均长-对方 |")
        lines.append("|------|--------|-----|----------|---------|--------|----------|")
        for s in scores:
            st = s.get("_stats", {})
            if st:
                lines.append(
                    f"| {s['date']} | {st.get('total','?')} | {st.get('me_pct','?')}% | "
                    f"{st.get('avg_reply_interval_min','?')}min | {st.get('other_initiations','?')}次 | "
                    f"{st.get('avg_me_len','?')}字 | {st.get('avg_other_len','?')}字 |"
                )

        # 评分趋势图（ECharts，md_in_html 渲染）
        import json as _json
        chart_data = [
            {"date": s["date"], "overall": s["overall"], "scores": s.get("scores", {})}
            for s in scores
        ]
        lines.append("")
        lines.append("## 评分趋势图")
        lines.append("")
        lines.append('<div id="score-chart" style="width:100%;height:360px;margin:8px 0;"></div>')
        lines.append('<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>')
        lines.append("<script>")
        lines.append("document.addEventListener('DOMContentLoaded', function(){")
        lines.append("var el=document.getElementById('score-chart');")
        lines.append("if(!el||typeof echarts==='undefined')return;")
        lines.append("var c=echarts.init(el);")
        lines.append(f"var data={_json.dumps(chart_data, ensure_ascii=False)};")
        lines.append("var dates=data.map(function(d){return d.date});")
        lines.append("var dims=['互动质量','对方投入度','自我暴露','节奏感','关系进展'];")
        lines.append("var s=[{name:'综合',type:'line',lineStyle:{width:3},data:data.map(function(d){return d.overall})}];")
        lines.append("dims.forEach(function(dm){s.push({name:dm,type:'line',data:data.map(function(d){return d.scores[dm]})});});")
        lines.append("c.setOption({title:{text:'评分趋势',left:'center',textStyle:{fontSize:14}},tooltip:{trigger:'axis'},legend:{top:26,type:'scroll'},grid:{left:50,right:20,top:70,bottom:30},xAxis:{type:'category',data:dates},yAxis:{type:'value',min:0,max:10},series:s});")
        lines.append("});")
        lines.append("</script>")

        path.write_text("\n".join(lines), encoding="utf-8")

    def _write_todos(self, path: Path, todos: list) -> None:
        """生成待跟进清单。"""
        if not todos:
            path.write_text("# 待跟进\n\n暂无待跟进事项。", encoding="utf-8")
            return

        pending = [t for t in todos if t.get("status") == "pending"]
        done = [t for t in todos if t.get("status") != "pending"]

        lines = ["# 待跟进", ""]
        if pending:
            lines.append(f"## 进行中（{len(pending)} 项）")
            lines.append("")
            for t in pending:
                lines.append(f"- [{t.get('date','')}] {t.get('content','')}")
            lines.append("")
        if done:
            lines.append(f"## 已完成（{len(done)} 项）")
            lines.append("")
            for t in done:
                lines.append(f"- ~~[{t.get('date','')}] {t.get('content','')}~~")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _load_json(self, name: str) -> list:
        p = self.out_dir / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return []

    def _load_md(self, name: str) -> str:
        p = self.out_dir / name
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ai_eval"
    exporter = MdExporter()
    path = exporter.export(target)
    print(f"已导出到: {path}")
    for f in sorted(path.rglob("*.md")):
        print(f"  {f.relative_to(path)}")


if __name__ == "__main__":
    main()
