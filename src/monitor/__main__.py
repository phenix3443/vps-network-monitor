#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.monitor import VPSMonitor
from src.log.logger import setup_logger

logger = setup_logger("monitor_main")


def main():
    parser = argparse.ArgumentParser(description="VPS 监控程序 - 根据配置文件监控所有 VPS 节点")
    parser.add_argument(
        "-c",
        "--config",
        default="config/vps.json",
        help="VPS 配置文件路径 (默认: config/vps.json)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=60,
        help="持续监控模式下的测试间隔（秒，默认: 60）",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=10, help="每次 ping 的次数 (默认: 10)"
    )
    parser.add_argument(
        "-o", "--once", action="store_true", help="只执行一次测试（不持续监控）"
    )
    parser.add_argument(
        "-s", "--save", type=str, help="保存结果到指定文件"
    )
    parser.add_argument(
        "--mtr", action="store_true", help="启用 MTR 路径追踪（需要安装 mtr 工具）"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="json",
        choices=["json", "html", "markdown", "md"],
        help="报告格式（默认: json）",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认: INFO）",
    )

    args = parser.parse_args()

    logger = setup_logger("vps_monitor", level=args.log_level)

    monitor = VPSMonitor(config_file=args.config)

    if not monitor.vps_list:
        logger.error("请先配置 VPS 列表")
        logger.info(f"提示: 编辑配置文件 {args.config}")
        return

    if args.once:
        session = monitor.run_once(args.count, use_mtr=args.mtr)
        monitor.print_summary()

        if args.save:
            monitor.save_results(args.save, format=args.format)
        else:
            monitor.save_results(format=args.format)
    else:
        monitor.run_continuous(args.interval, args.count, use_mtr=args.mtr)


if __name__ == "__main__":
    main()
