#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from jinja2 import Template

from src.tester.models import TestSession, VPSTestResult
from src.log.logger import setup_logger

logger = setup_logger("reporters")


class BaseReporter:
    def generate(self, session: TestSession, output_path: Optional[str] = None) -> str:
        raise NotImplementedError


class JSONReporter(BaseReporter):
    def generate(self, session: TestSession, output_path: Optional[str] = None) -> str:
        data = session.to_dict()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"JSON 报告已保存: {output_file}")
            return str(output_file)

        return json_str


class MarkdownReporter(BaseReporter):
    def generate(self, session: TestSession, output_path: Optional[str] = None) -> str:
        lines = []
        lines.append(f"# VPS 网络监控报告")
        lines.append("")
        lines.append(f"**会话 ID**: {session.session_id}")
        lines.append(f"**开始时间**: {session.start_time}")
        if session.end_time:
            lines.append(f"**结束时间**: {session.end_time}")
        lines.append(f"**测试总数**: {session.total_tests}")
        lines.append(f"**成功**: {session.successful_tests}")
        lines.append(f"**失败**: {session.failed_tests}")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 测试结果汇总")
        lines.append("")
        lines.append("| VPS 名称 | 提供商 | 区域 | IP | 状态 | 平均延迟 (ms) | 最小延迟 (ms) | 最大延迟 (ms) | 丢包率 (%) | 错误信息 |")
        lines.append("|---------|--------|------|-----|------|--------------|--------------|--------------|-----------|---------|")

        sorted_results = sorted(
            session.results,
            key=lambda x: (not x.ping.success, x.ping.avg if x.ping.success and x.ping.avg else float("inf"))
        )

        for result in sorted_results:
            if result.ping.success:
                status = "✓ 成功"
                avg_delay = f"{result.ping.avg:.2f}" if result.ping.avg else "N/A"
                min_delay = f"{result.ping.min:.2f}" if result.ping.min else "N/A"
                max_delay = f"{result.ping.max:.2f}" if result.ping.max else "N/A"
                packet_loss = f"{result.ping.packet_loss:.1f}"
                error = "-"
            else:
                status = "✗ 失败"
                avg_delay = "-"
                min_delay = "-"
                max_delay = "-"
                packet_loss = "-"
                error = result.ping.error or "未知错误"

            lines.append(
                f"| {result.name} | {result.provider} | {result.region} | {result.ip} | "
                f"{status} | {avg_delay} | {min_delay} | {max_delay} | {packet_loss} | {error} |"
            )

        lines.append("")

        mtr_results = [r for r in session.results if r.mtr and r.mtr.success]
        if mtr_results:
            lines.append("## MTR 路径追踪结果")
            lines.append("")
            for result in mtr_results:
                lines.append(f"### {result.name} ({result.mtr.destination})")
                lines.append(f"**总跳数**: {result.mtr.total_hops}")
                lines.append("")
                lines.append("| 跳数 | IP | 平均延迟 (ms) | 丢包率 (%) |")
                lines.append("|------|-----|--------------|-----------|")
                for hop in result.mtr.hops:
                    avg_str = f"{hop.avg:.2f}" if hop.avg else "N/A"
                    lines.append(f"| {hop.hop} | {hop.ip} | {avg_str} | {hop.loss:.1f} |")
                lines.append("")

        markdown_str = "\n".join(lines)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_str)
            logger.info(f"Markdown 报告已保存: {output_file}")
            return str(output_file)

        return markdown_str


class HTMLReporter(BaseReporter):
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPS 网络监控报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .success {
            color: #28a745;
        }
        .warning {
            color: #ffc107;
        }
        .error {
            color: #dc3545;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        .mtr-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>VPS 网络监控报告</h1>
        <p>会话 ID: {{ session_id }}</p>
        <p>开始时间: {{ start_time }}</p>
        {% if end_time %}
        <p>结束时间: {{ end_time }}</p>
        {% endif %}
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{{ total_tests }}</div>
            <div class="stat-label">测试总数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value success">{{ successful_tests }}</div>
            <div class="stat-label">成功</div>
        </div>
        <div class="stat-card">
            <div class="stat-value error">{{ failed_tests }}</div>
            <div class="stat-label">失败</div>
        </div>
    </div>

    <h2>测试结果详情</h2>
    <table>
        <thead>
            <tr>
                <th>VPS 名称</th>
                <th>提供商</th>
                <th>区域</th>
                <th>IP</th>
                <th>平均延迟 (ms)</th>
                <th>最小延迟 (ms)</th>
                <th>最大延迟 (ms)</th>
                <th>丢包率 (%)</th>
                <th>状态</th>
            </tr>
        </thead>
        <tbody>
            {% for result in results %}
            <tr>
                <td>{{ result.name }}</td>
                <td>{{ result.provider }}</td>
                <td>{{ result.region }}</td>
                <td>{{ result.ip }}</td>
                {% if result.ping.success %}
                <td>{{ "%.2f"|format(result.ping.avg) }}</td>
                <td>{{ "%.2f"|format(result.ping.min) }}</td>
                <td>{{ "%.2f"|format(result.ping.max) }}</td>
                <td>{{ "%.1f"|format(result.ping.packet_loss) }}</td>
                <td><span class="badge badge-success">成功</span></td>
                {% else %}
                <td colspan="4">-</td>
                <td><span class="badge badge-danger">失败</span></td>
                {% endif %}
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if mtr_results %}
    <h2>MTR 路径追踪结果</h2>
    {% for result in mtr_results %}
    <div class="mtr-section">
        <h3>{{ result.name }} - {{ result.mtr.destination }}</h3>
        <p><strong>总跳数:</strong> {{ result.mtr.total_hops }}</p>
        <table>
            <thead>
                <tr>
                    <th>跳数</th>
                    <th>IP</th>
                    <th>平均延迟 (ms)</th>
                    <th>丢包率 (%)</th>
                </tr>
            </thead>
            <tbody>
                {% for hop in result.mtr.hops %}
                <tr>
                    <td>{{ hop.hop }}</td>
                    <td>{{ hop.ip }}</td>
                    <td>{% if hop.avg %}{{ "%.2f"|format(hop.avg) }}{% else %}N/A{% endif %}</td>
                    <td>{{ "%.1f"|format(hop.loss) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endfor %}
    {% endif %}
</body>
</html>
"""

    def generate(self, session: TestSession, output_path: Optional[str] = None) -> str:
        template = Template(self.HTML_TEMPLATE)
        mtr_results = [r for r in session.results if r.mtr and r.mtr.success]

        html_str = template.render(
            session_id=session.session_id,
            start_time=session.start_time,
            end_time=session.end_time,
            total_tests=session.total_tests,
            successful_tests=session.successful_tests,
            failed_tests=session.failed_tests,
            results=session.results,
            mtr_results=mtr_results,
        )

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_str)
            logger.info(f"HTML 报告已保存: {output_file}")
            return str(output_file)

        return html_str


class ReporterFactory:
    _reporters = {
        "json": JSONReporter,
        "markdown": MarkdownReporter,
        "md": MarkdownReporter,
        "html": HTMLReporter,
    }

    @classmethod
    def get_reporter(cls, format_type: str) -> BaseReporter:
        format_type = format_type.lower()
        if format_type not in cls._reporters:
            raise ValueError(f"不支持的格式: {format_type}. 支持的格式: {list(cls._reporters.keys())}")
        return cls._reporters[format_type]()
