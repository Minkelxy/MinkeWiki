"""调用 LLM 对聊天记录进行多维度评估打分。"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import openai
import yaml


class Evaluator:
    """聊天质量评估器。"""

    DIMENSIONS = [
        "互动质量",    # 对话深度 + 话题多样性
        "对方投入度",  # 情绪积极度 + 回复意愿
        "自我暴露",
        "节奏感",
        "关系进展",
    ]

    def __init__(self, config_path: str | Path = "config.yaml"):
        self.config_path = Path(config_path).resolve()
        self.config = self._load_config(config_path)
        self.client = self._init_client()
        self.prompts_dir = self.config_path.parent / "prompts"
        self.api_extra = {"extra_body": {"thinking": {"type": "disabled"}}}

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

    def _load_messages(self, date_str: str) -> list[dict]:
        """加载已解析的消息列表。"""
        parsed_dir = self.config_path.parent / self.config.get("paths", {}).get(
            "parsed_logs", "data/chat_logs/parsed"
        )
        json_path = parsed_dir / f"{date_str}.json"
        if json_path.exists():
            return json.loads(json_path.read_text(encoding="utf-8")).get("messages", [])
        raise FileNotFoundError(f"未找到已解析的聊天记录: {json_path}")

    def _calc_stats(self, messages: list[dict]) -> dict:
        """计算客观统计数据，作为评分锚点。"""
        me_msgs = [m for m in messages if m["sender"] == "我"]
        other_msgs = [m for m in messages if m["sender"] != "我"]

        total = len(messages)
        me_count = len(me_msgs)
        other_count = len(other_msgs)

        # 对方平均回复间隔（分钟）
        intervals = []
        prev_time = None
        for m in messages:
            t = m.get("time", "")
            if len(t) < 16:
                continue
            try:
                cur = datetime.strptime(t[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if prev_time and m["sender"] != "我":
                gap = (cur - prev_time).total_seconds()
                if 0 < gap < 3600:  # 忽略超过1小时的间隔（换话题）
                    intervals.append(gap / 60)
            if m["sender"] == "我":
                prev_time = cur

        avg_interval = round(sum(intervals) / len(intervals), 1) if intervals else -1

        # 对方消息均长
        other_lengths = [len(m.get("content", "")) for m in other_msgs]
        avg_other_len = round(sum(other_lengths) / len(other_lengths), 1) if other_lengths else 0
        avg_me_len = round(
            sum(len(m.get("content", "")) for m in me_msgs) / len(me_msgs), 1
        ) if me_msgs else 0

        # 对方主动开启话题次数（间隔 >30 分钟后率先发言）
        initiations = 0
        prev_minute = None
        for m in messages:
            t = m.get("time", "")
            if len(t) < 16:
                continue
            try:
                cur_min = datetime.strptime(t[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if prev_minute:
                gap = (cur_min - prev_minute).total_seconds() / 60
                if gap > 30 and m["sender"] != "我":
                    initiations += 1
            prev_minute = cur_min

        # 对方使用非文字消息数量（表情/图片/语音）
        other_rich = sum(1 for m in other_msgs if m.get("type") != "text")

        return {
            "total": total,
            "me_count": me_count,
            "other_count": other_count,
            "me_pct": round(me_count / total * 100) if total else 50,
            "avg_reply_interval_min": avg_interval,
            "avg_other_len": avg_other_len,
            "avg_me_len": avg_me_len,
            "other_initiations": initiations,
            "other_rich_msgs": other_rich,
        }

    def _chat_content_str(self, messages: list[dict], max_chars: int = 7000) -> str:
        """消息列表转为文本，带有截断。"""
        lines = [f"[{m['time']}] {m['sender']}: {m['content']}" for m in messages]
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = "... (早期对话已省略) ...\n" + text[-(max_chars - 100):]
        return text

    def evaluate(self, date_str: str) -> dict:
        """评估指定日期的聊天质量。"""
        contact = self.config.get("contact_name", "对方")
        messages = self._load_messages(date_str)
        stats = self._calc_stats(messages)
        chat_content = self._chat_content_str(messages)

        # 加载历史评分用于校准
        prev_context = self._load_prev_context(date_str)

        prompt_template = (self.prompts_dir / "evaluate.txt").read_text(encoding="utf-8")

        stats_text = (
            f"消息总数: {stats['total']}（我 {stats['me_count']} 条 {stats['me_pct']}%，"
            f"对方 {stats['other_count']} 条）\n"
            f"对方平均回复间隔: {stats['avg_reply_interval_min']} 分钟\n"
            f"平均消息长度: 我 {stats['avg_me_len']} 字，对方 {stats['avg_other_len']} 字\n"
            f"对方主动开启话题: {stats['other_initiations']} 次\n"
            f"对方非文字消息: {stats['other_rich_msgs']} 条（表情/图片/语音）\n"
        )

        prompt = prompt_template.format(
            contact=contact,
            stats=stats_text,
            prev_context=prev_context,
            chat_content=chat_content,
        )

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-v4-pro"),
            max_tokens=api_config.get("max_tokens", 800),
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
            **self.api_extra,
        )

        msg = response.choices[0].message
        result_text = (msg.content or "").strip()
        if not result_text:
            reasoning = getattr(msg, "reasoning_content", None)
            if reasoning:
                result_text = reasoning.strip()
                if "{" in result_text:
                    result_text = result_text[result_text.rindex("{"):]
        result = self._parse_result(result_text, date_str) if result_text else {"scores": {}, "comment": "thinking 模式返回空内容"}
        result["_stats"] = stats
        return result

    def _load_prev_context(self, date_str: str) -> str:
        """加载前几日的评分作为校准上下文。"""
        out_dir = self.config_path.parent / self.config.get("paths", {}).get("output_dir", "output")
        scores_path = out_dir / "scores.json"
        if not scores_path.exists():
            return "(尚无历史评分)"

        all_scores = json.loads(scores_path.read_text(encoding="utf-8"))
        prev = [s for s in all_scores if s["date"] < date_str]
        if not prev:
            return "(今天为首日评分)"

        prev.sort(key=lambda x: x["date"])
        recent = prev[-3:]  # 最近3天
        lines = ["前几日评分参考："]
        for s in recent:
            dim_str = ", ".join(
                f"{k}:{v}" for k, v in s.get("scores", {}).items()
            )
            lines.append(
                f"  {s['date']} 综合{s['overall']}分 | {dim_str}"
            )
        return "\n".join(lines)

    def _parse_result(self, text: str, date_str: str) -> dict:
        """解析 LLM 返回的评估 JSON。"""
        json_match = text
        # 尝试提取 JSON 代码块
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            json_match = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            json_match = text[start:end].strip()
        # 提取最外层 { ... } 作为 JSON
        if "{" in json_match:
            start = json_match.index("{")
            end = json_match.rindex("}") + 1
            json_match = json_match[start:end]

        try:
            result = json.loads(json_match)
        except json.JSONDecodeError:
            import sys
            print(f"  [evaluator] JSON 解析失败，原始返回: {text[:300]}...", file=sys.stderr)
            result = {"scores": {}, "comment": "JSON 解析失败"}

        result["date"] = date_str
        result["timestamp"] = datetime.now().isoformat()
        # 兼容旧 comment 字段 → 转为 signals
        if "comment" in result and "signals" not in result:
            result["signals"] = [result["comment"], ""]

        # 计算加权综合分
        scores = result.get("scores", {})
        if scores:
            weights = self.config.get("scoring_weights", {})
            total_w = sum(weights.get(d, 1.0) for d in self.DIMENSIONS)
            result["overall"] = round(
                sum(scores.get(d, 5) * weights.get(d, 1.0) for d in self.DIMENSIONS) / total_w, 1
            )
        else:
            result["overall"] = result.get("overall", 5.0)

        return result

    def save_scores(self, result: dict) -> Path:
        """保存评分到 scores.json。"""
        out_dir = self.config_path.parent / self.config.get("paths", {}).get("output_dir", "output")
        scores_path = out_dir / "scores.json"
        scores_path.parent.mkdir(parents=True, exist_ok=True)

        existing = []
        if scores_path.exists():
            existing = json.loads(scores_path.read_text(encoding="utf-8"))

        date_str = result["date"]
        for i, item in enumerate(existing):
            if item.get("date") == date_str:
                existing[i] = result
                break
        else:
            existing.append(result)

        existing.sort(key=lambda x: x.get("date", ""))
        scores_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return scores_path

    def format_result(self, result: dict) -> str:
        """格式化评估结果。"""
        stats = result.get("_stats", {})
        lines = [
            f"日期: {result['date']}",
            f"综合评分: {result['overall']}/10",
            "",
            f"📊 今日数据: {stats.get('total', '?')}条 | "
            f"我{stats.get('me_pct', '?')}% | "
            f"对方间隔{stats.get('avg_reply_interval_min', '?')}min | "
            f"对方发起{stats.get('other_initiations', '?')}次",
            "-" * 30,
        ]
        for dim in self.DIMENSIONS:
            score = result.get("scores", {}).get(dim, "-")
            bar = "█" * int(score // 2) + "░" * (5 - int(score // 2))
            lines.append(f"  {dim:　<8}  {score:>2}  {bar}")
        lines.append("-" * 30)
        signals = result.get("signals", [result.get("comment", "无"), ""])
        if isinstance(signals, list) and len(signals) >= 2:
            lines.append(f"✓ {signals[0]}")
            if signals[1]:
                lines.append(f"⚠ {signals[1]}")
        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python evaluator.py <日期>  日期格式: 2026-07-10")
        sys.exit(1)

    date_str = sys.argv[1]
    evaluator = Evaluator()
    try:
        result = evaluator.evaluate(date_str)
        evaluator.save_scores(result)
        print(evaluator.format_result(result))
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请先运行 parser.py 解析原始聊天记录")
        sys.exit(1)


if __name__ == "__main__":
    main()
