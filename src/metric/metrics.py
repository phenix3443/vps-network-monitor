#!/usr/bin/env python3

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import List, Optional

from src.log.logger import setup_logger

logger = setup_logger("metrics")

ping_total = Counter(
    "vps_ping_total",
    "Ping 测试总数",
    ["vps_name", "provider", "region", "status"],
)

ping_latency = Histogram(
    "vps_ping_latency_ms",
    "Ping 延迟（毫秒）",
    ["vps_name", "provider", "region"],
    buckets=[10, 25, 50, 100, 200, 500, 1000, 2000, 5000],
)

ping_packet_loss = Gauge(
    "vps_ping_packet_loss_percent",
    "Ping 丢包率（百分比）",
    ["vps_name", "provider", "region"],
)

mtr_hops_total = Counter(
    "vps_mtr_hops_total",
    "MTR 路径跳数",
    ["vps_name", "provider", "region"],
)

mtr_hop_latency = Histogram(
    "vps_mtr_hop_latency_ms",
    "MTR 每跳延迟（毫秒）",
    ["vps_name", "provider", "region", "hop"],
    buckets=[1, 5, 10, 25, 50, 100, 200, 500, 1000],
)

test_duration = Histogram(
    "vps_test_duration_seconds",
    "测试耗时（秒）",
    ["vps_name", "provider", "region"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

errors_total = Counter(
    "vps_errors_total",
    "错误计数",
    ["error_type", "vps_name"],
)

config_reload_total = Counter(
    "vps_config_reload_total",
    "配置重载次数",
)

vps_info = Info(
    "vps_info",
    "VPS 信息",
)


class Metrics:
    def __init__(self):
        self._registered_vps = set()

    def record_ping_result(
        self,
        vps_name: str,
        provider: str,
        region: str,
        latency_ms: Optional[float],
        packet_loss: float,
        success: bool,
    ):
        status = "success" if success else "failed"
        ping_total.labels(
            vps_name=vps_name,
            provider=provider,
            region=region,
            status=status,
        ).inc()

        if latency_ms is not None:
            ping_latency.labels(
                vps_name=vps_name,
                provider=provider,
                region=region,
            ).observe(latency_ms)

        ping_packet_loss.labels(
            vps_name=vps_name,
            provider=provider,
            region=region,
        ).set(packet_loss)

    def record_mtr_result(
        self,
        vps_name: str,
        provider: str,
        region: str,
        hops: List,
    ):
        mtr_hops_total.labels(
            vps_name=vps_name,
            provider=provider,
            region=region,
        ).inc(len(hops))

        for hop in hops:
            if hop.avg is not None:
                mtr_hop_latency.labels(
                    vps_name=vps_name,
                    provider=provider,
                    region=region,
                    hop=str(hop.hop),
                ).observe(hop.avg)

    def record_error(self, error_type: str, vps_name: str = "unknown"):
        errors_total.labels(error_type=error_type, vps_name=vps_name).inc()

    def record_config_reload(self):
        config_reload_total.inc()

    def record_vps_info(
        self,
        vps_name: str,
        provider: str,
        region: str,
        ip: str,
    ):
        vps_key = f"{vps_name}:{provider}:{region}"
        if vps_key not in self._registered_vps:
            vps_info.labels(
                vps_name=vps_name,
                provider=provider,
                region=region,
                ip=ip,
            ).info(
                {
                    "vps_name": vps_name,
                    "provider": provider,
                    "region": region,
                    "ip": ip,
                }
            )
            self._registered_vps.add(vps_key)


metrics = Metrics()
