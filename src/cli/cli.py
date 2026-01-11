#!/usr/bin/env python3

import argparse
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tester import VPSTester, VPSTestResult
from src.tester.models import TestSession
from src.log.logger import setup_logger
from src.reports import ReporterFactory

logger = setup_logger("cli")


def format_result(result: VPSTestResult) -> str:
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"测试结果: {result.name} ({result.ip})")
    output.append(f"{'='*60}")
    output.append(f"时间: {result.timestamp}")
    output.append(f"提供商: {result.provider}")
    output.append(f"地区: {result.region}")
    output.append(f"\nPing 测试:")
    if result.ping.success:
        output.append(f"  状态: ✓ 成功")
        output.append(f"  平均延迟: {result.ping.avg:.2f} ms")
        output.append(f"  最小延迟: {result.ping.min:.2f} ms")
        output.append(f"  最大延迟: {result.ping.max:.2f} ms")
        output.append(f"  中位数延迟: {result.ping.median:.2f} ms")
        output.append(f"  丢包率: {result.ping.packet_loss:.1f}%")
        output.append(f"  样本数: {result.ping.samples}")
    else:
        output.append(f"  状态: ✗ 失败")
        output.append(f"  错误: {result.ping.error}")

    if result.mtr:
        output.append(f"\nMTR 路径追踪:")
        if result.mtr.success:
            output.append(f"  状态: ✓ 成功")
            output.append(f"  总跳数: {result.mtr.total_hops}")
            output.append(f"  路径:")
            for hop in result.mtr.hops:
                hop_info = f"    {hop.hop}. {hop.ip}"
                if hop.avg:
                    hop_info += f" - 平均延迟: {hop.avg:.2f} ms"
                if hop.loss > 0:
                    hop_info += f" - 丢包率: {hop.loss:.1f}%"
                output.append(hop_info)
        else:
            output.append(f"  状态: ✗ 失败")
            output.append(f"  错误: {result.mtr.error}")

    output.append(f"{'='*60}\n")
    return "\n".join(output)


def load_config(config_file: str = "config/vps.json") -> List[Dict]:
    config_path = Path(config_file)
    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / config_file

    if not config_path.exists():
        logger.error(f"配置文件 {config_path} 不存在")
        return []

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            vps_list = config.get("vps_list", [])
            logger.info(f"成功加载配置文件，包含 {len(vps_list)} 个 VPS 节点")
            return vps_list
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        return []
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return []


def save_report(result: VPSTestResult, output_file: str, format: str = "json"):
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format in ["json", "html", "markdown", "md"]:
        session = TestSession(
            session_id=str(uuid.uuid4()),
            start_time=result.timestamp,
            end_time=datetime.now().isoformat(),
            total_tests=1,
            successful_tests=1 if result.ping.success else 0,
            failed_tests=0 if result.ping.success else 1,
            results=[result],
        )

        reporter = ReporterFactory.get_reporter(format)
        reporter.generate(session, output_file)
        logger.info(f"报告已保存到: {output_file}")
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(format_result(result))
        logger.info(f"结果已保存到: {output_file}")


def save_session_report(session: TestSession, output_file: str, format: str = "json"):
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format in ["json", "html", "markdown", "md"]:
        reporter = ReporterFactory.get_reporter(format)
        reporter.generate(session, output_file)
        logger.info(f"报告已保存到: {output_file}")
    else:
        logger.warning(f"格式 {format} 不支持批量测试结果，使用 JSON 格式保存")
        reporter = ReporterFactory.get_reporter("json")
        reporter.generate(session, output_file)
        logger.info(f"报告已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="VPS 域名节点测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试单个域名
  python -m src.cli example.com

  # 测试域名并启用 MTR
  python -m src.cli example.com --mtr

  # 测试域名并指定名称和提供商
  python -m src.cli example.com --name "测试节点" --provider "Vultr" --region "日本东京"

  # 测试并保存为 JSON 报告
  python -m src.cli example.com --output result.json --format json

  # 从配置文件测试所有节点
  python -m src.cli --config config/vps.json

  # 从配置文件测试所有节点并启用 MTR
  python -m src.cli --config --mtr

  # 从配置文件测试所有节点并保存为 HTML 报告
  python -m src.cli --config --output results.html --format html
        """,
    )

    parser.add_argument(
        "domain",
        nargs="?",
        help="要测试的 VPS 域名或 IP 地址（如果提供了 --config，则忽略此参数）",
    )

    parser.add_argument(
        "-n",
        "--name",
        type=str,
        help="VPS 节点名称（默认使用域名）",
    )

    parser.add_argument(
        "-p",
        "--provider",
        type=str,
        default="Unknown",
        help="VPS 提供商（默认: Unknown）",
    )

    parser.add_argument(
        "-r",
        "--region",
        type=str,
        default="Unknown",
        help="VPS 地区（默认: Unknown）",
    )

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=10,
        help="Ping 测试次数（默认: 10）",
    )

    parser.add_argument(
        "--mtr",
        action="store_true",
        help="启用 MTR 路径追踪（需要安装 mtr 工具）",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="输出文件路径（可选）",
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="text",
        choices=["text", "json", "html", "markdown", "md"],
        help="输出格式（默认: text）",
    )

    parser.add_argument(
        "--config",
        type=str,
        nargs="?",
        const="config/vps.json",
        help="从配置文件测试所有节点（默认: config/vps.json）",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认: INFO）",
    )

    args = parser.parse_args()

    logger = setup_logger("vps_cli", level=args.log_level)
    tester = VPSTester()

    if args.config is not None:
        config_file = args.config
        vps_list = load_config(config_file)

        if not vps_list:
            logger.error("配置文件为空或加载失败")
            sys.exit(1)

        logger.info(f"开始测试配置文件中的所有节点（共 {len(vps_list)} 个）")

        results: List[VPSTestResult] = []
        start_time = datetime.now().isoformat()

        for i, vps in enumerate(vps_list, 1):
            vps_name = vps.get("name", "Unknown")
            vps_ip = vps.get("ip", "N/A")
            provider = vps.get("provider", "Unknown")
            region = vps.get("region", "Unknown")

            logger.info(f"[{i}/{len(vps_list)}] 测试: {vps_name} ({vps_ip})")

            result = tester.test_domain(
                domain=vps_ip,
                name=vps_name,
                provider=provider,
                region=region,
                ping_count=args.count,
                use_mtr=args.mtr,
            )

            results.append(result)
            print(format_result(result))

        end_time = datetime.now().isoformat()
        successful_tests = sum(1 for r in results if r.ping.success)
        failed_tests = len(results) - successful_tests

        session = TestSession(
            session_id=str(uuid.uuid4()),
            start_time=start_time,
            end_time=end_time,
            total_tests=len(results),
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            results=results,
        )

        logger.info(f"\n测试完成: 成功 {successful_tests}/{len(results)}, 失败 {failed_tests}/{len(results)}")

        if args.output:
            save_session_report(session, args.output, args.format)
        else:
            if args.format == "text":
                default_output = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                save_session_report(session, default_output, "markdown")
            else:
                default_output = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"
                save_session_report(session, default_output, args.format)

        sys.exit(0 if failed_tests == 0 else 1)
    else:
        if not args.domain:
            parser.error("必须提供 domain 参数或使用 --config 参数")

        logger.info(f"开始测试域名: {args.domain}")

        result = tester.test_domain(
            domain=args.domain,
            name=args.name or args.domain,
            provider=args.provider,
            region=args.region,
            ping_count=args.count,
            use_mtr=args.mtr,
        )

        print(format_result(result))

        if args.output:
            save_report(result, args.output, args.format)
        elif args.format != "text":
            default_output = f"test_result_{args.domain.replace('.', '_')}.{args.format}"
            save_report(result, default_output, args.format)

        sys.exit(0 if result.ping.success else 1)


if __name__ == "__main__":
    main()
