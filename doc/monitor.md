# Monitor 监控程序使用文档

## 简介

Monitor 是一个批量监控程序，根据配置文件 `config/vps.json` 监控所有配置的 VPS 节点，支持单次测试和持续监控模式。

## 基本用法

```bash
# 单次测试所有配置的 VPS 节点
poetry run python -m src.monitor --once

# 持续监控模式（每 60 秒测试一次）
poetry run python -m src.monitor
```

## 命令行参数

### 可选参数

- `-c, --config`: VPS 配置文件路径（默认: `config/vps.json`）
- `-i, --interval`: 持续监控模式下的测试间隔，单位：秒（默认: 60）
- `-n, --count`: 每次 ping 的次数（默认: 10）
- `-o, --once`: 只执行一次测试（不持续监控）
- `-s, --save`: 保存结果到指定文件
- `--mtr`: 启用 MTR 路径追踪（需要安装 mtr 工具）
- `--format`: 报告格式，可选值：`json`, `html`, `markdown`, `md`（默认: json）
- `--log-level`: 日志级别，可选值：`DEBUG`, `INFO`, `WARNING`, `ERROR`（默认: INFO）

## 使用示例

### 单次测试

```bash
# 执行一次测试并显示结果摘要
poetry run python -m src.monitor --once

# 执行一次测试并保存结果
poetry run python -m src.monitor --once --save results.json

# 执行一次测试，启用 MTR，并保存为 HTML 格式
poetry run python -m src.monitor --once --mtr --save results.html --format html
```

### 持续监控

```bash
# 每 60 秒测试一次（默认）
poetry run python -m src.monitor

# 每 30 秒测试一次
poetry run python -m src.monitor -i 30

# 每 5 分钟测试一次，启用 MTR
poetry run python -m src.monitor -i 300 --mtr
```

### 自定义配置

```bash
# 使用自定义配置文件
poetry run python -m src.monitor --config /path/to/custom_config.json --once

# 增加 ping 次数以提高准确性
poetry run python -m src.monitor --once --count 20
```

### 保存结果

```bash
# 单次测试并保存为 JSON
poetry run python -m src.monitor --once --save results.json

# 单次测试并保存为 HTML
poetry run python -m src.monitor --once --save report.html --format html

# 单次测试并保存为 Markdown
poetry run python -m src.monitor --once --save report.md --format markdown
```

## 配置文件格式

配置文件 `config/vps.json` 格式如下：

```json
{
  "vps_list": [
    {
      "name": "Vultr-日本",
      "provider": "Vultr",
      "region": "日本东京",
      "ip": "hnd-jp-ping.vultr.com"
    },
    {
      "name": "Hetzner-德国",
      "provider": "Hetzner",
      "region": "德国法兰克福",
      "ip": "hetzner.de"
    }
  ]
}
```

## 输出说明

### 控制台输出

程序会在控制台输出：
- 测试进度信息
- 每个 VPS 节点的测试结果
- 测试结果摘要（包括平均延迟、丢包率、状态等）

### 文件输出

如果使用 `--save` 参数，结果会保存到指定文件，格式由 `--format` 参数决定。

## 持续监控模式

在持续监控模式下，程序会：
1. 读取配置文件中的所有 VPS 节点
2. 依次测试每个节点
3. 等待指定的间隔时间（`--interval`）
4. 重复步骤 2-3

按 `Ctrl+C` 可以停止监控。

## 注意事项

1. **配置文件**: 确保 `config/vps.json` 文件存在且格式正确

2. **MTR 工具**: 如果使用 `--mtr` 参数，需要先安装 mtr 工具
   - macOS: `brew install mtr`
   - Linux: `apt-get install mtr` 或 `yum install mtr`

3. **资源消耗**: 持续监控模式会持续占用系统资源，建议根据实际需求设置合适的测试间隔

4. **日志文件**: 可以通过环境变量 `LOG_FILE` 指定日志文件路径

5. **Prometheus Metrics**: 监控程序会自动记录 Prometheus metrics，可以通过 metrics 端点查询
