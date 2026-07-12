"""长期趋势分析与报告生成。"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml


class Reporter:
    """长期聊天趋势报告生成器。"""

    DIMENSIONS = [
        "对话深度",
        "情绪积极度",
        "回复意愿",
        "话题多样性",
        "自我暴露",
        "节奏控制",
        "破冰进展",
    ]

    def __init__(self, config: dict | str | Path = "config.yaml"):
        if isinstance(config, dict):
            self.config = config
        else:
            with open(config, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

    def generate(self, scores: list[dict]) -> str:
        """基于历史评分数据生成趋势报告。"""
        if not scores:
            return "暂无评分数据。"

        # 按日期排序
        scores.sort(key=lambda x: x.get("date", ""))

        lines = [
            f"# 聊天质量趋势报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"统计天数: {len(scores)} 天",
            f"日期范围: {scores[0]['date']} ~ {scores[-1]['date']}",
            "",
        ]

        # 1. 综合趋势
        lines.append("## 综合评分趋势")
        lines.append("| 日期 | 综合分 | 趋势 |")
        lines.append("|------|--------|------|")

        prev_score = None
        for item in scores:
            score = item.get("overall", 0)
            if prev_score is None:
                trend = "—"
            elif score > prev_score + 0.3:
                trend = "↑"
            elif score < prev_score - 0.3:
                trend = "↓"
            else:
                trend = "→"
            lines.append(f"| {item['date']} | {score} | {trend} |")
            prev_score = score

        # 2. 各维度统计
        lines.append("")
        lines.append("## 各维度平均分与趋势")
        lines.append("| 维度 | 平均分 | 最低 | 最高 | 趋势 |")
        lines.append("|------|--------|------|------|------|")

        for dim in self.DIMENSIONS:
            dim_scores = [
                item.get("scores", {}).get(dim, 0)
                for item in scores
                if item.get("scores", {}).get(dim, 0) > 0
            ]
            if not dim_scores:
                continue

            avg = sum(dim_scores) / len(dim_scores)
            mn = min(dim_scores)
            mx = max(dim_scores)

            # 简单趋势：比较首尾
            if len(dim_scores) >= 2:
                first_half = sum(dim_scores[: len(dim_scores) // 2]) / (len(dim_scores) // 2)
                second_half = sum(dim_scores[len(dim_scores) // 2 :]) / (len(dim_scores) - len(dim_scores) // 2)
                if second_half > first_half + 0.5:
                    trend = "↑ 改善"
                elif second_half < first_half - 0.5:
                    trend = "↓ 下滑"
                else:
                    trend = "→ 持平"
            else:
                trend = "—"

            lines.append(f"| {dim} | {avg:.1f} | {mn} | {mx} | {trend} |")

        # 3. 风险预警
        lines.append("")
        lines.append("## 风险预警")
        alerts_cfg = self.config.get("alerts", {})
        low_threshold = alerts_cfg.get("overall_score_low", 4.0)
        reply_threshold = alerts_cfg.get("reply_willingness_low", 3.0)
        consecutive_days = alerts_cfg.get("consecutive_low_days", 3)

        warnings = []

        # 连续低分检测
        consecutive_low = 0
        for item in scores:
            if item.get("overall", 10) < low_threshold:
                consecutive_low += 1
            else:
                consecutive_low = 0
            if consecutive_low >= consecutive_days:
                warnings.append(
                    f"连续 {consecutive_days} 天综合评分低于 {low_threshold}"
                )
                break

        # 回复意愿低
        for item in scores[-3:]:  # 最近 3 天
            reply_score = item.get("scores", {}).get("回复意愿", 10)
            if reply_score <= reply_threshold:
                warnings.append(
                    f"{item['date']} 回复意愿评分低 ({reply_score}/10)"
                )

        # 下降趋势
        if len(scores) >= 3:
            recent = [s.get("overall", 0) for s in scores[-3:]]
            earlier = [s.get("overall", 0) for s in scores[:-3]] if len(scores) > 3 else []
            if earlier and sum(recent) / 3 < sum(earlier) / len(earlier) - 1.0:
                warnings.append("近 3 天综合评分呈下降趋势")

        if warnings:
            for w in warnings:
                lines.append(f"- **{w}**")
        else:
            lines.append("暂无明显风险信号。")

        # 4. 建议
        lines.append("")
        lines.append("## 行动建议")

        # 基于最低维度给出建议
        latest = scores[-1].get("scores", {})
        if latest:
            lowest_dim = min(latest, key=latest.get)
            lowest_score = latest[lowest_dim]
            suggestions = {
                "对话深度": "尝试引入更多有深度的话题（梦想、价值观、成长经历），避免停留在日常琐事",
                "情绪积极度": "关注对方当前的情绪状态，可以询问近况，表达关心",
                "回复意愿": "不要过度主动，给对方空间。检查是否消息频率过高或话题让对方无感",
                "话题多样性": "拓展聊天范围，准备一些不同领域的话题作为备选",
                "自我暴露": "适当先分享自己，降低对方的防御感，创造安全的分享氛围",
                "节奏控制": "注意消息的发送节奏，避免连续多条消息轰炸，也不要在对方热情时过于冷淡",
                "破冰进展": "寻找共同兴趣点或活动机会，创造线下或更深层次的互动",
            }
            lines.append(
                f"- **重点关注 {lowest_dim}**（当前 {lowest_score} 分）: "
                f"{suggestions.get(lowest_dim, '需要特别留意这个维度')}"
            )

        # 最高维度
        highest_dim = max(latest, key=latest.get)
        lines.append(f"- **继续保持 {highest_dim}**（当前 {latest[highest_dim]} 分），这是你的优势")

        return "\n".join(lines)

    def save(self, report: str) -> None:
        """保存报告到文件。"""
        output_dir = Path(self.config.get("paths", {}).get("reports", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"report_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = output_dir / filename
        output_path.write_text(report, encoding="utf-8")
        print(f"报告已保存: {output_path}")

    def chart_data(self, scores: list[dict]) -> dict:
        """生成可供 matplotlib 使用的图表数据。"""
        dates = [s["date"] for s in scores]
        overall = [s.get("overall", 0) for s in scores]
        dim_data = {}
        for dim in self.DIMENSIONS:
            dim_data[dim] = [
                s.get("scores", {}).get(dim, 0) for s in scores
            ]
        return {"dates": dates, "overall": overall, "dimensions": dim_data}


def main():
    scores_path = Path("data/scores.json")
    if not scores_path.exists():
        print("暂无评分数据。", file=sys.stderr)
        sys.exit(1)

    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    reporter = Reporter()
    report = reporter.generate(scores)
    print(report)
    reporter.save(report)


if __name__ == "__main__":
    main()
