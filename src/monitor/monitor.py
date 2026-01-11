#!/usr/bin/env python3

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.tester import VPSTester, VPSTestResult
from src.tester.models import TestSession
from src.log.logger import setup_logger
from src.metric.metrics import metrics

logger = setup_logger("vps_monitor")


class VPSMonitor:
    def __init__(self, config_file: str = "config/vps.json"):
        self.config_file = config_file
        self.vps_list = self.load_config()
        self.results: List[VPSTestResult] = []
        self.current_session: Optional[TestSession] = None
        self.tester = VPSTester()
        self._register_vps_info()

    def load_config(self) -> List[Dict]:
        config_path = Path(self.config_file)

        if not config_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / self.config_file

        if not config_path.exists():
            logger.warning(f"配置文件 {config_path} 不存在，将创建示例配置")
            self.create_sample_config(config_path)
            return []

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                vps_list = config.get("vps_list", [])
                logger.info(f"成功加载配置文件，包含 {len(vps_list)} 个 VPS 节点")
                return vps_list
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 {config_path} 格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            metrics.record_error("config_load_error")
            return []

    def create_sample_config(self, config_path: Path):
        config_path.parent.mkdir(parents=True, exist_ok=True)
        sample_config = {
            "vps_list": [
                {
                    "name": "Hetzner-德国",
                    "ip": "example.com",
                    "provider": "Hetzner",
                    "region": "德国",
                },
                {
                    "name": "Vultr-日本",
                    "ip": "example.com",
                    "provider": "Vultr",
                    "region": "日本东京",
                },
                {
                    "name": "阿里云-香港",
                    "ip": "example.com",
                    "provider": "阿里云",
                    "region": "香港",
                },
            ],
            "ping_count": 10,
            "ping_interval": 1,
            "monitor_interval": 60,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(sample_config, f, ensure_ascii=False, indent=2)
        logger.info(f"已创建示例配置文件: {config_path}")
        logger.info("请编辑配置文件，填入实际的 VPS IP 地址")

    def test_vps(self, vps: Dict, ping_count: int = 10, use_mtr: bool = False) -> VPSTestResult:
        vps_name = vps.get("name", "Unknown")
        vps_ip = vps.get("ip", "N/A")
        provider = vps.get("provider", "Unknown")
        region = vps.get("region", "Unknown")

        result = self.tester.test_domain(
            domain=vps_ip,
            name=vps_name,
            provider=provider,
            region=region,
            ping_count=ping_count,
            use_mtr=use_mtr,
        )

        if result.ping.success:
            metrics.record_ping_result(
                vps_name, provider, region, result.ping.avg, result.ping.packet_loss, True
            )
        else:
            metrics.record_ping_result(vps_name, provider, region, None, 100.0, False)

        if result.mtr and result.mtr.success:
            metrics.record_mtr_result(vps_name, provider, region, result.mtr.hops)

        return result

    def run_once(self, ping_count: int = 10, use_mtr: bool = False) -> TestSession:
        session_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()

        logger.info("=" * 60)
        logger.info(f"开始测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"测试节点数: {len(self.vps_list)}")
        if use_mtr:
            logger.info("MTR 路径追踪: 已启用")
        logger.info("=" * 60)

        results = []
        for i, vps in enumerate(self.vps_list, 1):
            logger.info(f"[{i}/{len(self.vps_list)}] 测试节点: {vps.get('name', 'Unknown')}")
            result = self.test_vps(vps, ping_count, use_mtr=use_mtr)
            results.append(result)
            self.results.append(result)
            if i < len(self.vps_list):
                time.sleep(1)

        end_time = datetime.now().isoformat()
        successful_tests = sum(1 for r in results if r.ping.success)
        failed_tests = len(results) - successful_tests

        session = TestSession(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            total_tests=len(results),
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            results=results,
        )

        self.current_session = session
        return session

    def run_continuous(self, interval: int = 60, ping_count: int = 10, use_mtr: bool = False):
        logger.info(f"开始持续监控模式，间隔: {interval} 秒")
        if use_mtr:
            logger.info("MTR 路径追踪: 已启用")
        logger.info("按 Ctrl+C 停止监控")

        try:
            while True:
                self.run_once(ping_count, use_mtr=use_mtr)
                self.print_summary()
                logger.info(f"等待 {interval} 秒后进行下一次测试...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("监控已停止")
            self.save_results()

    def save_results(self, filename: Optional[str] = None, format: str = "json"):
        if not self.results:
            logger.warning("没有测试结果可保存")
            return

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitor_results_{timestamp}.{format}"

        if format == "json":
            if self.current_session:
                data = self.current_session.to_dict()
            else:
                data = [r.to_dict() for r in self.results]

            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON 结果已保存到: {filename}")
        else:
            from src.reports import ReporterFactory

            if not self.current_session:
                session_id = str(uuid.uuid4())
                successful_tests = sum(1 for r in self.results if r.ping.success)
                self.current_session = TestSession(
                    session_id=session_id,
                    start_time=datetime.now().isoformat(),
                    total_tests=len(self.results),
                    successful_tests=successful_tests,
                    failed_tests=len(self.results) - successful_tests,
                    results=self.results,
                )

            reporter = ReporterFactory.get_reporter(format)
            reporter.generate(self.current_session, filename)

    def print_summary(self):
        if not self.results:
            logger.warning("暂无测试结果")
            return

        logger.info("=" * 60)
        logger.info("测试结果摘要")
        logger.info("=" * 60)

        successful_results = [r for r in self.results if r.ping.success]
        successful_results.sort(key=lambda x: x.ping.avg or float("inf"))

        for result in successful_results:
            status = "正常" if result.ping.packet_loss < 5 else "高丢包"
            logger.info(
                f"VPS {result.name:<20} - "
                f"平均延迟: {result.ping.avg:>8.2f}ms, "
                f"丢包率: {result.ping.packet_loss:>6.1f}%, "
                f"状态: {status}"
            )

        failed_results = [r for r in self.results if not r.ping.success]
        for result in failed_results:
            logger.warning(f"VPS {result.name:<20} - 测试失败: {result.ping.error}")

    def _register_vps_info(self):
        try:
            for vps in self.vps_list:
                metrics.record_vps_info(
                    vps.get("name", "Unknown"),
                    vps.get("provider", "Unknown"),
                    vps.get("region", "Unknown"),
                    vps.get("ip", "N/A"),
                )
        except ValueError:
            pass
