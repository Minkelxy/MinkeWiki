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

    def _load_chat_content(self, date_str: str) -> str:
        """从解析后的 JSON 或原始 txt 加载聊天内容。"""
        parsed_dir = Path(
            self.config.get("paths", {}).get("parsed_logs", "data/chat_logs/parsed")
        )
        raw_dir = Path(
            self.config.get("paths", {}).get("raw_logs", "data/chat_logs/raw")
        )

        # 优先读取已解析的 JSON
        json_path = parsed_dir / f"{date_str}.json"
        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))
            lines = []
            for msg in data.get("messages", []):
                lines.append(f"[{msg['time']}] {msg['sender']}: {msg['content']}")
            return "\n".join(lines)

        # 回退到原始 txt
        for ext in [".txt", ".log"]:
            raw_path = raw_dir / f"{date_str}{ext}"
            if raw_path.exists():
                return raw_path.read_text(encoding="utf-8")

        raise FileNotFoundError(
            f"未找到 {date_str} 的聊天记录文件（检查了 parsed/ 和 raw/）"
        )

    def generate_summary(self, date_str: str) -> str:
        """生成指定日期的总结。"""
        contact = self.config.get("contact_name", "对方")
        chat_content = self._load_chat_content(date_str)

        # 如果内容太长，截断到最近的消息（保留最后 ~8000 字）
        max_chars = 8000
        if len(chat_content) > max_chars:
            chat_content = (
                "... (早期对话已省略) ...\n" + chat_content[-(max_chars - 100) :]
            )

        prompt_template = self._load_prompt("summary.txt")
        prompt = prompt_template.format(contact=contact, chat_content=chat_content)

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-chat"),
            max_tokens=api_config.get("max_tokens", 1000),
            temperature=api_config.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )

        summary = response.choices[0].message.content
        return summary.strip()

    def write_to_diary(self, date_str: str, summary: str) -> None:
        """将总结写入 第0段记录.md 对应日期的 #### 记录 下。"""
        diary_rel = self.config.get("paths", {}).get("diary", "../docs/社交/第0段记录.md")
        diary_path = Path(diary_rel)
        if not diary_path.is_absolute():
            # 相对于 config.yaml 所在目录
            config_dir = Path("config.yaml").parent
            diary_path = (config_dir / diary_rel).resolve()

        if not diary_path.exists():
            raise FileNotFoundError(f"日记文件不存在: {diary_path}")

        content = diary_path.read_text(encoding="utf-8")

        # 提取日期短格式：2026-07-10 → 07-10
        short_date = date_str[-5:] if len(date_str) == 10 else date_str

        # 匹配 "### 07-10" 及其后续的 "#### 记录"
        date_heading = f"### {short_date}"

        if date_heading not in content:
            raise ValueError(f"在日记中未找到日期标题: {date_heading}")

        # 找到日期标题后的 #### 记录 位置
        date_pos = content.index(date_heading)
        after_date = content[date_pos:]

        record_heading = "#### 记录"
        if record_heading not in after_date:
            raise ValueError(f"在 {date_heading} 下未找到 {record_heading}")

        record_pos = date_pos + after_date.index(record_heading) + len(record_heading)
        # 找到下一行
        next_newline = content.index("\n", record_pos)
        # 检查下一行是否是 #### 计划 (即 #### 记录下无内容)
        next_section = content.find("####", next_newline + 1)

        insert_pos = next_newline

        # 在 "#### 记录" 后插入总结
        indent = "\n\n"
        # 检查是否已有内容
        existing = content[next_newline + 1 : next_section].strip() if next_section > 0 else ""
        if existing and not existing.startswith("##"):
            # 追加到已有内容后
            insert_pos = next_newline
            new_content = content[:insert_pos] + f"\n{summary}\n" + content[insert_pos + 1:]
        else:
            new_content = content[:insert_pos] + f"\n\n{summary}\n" + content[insert_pos:]

        diary_path.write_text(new_content, encoding="utf-8")
        print(f"总结已写入: {diary_path} ({short_date})")


def main():
    if len(sys.argv) < 2:
        print("用法: python summarizer.py <日期>  日期格式: 2026-07-10")
        sys.exit(1)

    date_str = sys.argv[1]
    summarizer = Summarizer()
    summary = summarizer.generate_summary(date_str)
    print("=" * 50)
    print(summary)
    print("=" * 50)

    answer = input("\n写入日记？(y/N): ").strip().lower()
    if answer == "y":
        summarizer.write_to_diary(date_str, summary)
    else:
        print("已取消。")


if __name__ == "__main__":
    main()
