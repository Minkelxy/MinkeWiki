"""共享工具函数。"""

import json
from pathlib import Path


def resolve_output_path(config: dict, config_path: Path, key: str) -> Path:
    """解析配置中的相对路径到输出目录。"""
    out_dir = config_path.parent / config.get("paths", {}).get("output_dir", "output")
    return out_dir / key


def load_messages(parsed_dir: Path, date_str: str) -> list[dict]:
    """加载已解析的消息列表。"""
    json_path = parsed_dir / f"{date_str}.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8")).get("messages", [])
    raise FileNotFoundError(f"未找到已解析的聊天记录: {json_path}")


def messages_to_text(messages: list[dict], max_chars: int = 7000) -> str:
    """消息列表转为文本字符串，支持截断。"""
    lines = [f"[{m['time']}] {m['sender']}: {m['content']}" for m in messages]
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = "... (早期对话已省略) ...\n" + text[-(max_chars - 100):]
    return text


def calc_stats(messages: list[dict]) -> dict:
    """计算每日基础统计。"""
    me_msgs = [m for m in messages if m["sender"] == "我"]
    total = len(messages)
    me_count = len(me_msgs)
    return {
        "total": total,
        "me_count": me_count,
        "other_count": total - me_count,
        "me_pct": round(me_count / total * 100) if total else 50,
    }
