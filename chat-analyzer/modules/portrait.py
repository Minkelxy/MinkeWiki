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
        self.config_path = Path(config_path).resolve()
        self.config = self._load_config(config_path)
        self.client = self._init_client()
        self.prompts_dir = Path(config_path).parent / "prompts"
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

    def _load_chat_content(self, date_str: str) -> str:
        parsed_dir = self.config_path.parent / self.config.get("paths", {}).get(
            "parsed_logs", "data/chat_logs/parsed"
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
            model=api_config.get("model", "deepseek-v4-pro"),
            max_tokens=api_config.get("max_tokens", 500),
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
            **self.api_extra,
        )

        msg = response.choices[0].message
        result_text = (msg.content or "").strip()
        # thinking 模式下 content 可能为空，尝试从 reasoning_content 提取
        if not result_text:
            reasoning = getattr(msg, "reasoning_content", None)
            if reasoning:
                result_text = reasoning.strip()
                # 提取最后一段 JSON（reasoning 通常在前面，JSON 在最后）
                if "{" in result_text:
                    result_text = result_text[result_text.rindex("{"):]

        return self._parse_result(result_text) if result_text else {cat: [] for cat in self.CATEGORIES}

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
        elif "{" in text:
            start = text.index("{")
            end = text.rindex("}") + 1
            json_match = text[start:end]

        try:
            result = json.loads(json_match)
        except json.JSONDecodeError:
            # thinking 模式可能返回空 content，记录并跳过
            import sys
            print(f"  [portrait] JSON 解析失败，原始返回: {text[:200]}...", file=sys.stderr)
            return {cat: [] for cat in self.CATEGORIES}
        return {cat: result.get(cat, []) for cat in self.CATEGORIES}

    def _portrait_path(self) -> Path:
        return self.config_path.parent / self.config.get("paths", {}).get("output_dir", "output") / "portrait.md"

    def update_portrait(self, new_info: dict[str, list[str]]) -> list[str]:
        """将新信息写入画像。返回实际新增的条目。"""
        portrait_path = self._portrait_path()
        if not portrait_path.exists():
            portrait_path.parent.mkdir(parents=True, exist_ok=True)
            portrait_path.write_text("## 画像\n\n## 爱好\n\n## 信息\n\n## 愿望\n\n## 过去\n", encoding="utf-8")

        content = portrait_path.read_text(encoding="utf-8")
        added = []

        for category, items in new_info.items():
            if not items:
                continue
            heading = f"## {category}"
            if heading not in content:
                continue

            # 找到分类区域
            cat_pos = content.index(heading)
            after_cat = content[cat_pos:]
            next_heading = re.search(r"\n## ", after_cat[len(heading):])
            section_end = cat_pos + len(heading) + next_heading.start() if next_heading else cat_pos + len(after_cat)

            # 只保留不重复的新条目
            new_items = [it for it in items if it not in content[cat_pos:section_end]]
            if not new_items:
                continue

            for it in new_items:
                added.append(f"[{category}] {it}")

            # 在分类标题后追加新条目
            insert_pos = content.index("\n", cat_pos + len(heading)) + 1
            new_lines = "\n".join(f"- {it}" for it in new_items) + "\n"
            content = content[:insert_pos] + new_lines + content[insert_pos:]

        if added:
            portrait_path.write_text(content, encoding="utf-8")

        return added

    def deduplicate(self) -> str:
        """语义去重画像内容，合并相似条目。"""
        portrait_path = self._portrait_path()
        if not portrait_path.exists():
            return "画像文件不存在，请先运行至少一次全流程。"

        content = portrait_path.read_text(encoding="utf-8")

        # 提取每个分类下的条目
        categories = {}
        import re
        for cat in self.CATEGORIES:
            heading = f"## {cat}"
            if heading not in content:
                continue
            cat_pos = content.index(heading)
            after_cat = content[cat_pos + len(heading):]
            next_h2 = re.search(r"\n## ", after_cat)
            block = after_cat[:next_h2.start()] if next_h2 else after_cat

            items = re.findall(r"^- (.+)$", block, re.MULTILINE)
            if items:
                categories[cat] = items

        if not categories:
            return "画像中无条目，无需去重。"

        # 构建 prompt
        cats_text = ""
        for cat, items in categories.items():
            cats_text += f"\n[{cat}]\n"
            for i, item in enumerate(items, 1):
                cats_text += f"{i}. {item}\n"

        prompt = f"""你是一个信息整理助手。以下是关于一个人的分类信息，其中存在语义重复的条目。

请合并真正重复的条目（意思相同或高度相似的），保留表述最完整的那条。保留所有不重复的条目。

注意：
- 只在同一分类内合并
- 意思不同的条目不要合并（比如"喜欢健身"和"喜欢练背"是不同层次的可以保留，但"健身"和"喜欢健身"是重复的）
- "有舍友"出现了两次，合并为一条
- 输出时保持原有分类结构

严格按以下格式输出：
[分类名]
- 条目1
- 条目2

{cats_text}

去重后的结果："""

        api_config = self.config.get("api", {})
        response = self.client.chat.completions.create(
            model=api_config.get("model", "deepseek-v4-pro"),
            max_tokens=1000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
            **self.api_extra,
        )

        result = response.choices[0].message.content.strip()

        # 重建画像文件
        preamble = content.split("## ")[0]
        new_content = preamble

        # 解析 LLM 输出
        current_cat = None
        for line in result.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                cat_name = line[1:-1]
                if cat_name in self.CATEGORIES:
                    current_cat = cat_name
                    new_content += f"## {cat_name}\n"
            elif line.startswith("- ") and current_cat:
                new_content += line + "\n"

        portrait_path.write_text(new_content, encoding="utf-8")

        # 统计变化
        old_count = sum(len(v) for v in categories.values())
        new_items = re.findall(r"^- ", new_content, re.MULTILINE)
        new_count = len(new_items)
        return f"去重完成: {old_count} 条 → {new_count} 条（合并 {old_count - new_count} 条重复）"

    def review_existing(self) -> str:
        """查看画像中已有的全部信息。"""
        portrait_path = self._portrait_path()
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
