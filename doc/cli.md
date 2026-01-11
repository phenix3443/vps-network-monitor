# CLI 工具使用文档

## 简介

CLI 工具用于测试单个 VPS 域名或 IP 地址的网络连接情况，也支持从配置文件批量测试所有节点。支持 ping 测试和 MTR 路径追踪。

**批量测试时**：会自动生成 Markdown 格式的报告，所有节点结果汇总在一个数据表中。

## 基本用法

### 测试单个域名

```bash
# 测试单个域名
poetry run python -m src.cli example.com

# 测试 IP 地址
poetry run python -m src.cli 8.8.8.8
```

### 从配置文件测试所有节点

```bash
# 使用默认配置文件测试所有节点
poetry run python -m src.cli --config

# 使用自定义配置文件
poetry run python -m src.cli --config /path/to/custom.json
```

## 命令行参数

### 参数说明

- `domain`: 要测试的 VPS 域名或 IP 地址（可选，如果使用 `--config` 则忽略）

### 可选参数

- `-n, --name`: VPS 节点名称（默认使用域名）
- `-p, --provider`: VPS 提供商（默认: Unknown）
- `-r, --region`: VPS 地区（默认: Unknown）
- `-c, --count`: Ping 测试次数（默认: 10）
- `--mtr`: 启用 MTR 路径追踪（需要安装 mtr 工具）
- `-o, --output`: 输出文件路径（可选）
- `-f, --format`: 输出格式，可选值：`text`, `json`, `html`, `markdown`, `md`（默认: text）
- `--config`: 从配置文件测试所有节点（默认: `config/vps.json`）。如果提供此参数，将忽略 `domain` 参数
- `--log-level`: 日志级别，可选值：`DEBUG`, `INFO`, `WARNING`, `ERROR`（默认: INFO）

## 使用示例

### 基本测试

```bash
# 测试单个域名
poetry run python -m src.cli example.com

# 测试并指定名称和提供商
poetry run python -m src.cli example.com \
  --name "测试节点" \
  --provider "Vultr" \
  --region "日本东京"
```

### 启用 MTR 路径追踪

```bash
# 测试域名并启用 MTR
poetry run python -m src.cli example.com --mtr

# 指定 ping 次数并启用 MTR
poetry run python -m src.cli example.com --count 20 --mtr
```

### 保存测试结果

```bash
# 保存为 JSON 格式
poetry run python -m src.cli example.com \
  --output result.json \
  --format json

# 保存为 HTML 格式
poetry run python -m src.cli example.com \
  --output result.html \
  --format html

# 保存为 Markdown 格式
poetry run python -m src.cli example.com \
  --output result.md \
  --format markdown
```

### 从配置文件测试所有节点

```bash
# 测试配置文件中的所有节点（自动生成 Markdown 报告）
poetry run python -m src.cli --config

# 测试所有节点并启用 MTR
poetry run python -m src.cli --config --mtr

# 测试所有节点并指定输出文件名
poetry run python -m src.cli --config --output results.md

# 测试所有节点并保存为 JSON 报告
poetry run python -m src.cli --config --output results.json --format json

# 测试所有节点并指定 ping 次数
poetry run python -m src.cli --config --count 20

# 使用自定义配置文件
poetry run python -m src.cli --config /path/to/custom.json
```

**注意**：使用 `--config` 参数时，如果不指定 `--output` 和 `--format`，会自动生成一个带时间戳的 Markdown 文件（如 `test_results_20260111_234837.md`），所有节点结果汇总在一个数据表中。

### 自定义日志级别

```bash
# 启用调试日志
poetry run python -m src.cli example.com --log-level DEBUG

# 只显示错误日志
poetry run python -m src.cli example.com --log-level ERROR
```

## 输出格式

### Text 格式（默认）

输出到控制台的文本格式，包含：
- 测试结果摘要
- Ping 测试详情（平均延迟、最小/最大延迟、丢包率等）
- MTR 路径追踪详情（如果启用）

**批量测试时**：会依次显示每个节点的测试结果，最后显示测试完成统计。

### JSON 格式

结构化的 JSON 数据，包含完整的测试结果，便于程序处理。

**批量测试时**：包含所有节点的测试结果，格式为 `TestSession`。

### HTML 格式

美观的 HTML 报告，包含图表和详细数据。

**批量测试时**：包含所有节点的测试结果和汇总信息。

### Markdown 格式

Markdown 格式的报告，便于在文档中使用。

**批量测试时**：包含所有节点的测试结果汇总表格，包括：
- 所有节点（成功和失败）统一在一个表格中
- 按延迟排序（成功的在前，失败的在后）
- 包含状态、延迟、丢包率、错误信息等完整信息
- 如果启用了 MTR，还会包含 MTR 路径追踪的详细结果

**表格列**：VPS 名称 | 提供商 | 区域 | IP | 状态 | 平均延迟 | 最小延迟 | 最大延迟 | 丢包率 | 错误信息

## 返回值

- 退出码 `0`: 测试成功
- 退出码 `1`: 测试失败

## 注意事项

1. **MTR 工具**: 如果使用 `--mtr` 参数，需要先安装 mtr 工具
   - macOS: `brew install mtr`
   - Linux: `apt-get install mtr` 或 `yum install mtr`

2. **网络权限**: 某些系统可能需要管理员权限才能执行 ping 和 MTR 测试

3. **超时设置**: 默认情况下，ping 测试会根据 `--count` 参数自动计算超时时间
