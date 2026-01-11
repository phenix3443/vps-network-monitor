#!/usr/bin/env python3

import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path

from src.monitor import VPSMonitor
from src.tester import VPSTester, VPSTestResult
from src.tester.models import TestSession
from src.utils.location_utils import add_location_to_vps
from src.log.logger import setup_logger

logger = setup_logger("api_server")

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

monitor_instance: Optional[VPSMonitor] = None
tester_instance: Optional[VPSTester] = None


def init_monitor(config_file: str = "config/vps.json"):
    global monitor_instance
    if monitor_instance is None:
        monitor_instance = VPSMonitor(config_file)
    return monitor_instance


def get_tester():
    global tester_instance
    if tester_instance is None:
        tester_instance = VPSTester()
    return tester_instance


@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")


@app.route("/api/status")
def get_status():
    """获取服务状态"""
    monitor = init_monitor()
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "vps_count": len(monitor.vps_list) if monitor else 0,
    })


@app.route("/api/vps/list")
def get_vps_list():
    """获取VPS列表"""
    monitor = init_monitor()
    vps_list = []
    for vps in monitor.vps_list:
        vps_with_location = add_location_to_vps(vps.copy())
        vps_data = {
            "name": vps_with_location.get("name"),
            "provider": vps_with_location.get("provider", "Unknown"),
            "region": vps_with_location.get("region", "Unknown"),
            "ip": vps_with_location.get("ip", "N/A"),
            "location": vps_with_location.get("location"),
        }
        vps_list.append(vps_data)
    return jsonify({"vps_list": vps_list})


@app.route("/api/results")
def get_results():
    """获取 monitor 的测试结果"""
    monitor = init_monitor()
    if monitor.current_session:
        return jsonify(monitor.current_session.to_dict())
    elif monitor.results:
        return jsonify({
            "session_id": "latest",
            "start_time": datetime.now().isoformat(),
            "results": [r.to_dict() for r in monitor.results],
        })
    else:
        return jsonify({"error": "No results available"}), 404


@app.route("/api/results/latest")
def get_latest_results():
    """获取最新测试结果（简化版，用于地图展示）"""
    monitor = init_monitor()
    if not monitor.results:
        return jsonify({"results": []})

    results = []
    for result in monitor.results:
        results.append({
            "name": result.name,
            "provider": result.provider,
            "region": result.region,
            "ip": result.ip,
            "ping": {
                "success": result.ping.success,
                "avg": result.ping.avg,
                "packet_loss": result.ping.packet_loss,
            },
            "mtr": result.mtr.to_dict() if result.mtr else None,
        })
    return jsonify({"results": results})


@app.route("/api/test/domain", methods=["POST"])
def test_domain():
    """测试前端传递的 VPS 节点域名（调用 tester 模块）"""
    data = request.get_json() or {}
    domain = data.get("domain")
    
    if not domain:
        return jsonify({"success": False, "error": "domain parameter is required"}), 400

    name = data.get("name", domain)
    provider = data.get("provider", "Unknown")
    region = data.get("region", "Unknown")
    ping_count = data.get("ping_count", 10)
    use_mtr = data.get("use_mtr", False)

    try:
        tester = get_tester()
        result = tester.test_domain(
            domain=domain,
            name=name,
            provider=provider,
            region=region,
            ping_count=ping_count,
            use_mtr=use_mtr,
        )
        return jsonify({
            "success": True,
            "result": result.to_dict(),
        })
    except Exception as e:
        logger.error(f"测试域名失败: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test/run", methods=["POST"])
def run_test():
    """执行一次测试（测试所有配置的 VPS 节点）"""
    monitor = init_monitor()
    data = request.get_json() or {}
    ping_count = data.get("ping_count", 10)
    use_mtr = data.get("use_mtr", False)

    try:
        session = monitor.run_once(ping_count=ping_count, use_mtr=use_mtr)
        return jsonify({
            "success": True,
            "session": session.to_dict(),
        })
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test/start", methods=["POST"])
def start_continuous_test():
    """启动持续测试"""
    data = request.get_json() or {}
    interval = data.get("interval", 60)
    ping_count = data.get("ping_count", 10)
    use_mtr = data.get("use_mtr", False)

    return jsonify({
        "success": True,
        "message": "持续测试功能需要在CLI模式下使用",
    })


@app.route("/api/config/reload", methods=["POST"])
def reload_config():
    """重新加载配置"""
    global monitor_instance
    monitor_instance = None
    monitor = init_monitor()
    return jsonify({
        "success": True,
        "vps_count": len(monitor.vps_list),
    })


@app.route("/api/health")
def health():
    """健康检查"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="VPS Monitor API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--config", default="config/vps.json", help="Config file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    init_monitor(args.config)
    logger.info(f"Starting API server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
