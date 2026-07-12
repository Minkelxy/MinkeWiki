"""从聊天记录提取人物画像信息，更新画像.md。"""

import json
import re
import sys
from pathlib import Path

import openai
import yaml


class PortraitUpdater:
    """人物画像自动更新器。"""

    CATEGORIES = ["爱好", "信息", "愿望", "过去"]

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

    def extract_info(self, date_str: str) -> dict[str, list[str]]:
        """从聊天记录中提取对方的新信息。"""
        contact = self.config.get("contact_name", "对方")
        chat_content = self._load_chat_content(date_str)

        max_chars = 8000
        if len(chat_content) > max_chars:
            chat_content = (
                "... (早期对话已省略) ...\n" + chat_content[-(max_chars - 100) :]
            )

        prompt_template = (self.prompts_dir / "portrait.txt").read_text(encoding="utf-8")
        prompt = prompt_template.format(contact=contact, chat_content=chat_content)

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-chat"),
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        result_text = response.choices[0].message.content.strip()

        # 解析 JSON
        return self._parse_result(result_text)

    def _parse_result(self, text: str) -> dict[str, list[str]]:
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
        return {cat: result.get(cat, []) for cat in self.CATEGORIES}

    def update_portrait(self, new_info: dict[str, list[str]]) -> list[str]:
        """将新信息写入画像.md。返回实际新增的条目。"""
        portrait_rel = self.config.get("paths", {}).get("portrait", "../docs/社交/画像.md")
        portrait_path = Path(portrait_rel)
        if not portrait_path.is_absolute():
            config_dir = Path("config.yaml").parent
            portrait_path = (config_dir / portrait_rel).resolve()

        if not portrait_path.exists():
            raise FileNotFoundError(f"画像文件不存在: {portrait_path}")

        content = portrait_path.read_text(encoding="utf-8")
        added = []

        for category, items in new_info.items():
            if not items:
                continue
            heading = f"## {category}"
            if heading not in content:
                continue

            # 找到该分类标题的位置
            cat_pos = content.index(heading)
            after_cat = content[cat_pos:]

            # 找到下一个 ## 的位置作为分类结束
            next_heading = re.search(r"\n## ", after_cat[len(heading) :])
            if next_heading:
                insert_pos = cat_pos + len(heading) + next_heading.start()
            else:
                insert_pos = cat_pos + len(after_cat)

            for item in items:
                # 检查是否已存在（简单去重）
                if item not in content[cat_pos:insert_pos]:
                    added.append(f"[{category}] {item}")

            if added:
                # 在分类标题后插入新条目
                insert_line_pos = content.index("\n", cat_pos + len(heading))
                new_lines = "\n".join(f"- {item}" for item in items)
                content = (
                    content[: insert_line_pos + 1]
                    + new_lines
                    + "\n"
                    + content[insert_line_pos + 1 :]
                )

        if added:
            portrait_path.write_text(content, encoding="utf-8")

        return added

    def review_existing(self) -> str:
        """查看画像中已有的全部信息。"""
        portrait_rel = self.config.get("paths", {}).get("portrait", "../docs/社交/画像.md")
        portrait_path = Path(portrait_rel)
        if not portrait_path.is_absolute():
            config_dir = Path("config.yaml").parent
            portrait_path = (config_dir / portrait_rel).resolve()

        if not portrait_path.exists():
            return "画像文件不存在"
        return portrait_path.read_text(encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("用法: python portrait.py <日期>  日期格式: 2026-07-10")
        print("      python portrait.py --show   查看当前画像")
        sys.exit(1)

    updater = PortraitUpdater()

    if sys.argv[1] == "--show":
        print(updater.review_existing())
        return

    date_str = sys.argv[1]
    try:
        new_info = updater.extract_info(date_str)
        added = updater.update_portrait(new_info)

        if added:
            print("新增画像信息:")
            for item in added:
                print(f"  + {item}")
        else:
            print("未发现新的画像信息。")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
