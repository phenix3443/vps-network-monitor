#!/usr/bin/env python3

import subprocess
import sys
import statistics
from datetime import datetime
from typing import Optional, List

from src.tester.models import PingResult, MtrResult, MtrHop, VPSTestResult
from src.log.logger import setup_logger

logger = setup_logger("vps_tester")


class VPSTester:
    def __init__(self):
        pass

    def _parse_ping_output_unix(self, output: str) -> tuple[List[float], float]:
        times = []
        packet_loss = 0.0

        for line in output.split("\n"):
            if "time=" in line or "time<" in line:
                try:
                    time_str = line.split("time=")[1].split()[0]
                    times.append(float(time_str))
                except (IndexError, ValueError):
                    pass
            elif "packet loss" in line:
                try:
                    loss_str = line.split("%")[0].split()[-1]
                    packet_loss = float(loss_str)
                except (IndexError, ValueError):
                    pass

        return times, packet_loss

    def _parse_ping_output_windows(self, output: str) -> tuple[List[float], float]:
        times = []
        packet_loss = 0.0

        for line in output.split("\n"):
            if "time=" in line or "time<" in line:
                try:
                    time_str = line.split("time=")[1].split()[0]
                    times.append(float(time_str.replace("ms", "")))
                except (IndexError, ValueError):
                    pass
            elif "Lost" in line:
                try:
                    parts = line.split("(")
                    if len(parts) > 1:
                        loss_str = parts[1].split("%")[0]
                        packet_loss = float(loss_str)
                except (IndexError, ValueError):
                    pass

        return times, packet_loss

    def _parse_ping_result(self, output: str, host: str) -> PingResult:
        if sys.platform == "win32":
            times, packet_loss = self._parse_ping_output_windows(output)
        else:
            times, packet_loss = self._parse_ping_output_unix(output)

        if not times:
            error_msg = "无法解析 ping 结果"
            logger.warning(f"Ping {host}: {error_msg}")
            return PingResult(success=False, error=error_msg)

        return PingResult(
            success=True,
            min=min(times),
            max=max(times),
            avg=statistics.mean(times),
            median=statistics.median(times),
            packet_loss=packet_loss,
            samples=len(times),
        )

    def ping_host(self, host: str, count: int = 10, interval: float = 1.0) -> PingResult:
        try:
            if sys.platform == "win32":
                cmd = ["ping", "-n", str(count), "-w", "1000", host]
            else:
                cmd = ["ping", "-c", str(count), "-i", str(interval), host]

            logger.debug(f"执行 ping 命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=count * interval + 5
            )

            if result.returncode != 0:
                error_msg = f"Ping 失败: {result.stderr}"
                logger.warning(f"Ping {host}: {error_msg}")
                return PingResult(success=False, error=error_msg)

            return self._parse_ping_result(result.stdout, host)

        except subprocess.TimeoutExpired:
            error_msg = "Ping 超时"
            logger.warning(f"Ping {host}: {error_msg}")
            return PingResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ping {host} 发生异常: {error_msg}", exc_info=True)
            return PingResult(success=False, error=error_msg)

    def _parse_mtr_raw_output(self, output: str, count: int) -> Optional[MtrResult]:
        hops = []
        for line in output.split("\n"):
            if not line.startswith("H "):
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            try:
                hop_num = int(parts[1])
                hop_ip = parts[2]
                sent = int(parts[3])
                last = float(parts[4]) if parts[4] != "0.0" else None
                avg = float(parts[5]) if parts[5] != "0.0" else None
                best = float(parts[6]) if parts[6] != "0.0" else None
                worst = float(parts[7]) if parts[7] != "0.0" else None

                hops.append(
                    MtrHop(
                        hop=hop_num,
                        ip=hop_ip,
                        sent=sent,
                        last=last,
                        avg=avg,
                        best=best,
                        worst=worst,
                        loss=(count - sent) / count * 100 if count > 0 else 0,
                    )
                )
            except (ValueError, IndexError):
                continue

        if not hops:
            return None

        return MtrResult(
            success=True,
            hops=hops,
            total_hops=len(hops),
            destination=None,
        )

    def _parse_mtr_report_output(self, output: str, count: int) -> Optional[MtrResult]:
        hops = []
        for line in output.split("\n"):
            if not line.strip() or line.startswith("HOST:"):
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            try:
                hop_ip = parts[0]
                loss = 0.0
                if "%" in line:
                    loss_str = line.split("%")[0].split()[-1]
                    loss = float(loss_str)

                avg = None
                for i, part in enumerate(parts):
                    if "Avg" in part or i > 0:
                        try:
                            avg_str = parts[i + 1] if i + 1 < len(parts) else None
                            if avg_str:
                                avg = float(avg_str.replace("ms", ""))
                            break
                        except (ValueError, IndexError):
                            continue

                hops.append(
                    MtrHop(
                        hop=len(hops) + 1,
                        ip=hop_ip,
                        sent=count,
                        avg=avg,
                        loss=loss,
                    )
                )
            except (ValueError, IndexError):
                continue

        if not hops:
            return None

        return MtrResult(
            success=True,
            hops=hops,
            total_hops=len(hops),
            destination=None,
        )

    def mtr_host(self, host: str, count: int = 10) -> MtrResult:
        if sys.platform == "win32":
            logger.error("Windows 系统暂不支持 MTR")
            return MtrResult(success=False, error="Windows 系统暂不支持 MTR，请使用 Linux/macOS")

        try:
            cmd = [
                "mtr",
                "--report",
                "--report-cycles",
                str(count),
                "--no-dns",
                "--raw",
                host,
            ]

            logger.debug(f"执行 MTR 命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=count * 2 + 10)

            if result.returncode == 0:
                mtr_result = self._parse_mtr_raw_output(result.stdout, count)
                if mtr_result:
                    mtr_result.destination = host
                    return mtr_result

            cmd = ["mtr", "--report", "--report-cycles", str(count), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=count * 2 + 10)

            if result.returncode == 0:
                mtr_result = self._parse_mtr_report_output(result.stdout, count)
                if mtr_result:
                    mtr_result.destination = host
                    return mtr_result

            error_msg = f"MTR 失败: {result.stderr}"
            logger.warning(f"MTR {host}: {error_msg}")
            return MtrResult(success=False, error=error_msg)

        except subprocess.TimeoutExpired:
            error_msg = "MTR 超时"
            logger.warning(f"MTR {host}: {error_msg}")
            return MtrResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"MTR {host} 发生异常: {error_msg}", exc_info=True)
            return MtrResult(success=False, error=error_msg)

    def test_domain(
        self,
        domain: str,
        name: str = None,
        provider: str = "Unknown",
        region: str = "Unknown",
        ping_count: int = 10,
        use_mtr: bool = False,
    ) -> VPSTestResult:
        if name is None:
            name = domain

        logger.info(f"开始测试域名: {name} ({domain})")

        ping_result = self.ping_host(domain, count=ping_count)

        if ping_result.success:
            logger.info(
                f"{name} ping 成功 - "
                f"平均延迟: {ping_result.avg:.2f}ms, "
                f"丢包率: {ping_result.packet_loss:.1f}%"
            )
        else:
            logger.warning(f"{name} ping 失败: {ping_result.error}")

        mtr_result = None
        if use_mtr:
            logger.debug(f"执行 MTR 路径追踪: {name}")
            mtr_result = self.mtr_host(domain, count=ping_count)

            if mtr_result.success:
                logger.info(f"{name} MTR 成功 - 路径跳数: {mtr_result.total_hops}")
                if mtr_result.hops:
                    first_hop = mtr_result.hops[0]
                    last_hop = mtr_result.hops[-1]
                    if first_hop.avg:
                        logger.debug(f"{name} 第一跳延迟: {first_hop.avg:.2f} ms")
                    if last_hop.avg:
                        logger.debug(f"{name} 最后一跳延迟: {last_hop.avg:.2f} ms")
            else:
                logger.warning(f"{name} MTR 测试失败: {mtr_result.error}")

        return VPSTestResult(
            timestamp=datetime.now().isoformat(),
            name=name,
            provider=provider,
            region=region,
            ip=domain,
            ping=ping_result,
            mtr=mtr_result,
        )
