"""parser.py 单元测试。"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.parser import ChatParser


def test_parse_iso_format():
    """测试 ISO 格式: 2026-07-10 10:30:00 UserName"""
    content = """2026-07-10 10:30:00 我
今天天气不错

2026-07-10 10:32:00 对方
是啊，挺适合出去的

2026-07-10 10:35:00 我
准备去哪玩

2026-07-10 10:36:00 对方
还没想好
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        f.write(content)
        tmp_path = f.name

    parser = ChatParser()
    messages = parser.parse(tmp_path)
    Path(tmp_path).unlink()

    assert len(messages) == 4, f"期望 4 条消息，实际 {len(messages)} 条"
    assert messages[0]["sender"] == "我"
    assert messages[0]["time"] == "2026-07-10 10:30:00"
    assert messages[1]["content"] == "是啊，挺适合出去的"
    print("✓ ISO 格式测试通过")


def test_parse_json_format():
    """测试 JSON 格式（列表直接包裹）。"""
    data = [
        {"time": "2026-07-10 10:30", "sender": "我", "content": "你好"},
        {"time": "2026-07-10 10:31", "sender": "对方", "content": "你好呀"},
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        tmp_path = f.name

    parser = ChatParser()
    messages = parser.parse(tmp_path)
    Path(tmp_path).unlink()

    assert len(messages) == 2
    assert messages[0]["sender"] == "我"
    assert messages[1]["content"] == "你好呀"
    print("✓ JSON 格式测试通过")


def test_save_parsed():
    """测试保存解析结果。"""
    messages = [
        {"time": "2026-07-10 10:30", "sender": "我", "content": "你好"},
        {"time": "2026-07-10 10:31", "sender": "对方", "content": "你好呀"},
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "test.json"
        parser = ChatParser()
        parser.save_parsed(messages, output)

        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["message_count"] == 2
        assert data["date"] == "2026-07-10"
    print("✓ 保存解析结果测试通过")


if __name__ == "__main__":
    test_parse_iso_format()
    test_parse_json_format()
    test_save_parsed()
    print("\n全部测试通过 ✓")
