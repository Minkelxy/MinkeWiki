"""全量聊天记录阶段性评估分析。"""

import json
import sys
from datetime import datetime
from pathlib import Path

import openai
import yaml


class StageAnalyzer:
    """跨日期整体关系分析器。"""

    def __init__(self, config_path: str | Path = "config.yaml"):
        self.config = self._load_config(config_path)
        self.client = self._init_client()
        self.prompts_dir = Path(config_path).parent / "prompts"

    def _load_config(self, path: str | Path) -> dict:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _init_client(self) -> openai.OpenAI:
        import os

        api_config = self.config.get("api", {})
        api_key = api_config.get("api_key", "")
        if not api_key:
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY")
        return openai.OpenAI(
            api_key=api_key,
            base_url=api_config.get("base_url", "https://api.deepseek.com"),
        )

    def _load_scores(self) -> dict:
        """加载所有评分数据，按日期排序。"""
        scores_path = Path(self.config.get("paths", {}).get("scores", "data/scores.json"))
        if not scores_path.exists():
            raise FileNotFoundError(f"评分数据不存在: {scores_path}。请先运行每日评估。")

        scores = json.loads(scores_path.read_text(encoding="utf-8"))
        scores.sort(key=lambda x: x.get("date", ""))
        return scores

    def _load_daily_summaries(self) -> dict[str, str]:
        """从日记文件或 parsed JSON 中提取每日摘要。"""
        diary_path = Path(self.config.get("paths", {}).get("diary", "../docs/社交/第0段记录.md"))
        config_dir = Path("config.yaml").parent
        diary_full = (config_dir / diary_path).resolve()
        summaries = {}

        if diary_full.exists():
            content = diary_full.read_text(encoding="utf-8")
            # 按日期提取 "### MM-DD" 后的 "#### 记录" 内容
            import re
            date_blocks = re.split(r"\n### (\d{2}-\d{2})\n", content)
            # date_blocks[0] is before first date, then alternating date/content
            i = 1
            while i + 1 < len(date_blocks):
                date_short = date_blocks[i]
                block = date_blocks[i + 1]
                # 提取 #### 记录 下的内容
                record_match = re.search(r"#### 记录\n(.*?)(?=\n####|\Z)", block, re.DOTALL)
                if record_match:
                    text = record_match.group(1).strip()
                    if text:
                        year = datetime.now().year
                        date_full = f"{year}-{date_short}"
                        summaries[date_full] = text
                i += 2

        return summaries

    def _build_scores_summary(self, scores: list[dict]) -> str:
        """将评分数据压缩为可读摘要。"""
        lines = []
        for item in scores:
            date = item.get("date", "?")
            overall = item.get("overall", "-")
            comment = item.get("comment", "")
            dims = item.get("scores", {})
            dim_str = " | ".join(f"{k}:{v}" for k, v in dims.items())
            lines.append(f"{date} 综合{overall}分 | {dim_str}")
            if comment:
                lines.append(f"  评语: {comment}")
        return "\n".join(lines)

    def analyze(self) -> str:
        """生成阶段性分析报告。"""
        contact = self.config.get("contact_name", "对方")
        scores = self._load_scores()
        summaries = self._load_daily_summaries()

        if len(scores) < 1:
            raise ValueError("至少需要 1 天的评分数据。")

        # 构建评分摘要
        scores_summary = self._build_scores_summary(scores)

        # 构建每日摘要
        daily_text = ""
        for s in scores:
            date = s["date"]
            summary = summaries.get(date, "(该日暂无日记总结)")
            daily_text += f"\n### {date}\n{summary}\n"

        # 日期范围
        date_first = scores[0]["date"]
        date_last = scores[-1]["date"]
        days = len(scores)

        # 截断过长内容
        max_chars = 6000
        if len(daily_text) > max_chars:
            daily_text = daily_text[:max_chars] + "\n...（后续内容已省略）"

        prompt_template = (self.prompts_dir / "stage_report.txt").read_text(encoding="utf-8")
        prompt = prompt_template.format(
            contact=contact,
            date_first=date_first,
            date_last=date_last,
            days=days,
            scores_summary=scores_summary,
            daily_summaries=daily_text,
        )

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-chat"),
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content.strip()

    def save_report(self, report: str) -> Path:
        """保存阶段报告。"""
        output_dir = Path(self.config.get("paths", {}).get("reports", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"stage_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        output_path = output_dir / filename
        output_path.write_text(report, encoding="utf-8")
        return output_path


def main():
    analyzer = StageAnalyzer()
    try:
        report = analyzer.analyze()
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}")
        sys.exit(1)

    print("=" * 60)
    print("         阶段性分析报告")
    print("=" * 60)
    print(report)
    print("=" * 60)

    answer = input("\n保存报告？(y/N): ").strip().lower()
    if answer == "y":
        path = analyzer.save_report(report)
        print(f"已保存: {path}")


if __name__ == "__main__":
    main()
