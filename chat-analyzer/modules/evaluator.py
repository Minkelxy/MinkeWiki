"""调用 LLM 对聊天记录进行多维度评估打分。"""

import json
import sys
from datetime import datetime
from pathlib import Path

import openai
import yaml


class Evaluator:
    """聊天质量评估器。"""

    DIMENSIONS = [
        "对话深度",
        "情绪积极度",
        "回复意愿",
        "话题多样性",
        "自我暴露",
        "节奏控制",
        "破冰进展",
    ]

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

    def _load_chat_content(self, date_str: str) -> str:
        """从解析后的 JSON 加载聊天内容。"""
        parsed_dir = Path(
            self.config.get("paths", {}).get("parsed_logs", "data/chat_logs/parsed")
        )

        json_path = parsed_dir / f"{date_str}.json"
        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))
            lines = []
            for msg in data.get("messages", []):
                lines.append(f"[{msg['time']}] {msg['sender']}: {msg['content']}")
            return "\n".join(lines)

        raise FileNotFoundError(f"未找到已解析的聊天记录: {json_path}")

    def evaluate(self, date_str: str) -> dict:
        """评估指定日期的聊天质量。"""
        contact = self.config.get("contact_name", "对方")
        chat_content = self._load_chat_content(date_str)

        # 截断过长内容
        max_chars = 8000
        if len(chat_content) > max_chars:
            chat_content = (
                "... (早期对话已省略) ...\n" + chat_content[-(max_chars - 100) :]
            )

        prompt_template = (self.prompts_dir / "evaluate.txt").read_text(encoding="utf-8")
        prompt = prompt_template.format(contact=contact, chat_content=chat_content)

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-chat"),
            max_tokens=800,
            temperature=0.3,  # 评估用低温度，更稳定
            messages=[{"role": "user", "content": prompt}],
        )

        result_text = response.choices[0].message.content.strip()

        # 解析 JSON 响应
        return self._parse_result(result_text, date_str)

    def _parse_result(self, text: str, date_str: str) -> dict:
        """解析 LLM 返回的评估 JSON。"""
        # 提取 JSON 块
        json_match = text
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            json_match = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            json_match = text[start:end].strip()

        result = json.loads(json_match)
        result["date"] = date_str
        result["timestamp"] = datetime.now().isoformat()

        # 计算加权综合分
        weights = self.config.get("scoring_weights", {})
        scores = result.get("scores", {})
        if scores:
            weighted_sum = 0.0
            total_weight = 0.0
            for dim in self.DIMENSIONS:
                score = scores.get(dim, 5)
                weight = weights.get(dim, 1.0)
                weighted_sum += score * weight
                total_weight += weight
            result["overall"] = round(weighted_sum / total_weight, 1)
        else:
            result["overall"] = result.get("overall", 5.0)

        return result

    def save_scores(self, result: dict) -> Path:
        """将评估结果追加到 scores.json。"""
        scores_path = Path(self.config.get("paths", {}).get("scores", "data/scores.json"))
        scores_path.parent.mkdir(parents=True, exist_ok=True)

        existing = []
        if scores_path.exists():
            existing = json.loads(scores_path.read_text(encoding="utf-8"))

        # 如果当天已有记录，替换；否则追加
        date_str = result["date"]
        replaced = False
        for i, item in enumerate(existing):
            if item.get("date") == date_str:
                existing[i] = result
                replaced = True
                break

        if not replaced:
            existing.append(result)

        # 按日期排序
        existing.sort(key=lambda x: x.get("date", ""))

        scores_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return scores_path

    def format_result(self, result: dict) -> str:
        """将评估结果格式化为可读文本。"""
        lines = [
            f"日期: {result['date']}",
            f"综合评分: {result['overall']}/10",
            "-" * 30,
        ]
        for dim in self.DIMENSIONS:
            score = result.get("scores", {}).get(dim, "-")
            bar = "█" * int(score // 2) + "░" * (5 - int(score // 2))
            lines.append(f"  {dim:　<8}  {score:>2}  {bar}")
        lines.append("-" * 30)
        lines.append(f"评语: {result.get('comment', '无')}")
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
