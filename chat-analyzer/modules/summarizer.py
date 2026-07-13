"""调用 LLM 生成每日总结，写入日记文档。"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import openai
import yaml


class Summarizer:
    """聊天记录每日总结器。"""

    def __init__(self, config_path: str | Path = "config.yaml"):
        self.config_path = Path(config_path).resolve()
        self.config = self._load_config(config_path)
        self.client = self._init_client()
        self.prompts_dir = Path(config_path).parent / "prompts"
        self.api_extra = {}
        if self.config.get("api", {}).get("thinking"):
            self.api_extra = {"extra_body": {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}}

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
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量或 config.yaml 中的 api_key")
        return openai.OpenAI(
            api_key=api_key,
            base_url=api_config.get("base_url", "https://api.deepseek.com"),
        )

    def _load_prompt(self, name: str) -> str:
        prompt_path = self.prompts_dir / name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def generate_summary(self, date_str: str) -> dict:
        """生成指定日期的总结和计划。返回 {"summary": str, "plan": str, "todos": str}。"""
        contact = self.config.get("contact_name", "对方")
        messages = self._load_messages(date_str)
        stats = self._calc_stats(messages)
        todo_ctx = self._load_todos_context()
        chat_content = self._chat_content_str(messages)

        prompt_template = self._load_prompt("summary.txt")
        prompt = prompt_template.format(
            contact=contact,
            stats=self._stats_text(stats),
            todos_context=todo_ctx,
            chat_content=chat_content,
        )

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-v4-pro"),
            max_tokens=api_config.get("max_tokens", 1500),
            temperature=api_config.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
            **self.api_extra,
        )

        raw = response.choices[0].message.content.strip()
        result = self._parse_result(raw)
        self._save_todos(result.get("todos", ""), date_str)
        return result

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
        """计算每日统计。"""
        me_msgs = [m for m in messages if m["sender"] == "我"]
        other_msgs = [m for m in messages if m["sender"] != "我"]
        return {
            "total": len(messages),
            "me_count": len(me_msgs),
            "other_count": len(other_msgs),
            "me_pct": round(len(me_msgs) / len(messages) * 100) if messages else 50,
        }

    def _stats_text(self, stats: dict) -> str:
        return (
            f"消息 {stats['total']} 条（我 {stats['me_count']}，对方 {stats['other_count']}），"
            f"我占比 {stats['me_pct']}%"
        )

    def _chat_content_str(self, messages: list[dict], max_chars: int = 7000) -> str:
        lines = [f"[{m['time']}] {m['sender']}: {m['content']}" for m in messages]
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = "... (早期对话已省略) ...\n" + text[-(max_chars - 100):]
        return text

    def _load_todos_context(self) -> str:
        """加载待跟进上下文。"""
        todos_path = self.config_path.parent / self.config.get("paths", {}).get("output_dir", "output") / "todos.json"
        if not todos_path.exists():
            return "(无待跟进事项)"
        todos = json.loads(todos_path.read_text(encoding="utf-8"))
        pending = [t for t in todos if t.get("status") == "pending"]
        if not pending:
            return "(所有待办已完成)"
        lines = ["以下是从之前聊天中提取的待跟进事项："]
        for t in pending[-8:]:
            lines.append(f"  - [{t['date']}] {t['content']}")
        return "\n".join(lines)

    def _save_todos(self, todos_text: str, date_str: str) -> None:
        """保存新提取的待办。"""
        if not todos_text or todos_text.strip() in ("无", "无。", ""):
            return
        items = [line.strip("- ").strip() for line in todos_text.split("\n")
                 if line.strip().startswith("-")]
        if not items:
            return

        todos_path = self.config_path.parent / self.config.get("paths", {}).get("output_dir", "output") / "todos.json"
        existing = []
        if todos_path.exists():
            existing = json.loads(todos_path.read_text(encoding="utf-8"))

        for item in items:
            # 简单去重
            if not any(t.get("content") == item for t in existing):
                existing.append({
                    "date": date_str,
                    "content": item,
                    "status": "pending",
                })

        todos_path.parent.mkdir(parents=True, exist_ok=True)
        todos_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    def _parse_result(self, raw: str) -> dict:
        """解析 LLM 输出，提取总结、计划和待跟进。"""
        import re

        result = {"summary": "", "plan": "", "todos": ""}

        summary_match = re.search(r"【总结】\s*\n?(.*?)(?=【计划】|\Z)", raw, re.DOTALL)
        plan_match = re.search(r"【计划】\s*\n?(.*?)(?=【待跟进】|\Z)", raw, re.DOTALL)
        todos_match = re.search(r"【待跟进】\s*\n?(.*?)(?=\Z)", raw, re.DOTALL)

        if summary_match:
            result["summary"] = summary_match.group(1).strip()
        else:
            result["summary"] = raw

        if plan_match:
            result["plan"] = plan_match.group(1).strip()
        if todos_match:
            result["todos"] = todos_match.group(1).strip()

        return result

    def save_summary(self, date_str: str, result: dict) -> None:
        """将总结+计划+待办写入 output/diary/ 目录。"""
        out_dir = self.config_path.parent / self.config.get("paths", {}).get("output_dir", "output") / "diary"
        out_dir.mkdir(parents=True, exist_ok=True)

        lines = [f"# {date_str} 日记", ""]
        lines.append("## 总结")
        lines.append("")
        lines.append(result.get("summary", ""))
        lines.append("")

        plan = result.get("plan", "")
        if plan:
            lines.append("## 计划")
            lines.append("")
            lines.append(plan)
            lines.append("")

        todos = result.get("todos", "")
        if todos and todos.strip() not in ("无", "无。", ""):
            lines.append("## 待跟进")
            lines.append("")
            lines.append(todos)
            lines.append("")

        out_path = out_dir / f"{date_str}.md"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        short = date_str[-5:] if len(date_str) == 10 else date_str
        print(f"总结+计划已写入: {out_path}")


def main():
    if len(sys.argv) < 2:
        print("用法: python summarizer.py <日期>  日期格式: 2026-07-10")
        sys.exit(1)

    date_str = sys.argv[1]
    summarizer = Summarizer()
    result = summarizer.generate_summary(date_str)
    print("=" * 50)
    print("【总结】")
    print(result.get("summary", ""))
    if result.get("plan"):
        print()
        print("【计划】")
        print(result["plan"])
    print("=" * 50)

    answer = input("\n写入日记？(y/N): ").strip().lower()
    if answer == "y":
        summarizer.save_summary(date_str, result)
    else:
        print("已取消。")


if __name__ == "__main__":
    main()
