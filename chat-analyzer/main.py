#!/usr/bin/env python3
"""聊天记录评估系统 - 入口脚本。

使用流程:
  1. WeChatMsg 导出聊天记录 → data/chat_logs/raw/07-10.txt
  2. python main.py --date 2026-07-10           # 全部流程
  3. python main.py --date 2026-07-10 --dry     # 预览，不写入
  4. python main.py --report                    # 生成长期报告
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

from modules.parser import ChatParser
from modules.summarizer import Summarizer
from modules.evaluator import Evaluator
from modules.stage_analyzer import StageAnalyzer
from modules.portrait import PortraitUpdater


def load_config(config_path: str = "config.yaml") -> dict:
    path = Path(config_path)
    if not path.exists():
        print(f"错误: 配置文件不存在: {path}")
        print("请先编辑 config.yaml，填入 API key 和联系人名称")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cmd_parse(args, config: dict) -> None:
    """解析聊天记录。"""
    parsed_dir = Path(config["paths"].get("parsed_logs", "data/chat_logs/parsed"))
    parsed_file = parsed_dir / f"{args.date}.json"

    # 已解析过，跳过
    if parsed_file.exists():
        print(f"已存在解析文件: {parsed_file}，跳过解析")
        return

    raw_dir = Path(config["paths"].get("raw_logs", "data/chat_logs/raw"))
    raw_file = raw_dir / f"{args.date}.txt"

    if not raw_file.exists():
        # 尝试查找其他扩展名
        candidates = list(raw_dir.glob(f"{args.date}.*"))
        if candidates:
            raw_file = candidates[0]
        else:
            # 可能是单个全量导出文件，尝试从中提取指定日期
            all_files = list(raw_dir.glob("*"))
            for f in all_files:
                if f.suffix in (".json", ".txt"):
                    try:
                        parser = ChatParser(contact_name=config.get("contact_name", ""))
                        all_msgs = parser.parse(f)
                        # 按日期过滤
                        date_msgs = [m for m in all_msgs if m["time"].startswith(args.date)]
                        if date_msgs:
                            parser.save_parsed(date_msgs, parsed_file)
                            print(f"从 {f.name} 提取: {len(date_msgs)} 条消息 → {parsed_file}")
                            return
                    except Exception:
                        continue
            print(f"错误: 未找到 {args.date} 的聊天记录")
            print(f"请将文件放到: {raw_dir}")
            sys.exit(1)

    parser = ChatParser(contact_name=config.get("contact_name", ""))
    messages = parser.parse(raw_file)
    parser.save_parsed(messages, parsed_file)

    print(f"解析完成: {len(messages)} 条消息 → {parsed_file}")


def cmd_summarize(args, config: dict) -> None:
    """生成每日总结。"""
    summarizer = Summarizer()
    summary = summarizer.generate_summary(args.date)
    print("=" * 60)
    print("【每日总结】")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    if not args.dry:
        summarizer.write_to_diary(args.date, summary)


def cmd_evaluate(args, config: dict) -> None:
    """评估聊天质量。"""
    evaluator = Evaluator()
    try:
        result = evaluator.evaluate(args.date)
        evaluator.save_scores(result)
        print(evaluator.format_result(result))
    except FileNotFoundError:
        print("请先运行 parse 解析聊天记录: python main.py parse --date ...")
        sys.exit(1)


def cmd_portrait(args, config: dict) -> None:
    """更新人物画像。"""
    updater = PortraitUpdater()

    if getattr(args, "show", False):
        print(updater.review_existing())
        return

    try:
        new_info = updater.extract_info(args.date)
        print("提取到的信息:")
        for cat, items in new_info.items():
            if items:
                print(f"  [{cat}]")
                for item in items:
                    print(f"    - {item}")

        if not args.dry and any(new_info.values()):
            added = updater.update_portrait(new_info)
            if added:
                print("\n已写入画像:")
                for item in added:
                    print(f"  + {item}")
            else:
                print("\n未发现可写入的新信息（可能已存在）。")
    except FileNotFoundError:
        print("请先运行 parse 解析聊天记录: python main.py parse --date ...")
        sys.exit(1)


def cmd_all(args, config: dict) -> None:
    """运行全流程（parse → summarize → evaluate → portrait）。"""
    print(f"\n{'='*40}")
    print(f"  全流程分析: {args.date}")
    print(f"{'='*40}\n")

    # 1. Parse
    print("[1/4] 解析聊天记录...")
    cmd_parse(args, config)

    # 2. Summarize
    print("\n[2/4] 生成每日总结...")
    cmd_summarize(args, config)

    # 3. Evaluate
    print("\n[3/4] 评估聊天质量...")
    cmd_evaluate(args, config)

    # 4. Portrait
    print("\n[4/4] 更新人物画像...")
    cmd_portrait(args, config)

    print(f"\n{'='*40}")
    print("  全流程完成 ✓")
    print(f"{'='*40}\n")


def cmd_stage(args, config: dict) -> None:
    """阶段性全量分析报告。"""
    analyzer = StageAnalyzer()
    try:
        report = analyzer.analyze()
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}")
        sys.exit(1)

    print("=" * 60)
    print("         阶段性分析报告")
    print("=" * 60)
    print(report)
    print("=" * 60)

    if not args.dry:
        path = analyzer.save_report(report)
        print(f"\n已保存: {path}")


def cmd_report(args, config: dict) -> None:
    """生成长期趋势报告。"""
    scores_path = Path(config["paths"].get("scores", "data/scores.json"))
    if not scores_path.exists():
        print("暂无评分数据。请先运行 evaluate 积累数据。")
        sys.exit(1)

    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    if len(scores) < 2:
        print("数据不足（需要至少 2 天的评分数据）。")
        sys.exit(1)

    from modules.reporter import Reporter

    reporter = Reporter(config)
    report = reporter.generate(scores)
    print(report)

    if not args.dry:
        reporter.save(report)


def main():
    parser = argparse.ArgumentParser(
        description="聊天记录评估系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py parse --date 2026-07-10     仅解析聊天记录
  python main.py --date 2026-07-10           全流程分析
  python main.py --date 2026-07-10 --dry     预览所有结果，不写入文件
  python main.py eval --date 2026-07-10      仅评估聊天质量
  python main.py report                      生成长期趋势报告
  python main.py portrait --show             查看当前人物画像
        """,
    )

    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析日期 (默认今天), 格式: 2026-07-10",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="预览模式，不写入文件",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径 (默认 config.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    subparsers.add_parser("parse", help="仅解析聊天记录")
    subparsers.add_parser("eval", help="仅评估聊天质量")
    subparsers.add_parser("portrait", help="更新人物画像")
    subparsers.add_parser(
        "portrait-show", help="查看当前画像"
    ).add_argument("--show", action="store_true", default=True)
    subparsers.add_parser("stage", help="阶段性全量分析报告")
    subparsers.add_parser("report", help="生成长期趋势报告")

    args = parser.parse_args()
    config = load_config(args.config)

    # 处理特殊子命令
    if args.command == "stage":
        cmd_stage(args, config)
        return

    if args.command == "report":
        cmd_report(args, config)
        return

    if args.command == "portrait-show":
        cmd_portrait(argparse.Namespace(date="", show=True, dry=True), config)
        return

    # 如果有子命令，仅执行该命令
    if args.command == "parse":
        cmd_parse(args, config)
    elif args.command == "eval":
        cmd_evaluate(args, config)
    elif args.command == "portrait":
        cmd_portrait(args, config)
    else:
        # 默认: 全流程
        cmd_all(args, config)


if __name__ == "__main__":
    main()
