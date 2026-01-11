#!/usr/bin/env python3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from src.log.logger import setup_logger

logger = setup_logger("visualization")


class ResultVisualizer:
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def plot_ping_results(self, results: List[Dict], filename: Optional[str] = None) -> str:
        if not results:
            logger.warning("没有数据可绘制")
            return ""

        successful_results = [r for r in results if r.get("ping", {}).get("success", False)]

        if not successful_results:
            logger.warning("没有成功的 ping 结果可绘制")
            return ""

        names = [r.get("name", "Unknown") for r in successful_results]
        avg_latencies = [r["ping"].get("avg", 0) for r in successful_results]
        min_latencies = [r["ping"].get("min", 0) for r in successful_results]
        max_latencies = [r["ping"].get("max", 0) for r in successful_results]
        packet_losses = [r["ping"].get("packet_loss", 0) for r in successful_results]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle("VPS Ping 测试结果", fontsize=16, fontweight="bold")

        x_pos = range(len(names))
        width = 0.35

        ax1.bar(
            [x - width / 2 for x in x_pos], min_latencies, width, label="最小延迟", color="#2ecc71"
        )
        ax1.bar(
            [x - width / 2 for x in x_pos],
            [avg - min for avg, min in zip(avg_latencies, min_latencies)],
            width,
            bottom=min_latencies,
            label="平均延迟",
            color="#3498db",
        )
        ax1.bar(
            [x + width / 2 for x in x_pos],
            [max - avg for max, avg in zip(max_latencies, avg_latencies)],
            width,
            bottom=avg_latencies,
            label="最大延迟",
            color="#e74c3c",
        )

        ax1.set_xlabel("VPS 节点", fontsize=12)
        ax1.set_ylabel("延迟 (ms)", fontsize=12)
        ax1.set_title("延迟统计（最小/平均/最大）", fontsize=14)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(names, rotation=45, ha="right")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        colors = [
            "#2ecc71" if loss < 1 else "#f39c12" if loss < 5 else "#e74c3c"
            for loss in packet_losses
        ]
        ax2.bar(x_pos, packet_losses, color=colors, alpha=0.7)
        ax2.axhline(y=1, color="#f39c12", linestyle="--", label="警告阈值 (1%)")
        ax2.axhline(y=5, color="#e74c3c", linestyle="--", label="严重阈值 (5%)")

        ax2.set_xlabel("VPS 节点", fontsize=12)
        ax2.set_ylabel("丢包率 (%)", fontsize=12)
        ax2.set_title("丢包率统计", fontsize=14)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(names, rotation=45, ha="right")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ping_results_{timestamp}.png"

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Ping 图表已保存: {filepath}")
        return str(filepath)

    def plot_mtr_results(self, results: List[Dict], filename: Optional[str] = None) -> str:
        if not results:
            logger.warning("没有数据可绘制")
            return ""

        mtr_results = [r for r in results if r.get("mtr", {}).get("success", False)]

        if not mtr_results:
            logger.warning("没有成功的 MTR 结果可绘制")
            return ""

        num_vps = len(mtr_results)
        fig, axes = plt.subplots(num_vps, 1, figsize=(14, 4 * num_vps))
        if num_vps == 1:
            axes = [axes]

        fig.suptitle("MTR 路径追踪结果", fontsize=16, fontweight="bold")

        for idx, result in enumerate(mtr_results):
            ax = axes[idx]
            mtr_data = result["mtr"]
            hops = mtr_data.get("hops", [])

            if not hops:
                continue

            hop_numbers = [h["hop"] for h in hops]
            avg_delays = [h.get("avg", 0) if h.get("avg") is not None else 0 for h in hops]
            losses = [h.get("loss", 0) for h in hops]

            ax2 = ax.twinx()
            line1 = ax.plot(
                hop_numbers,
                avg_delays,
                "o-",
                color="#3498db",
                linewidth=2,
                markersize=8,
                label="平均延迟",
            )
            ax.set_xlabel("跳数 (Hop)", fontsize=10)
            ax.set_ylabel("延迟 (ms)", fontsize=10, color="#3498db")
            ax.tick_params(axis="y", labelcolor="#3498db")
            ax.grid(True, alpha=0.3)

            line2 = ax2.bar(hop_numbers, losses, alpha=0.3, color="#e74c3c", label="丢包率")
            ax2.set_ylabel("丢包率 (%)", fontsize=10, color="#e74c3c")
            ax2.tick_params(axis="y", labelcolor="#e74c3c")

            vps_name = result.get("name", "Unknown")
            ax.set_title(f"{vps_name} - 路径延迟和丢包率", fontsize=12, fontweight="bold")

            lines = line1 + [line2]
            labels = [line.get_label() for line in lines]
            ax.legend(lines, labels, loc="upper left")

        plt.tight_layout()

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mtr_results_{timestamp}.png"

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"MTR 图表已保存: {filepath}")
        return str(filepath)

    def plot_combined_results(self, results: List[Dict], filename: Optional[str] = None) -> str:
        if not results:
            logger.warning("没有数据可绘制")
            return ""

        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        ax1 = fig.add_subplot(gs[0, :])
        successful_results = [r for r in results if r.get("ping", {}).get("success", False)]
        if successful_results:
            names = [r.get("name", "Unknown") for r in successful_results]
            avg_latencies = [r["ping"].get("avg", 0) for r in successful_results]
            x_pos = range(len(names))
            ax1.bar(x_pos, avg_latencies, color="#3498db", alpha=0.7)
            ax1.set_xlabel("VPS 节点", fontsize=11)
            ax1.set_ylabel("平均延迟 (ms)", fontsize=11)
            ax1.set_title("各 VPS 平均延迟对比", fontsize=13, fontweight="bold")
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(names, rotation=45, ha="right")
            ax1.grid(True, alpha=0.3, axis="y")

        ax2 = fig.add_subplot(gs[1, 0])
        if successful_results:
            packet_losses = [r["ping"].get("packet_loss", 0) for r in successful_results]
            colors = [
                "#2ecc71" if loss < 1 else "#f39c12" if loss < 5 else "#e74c3c"
                for loss in packet_losses
            ]
            ax2.bar(x_pos, packet_losses, color=colors, alpha=0.7)
            ax2.axhline(y=1, color="#f39c12", linestyle="--", linewidth=1)
            ax2.axhline(y=5, color="#e74c3c", linestyle="--", linewidth=1)
            ax2.set_xlabel("VPS 节点", fontsize=11)
            ax2.set_ylabel("丢包率 (%)", fontsize=11)
            ax2.set_title("Ping 丢包率", fontsize=13, fontweight="bold")
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels(names, rotation=45, ha="right")
            ax2.grid(True, alpha=0.3, axis="y")

        ax3 = fig.add_subplot(gs[1, 1])
        mtr_results = [r for r in results if r.get("mtr", {}).get("success", False)]
        if mtr_results:
            mtr_names = [r.get("name", "Unknown") for r in mtr_results]
            hop_counts = [r["mtr"].get("total_hops", 0) for r in mtr_results]
            x_pos_mtr = range(len(mtr_names))
            ax3.bar(x_pos_mtr, hop_counts, color="#9b59b6", alpha=0.7)
            ax3.set_xlabel("VPS 节点", fontsize=11)
            ax3.set_ylabel("路径跳数", fontsize=11)
            ax3.set_title("MTR 路径跳数", fontsize=13, fontweight="bold")
            ax3.set_xticks(x_pos_mtr)
            ax3.set_xticklabels(mtr_names, rotation=45, ha="right")
            ax3.grid(True, alpha=0.3, axis="y")

        if mtr_results:
            ax4 = fig.add_subplot(gs[2, :])
            for result in mtr_results[:5]:
                mtr_data = result["mtr"]
                hops = mtr_data.get("hops", [])
                if hops:
                    hop_numbers = [h["hop"] for h in hops]
                    avg_delays = [h.get("avg", 0) if h.get("avg") is not None else 0 for h in hops]
                    ax4.plot(
                        hop_numbers,
                        avg_delays,
                        "o-",
                        label=result.get("name", "Unknown"),
                        linewidth=2,
                        markersize=6,
                    )

            ax4.set_xlabel("跳数 (Hop)", fontsize=11)
            ax4.set_ylabel("延迟 (ms)", fontsize=11)
            ax4.set_title("MTR 路径延迟对比（前 5 个节点）", fontsize=13, fontweight="bold")
            ax4.legend()
            ax4.grid(True, alpha=0.3)

        fig.suptitle("VPS 网络监控综合报告", fontsize=16, fontweight="bold", y=0.995)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_results_{timestamp}.png"

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"综合图表已保存: {filepath}")
        return str(filepath)
