"""解析 WeChatMsg 导出的聊天记录，转为结构化 JSON。"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


class ChatParser:
    """解析 WeChatMsg 聊天记录文本。"""

    # 常见时间格式
    PATTERNS = {
        # 2026-07-10 10:30:00
        "iso": re.compile(
            r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)\s+(.+)$"
        ),
        # 2026年7月10日 上午10:30 或 2026年7月10日 10:30
        "cn_date": re.compile(
            r"^(\d{4})年(\d{1,2})月(\d{1,2})日\s+(?:[上中下]午)?(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$"
        ),
        # 7月10日 10:30
        "short_cn": re.compile(
            r"^(\d{1,2})月(\d{1,2})日\s+(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$"
        ),
        # 07-10 10:30
        "short": re.compile(
            r"^(\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)\s+(.+)$"
        ),
        # 10:30 UserName
        "time_only": re.compile(
            r"^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$"
        ),
    }

    def __init__(self, contact_name: str = "", year: int | None = None):
        self.contact_name = contact_name
        self.year = year or datetime.now().year

    def parse(self, file_path: str | Path) -> list[dict]:
        """解析聊天记录文件，返回消息列表。"""
        content = Path(file_path).read_text(encoding="utf-8")

        # 先尝试 JSON 格式（WeChatMsg v3+）
        if content.strip().startswith(("{", "[")):
            return self._parse_json(content)

        return self._parse_text(content)

    def parse_with_meta(self, file_path: str | Path) -> dict:
        """解析并返回元信息和消息列表。"""
        messages = self.parse(file_path)
        content = Path(file_path).read_text(encoding="utf-8")
        meta = {}

        if content.strip().startswith("{"):
            data = json.loads(content)
            if isinstance(data, dict):
                meta = {
                    "contact": data.get("contact_remark", data.get("chat", "")),
                    "nick_name": data.get("contact_nick_name", ""),
                    "date_first": data.get("date_first_msg", ""),
                    "date_last": data.get("date_last_msg", ""),
                }

        return {"meta": meta, "messages": messages}

    def _parse_json(self, content: str) -> list[dict]:
        """解析 WeChatMsg JSON 导出格式。"""
        data = json.loads(content)
        messages = []

        # 提取联系人名称，用于 sender 翻译
        contact_name = ""
        if isinstance(data, dict):
            contact_name = data.get("contact_remark", data.get("contact_nick_name", ""))
            items = data.get("messages", data.get("msgs", []))
        elif isinstance(data, list):
            items = data
        else:
            return []

        for item in items:
            # 跳过系统消息
            if item.get("type") == "system":
                continue

            # 时间戳转换
            ts = item.get("timestamp", item.get("time", item.get("createTime", 0)))
            if isinstance(ts, (int, float)) and ts > 1000000000:
                from datetime import datetime

                time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = str(ts)

            # sender 翻译: "me" → "我", 联系人名保持不变
            sender = str(item.get("sender", item.get("talker", item.get("userName", ""))))
            if sender == "me":
                sender = "我"
            elif not sender or sender == "None":
                sender = "未知"

            # 内容处理：非文本消息生成描述
            msg_type = item.get("type", "text")
            content = str(item.get("content", item.get("msg", item.get("message", ""))))

            if not content or content == "None":
                type_desc = {
                    "image": "[图片]",
                    "sticker": "[表情]",
                    "video": "[视频]",
                    "voice": "[语音]",
                    "link_or_file": "[链接/文件]",
                    "file": "[文件]",
                    "location": "[位置]",
                }
                content = type_desc.get(msg_type, f"[{msg_type}]")

            messages.append({
                "time": time_str,
                "sender": sender,
                "content": content,
                "type": msg_type,
            })

        return messages

    def _parse_text(self, content: str) -> list[dict]:
        """解析文本格式聊天记录。"""
        lines = content.strip().split("\n")
        messages = []
        current_msg = None
        detected_pattern = None
        current_date = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试匹配每种格式
            match = None
            pattern_name = None

            for name, pattern in self.PATTERNS.items():
                match = pattern.match(line)
                if match:
                    pattern_name = name
                    break

            if match:
                # 这是新消息的头部
                # 保存上一条消息
                if current_msg:
                    messages.append(current_msg)

                # 提取发送者
                sender = match.group(self._get_sender_group(pattern_name))

                # 跳过系统消息
                if self._is_system_msg(sender, pattern_name):
                    current_msg = None
                    continue

                # 构建时间字符串
                time_str = self._build_time(pattern_name, match)

                current_msg = {
                    "time": time_str,
                    "sender": sender,
                    "content": "",
                }
                current_date = time_str.split(" ")[0] if " " in time_str else time_str
            elif current_msg is not None:
                # 续行，追加到上一条消息
                if current_msg["content"]:
                    current_msg["content"] += "\n" + line
                else:
                    current_msg["content"] = line

        # 保存最后一条
        if current_msg:
            messages.append(current_msg)

        return messages

    @staticmethod
    def _get_sender_group(pattern_name: str) -> int:
        """返回 sender 在正则分组中的位置。"""
        mapping = {
            "iso": 3,
            "cn_date": 4,
            "short_cn": 3,
            "short": 3,
            "time_only": 2,
        }
        return mapping.get(pattern_name, 3)

    def _build_time(self, pattern_name: str, match: re.Match) -> str:
        """根据匹配结果构建完整时间字符串。"""
        if pattern_name == "iso":
            date = match.group(1)
            time = match.group(2)
            if len(time.split(":")) == 2:
                time += ":00"
            return f"{date} {time}"

        elif pattern_name == "cn_date":
            y = match.group(1)
            m = match.group(2).zfill(2)
            d = match.group(3).zfill(2)
            time = match.group(4)
            if len(time.split(":")) == 2:
                time += ":00"
            return f"{y}-{m}-{d} {time}"

        elif pattern_name == "short_cn":
            m = match.group(1).zfill(2)
            d = match.group(2).zfill(2)
            time = match.group(3)
            if len(time.split(":")) == 2:
                time += ":00"
            return f"{self.year}-{m}-{d} {time}"

        elif pattern_name == "short":
            date = match.group(1)
            time = match.group(2)
            if len(time.split(":")) == 2:
                time += ":00"
            return f"{self.year}-{date} {time}"

        elif pattern_name == "time_only":
            time = match.group(1)
            if len(time.split(":")) == 2:
                time += ":00"
            return f"未知日期 {time}"

        return ""

    @staticmethod
    def _is_system_msg(sender: str, pattern_name: str) -> bool:
        """判断是否为系统消息。"""
        system_keywords = ["系统消息", "System", "你撤回了一条消息", "对方撤回了一条消息"]
        return any(kw in sender for kw in system_keywords)

    def save_parsed(self, messages: list[dict], output_path: str | Path, meta: dict | None = None) -> None:
        """将解析结果保存为 JSON。"""
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "date": self._guess_date(messages),
            "contact": self.contact_name or (meta or {}).get("contact", ""),
            "message_count": len(messages),
            "messages": messages,
        }
        if meta:
            data["meta"] = meta
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _guess_date(messages: list[dict]) -> str:
        """从消息中猜测对话日期。"""
        for msg in messages:
            time_str = msg.get("time", "")
            if time_str and " " in time_str:
                return time_str.split(" ")[0]
        return datetime.now().strftime("%Y-%m-%d")


def main():
    if len(sys.argv) < 2:
        print("用法: python parser.py <raw_log.txt> [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    parser = ChatParser()
    messages = parser.parse(input_path)
    print(f"解析完成: {len(messages)} 条消息")

    if output_path:
        parser.save_parsed(messages, output_path)
        print(f"已保存: {output_path}")
    else:
        for msg in messages[:5]:
            print(f"[{msg['time']}] {msg['sender']}: {msg['content'][:50]}...")
        if len(messages) > 5:
            print(f"... 共 {len(messages)} 条消息")


if __name__ == "__main__":
    main()
