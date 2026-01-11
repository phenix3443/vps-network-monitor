# VPS 访问情况监控工具

这是一个用于**从本地网络实时检测不同 VPS 厂商访问情况**的 Python 监控程序。

## 功能特点

- ✅ **前后端分离**：RESTful API 后端 + 交互式前端地图
- ✅ **实时地图可视化**：在世界地图上展示 VPS 位置和连接情况
- ✅ **本地测试**：从你的本地电脑测试访问各个 VPS 的网络性能
- ✅ 实时检测多个 VPS 的延迟、丢包率等网络指标
- ✅ 支持持续监控模式，定期自动测试
- ✅ 结果保存为 JSON、HTML、Markdown 格式，便于分析
- ✅ 支持自定义测试间隔和 ping 次数
- ✅ 跨平台支持（Linux、macOS、Windows）
- ✅ 使用 Poetry 管理依赖，项目结构规范
- ✅ Prometheus metrics 支持，便于监控

## 环境要求

- Python 3.12+（推荐使用最新版本）
- Poetry（用于依赖管理）
- MTR 工具（可选，用于路径追踪）
  - macOS: `brew install mtr`
  - Linux: `apt-get install mtr` 或 `yum install mtr`

## 快速开始

### 安装依赖

```bash
# 安装 Poetry（如果还没有）
curl -sSL https://install.python-poetry.org | python3 -

# 克隆项目
git clone <repository-url>
cd vps-network-monitor

# 安装依赖
poetry install
```

### 配置 VPS 列表

编辑 `config/vps.json` 文件，填入要测试的 VPS IP 地址或域名。

### 使用方式

项目提供三种使用方式：

#### 1. CLI 工具（测试单个域名或批量测试）

```bash
# 测试单个域名
poetry run python -m src.cli example.com

# 从配置文件测试所有节点
poetry run python -m src.cli --config

# 查看详细文档
# doc/cli.md
```

#### 2. Monitor 监控程序（批量监控）

```bash
# 单次测试所有配置的 VPS 节点
poetry run python -m src.monitor --once

# 持续监控模式（每 60 秒测试一次）
poetry run python -m src.monitor

# 查看详细文档
# doc/monitor.md
```

#### 3. Gateway API 服务器（Web 界面）

```bash
# 启动 API 服务器（包含前端）
poetry run python -m src.gateway

# 打开浏览器访问 http://localhost:5000

# 查看详细文档
# doc/gateway.md
```

### 使用 Makefile（推荐）

```bash
# 安装依赖
make install

# 启动服务（后端 + 前端）
make start

# 执行一次测试
make test-once

# 查看所有可用命令
make help
```

## 项目结构

```text
vps-network-monitor/
├── src/                  # 源代码目录
│   ├── tester/          # 测试器模块
│   ├── cli/             # 命令行接口
│   ├── monitor/         # 监控程序
│   ├── gateway/         # API 网关
│   ├── log/             # 日志模块
│   ├── metric/          # 指标模块
│   ├── utils/           # 工具模块
│   ├── reports/         # 报告生成模块
│   └── frontend/        # 前端代码
├── config/              # 配置文件目录
│   └── vps.json         # VPS 节点配置文件
├── doc/                 # 文档目录
│   ├── cli.md          # CLI 工具使用文档
│   ├── monitor.md      # Monitor 监控程序文档
│   └── gateway.md      # Gateway API 服务器文档
├── .github/             # GitHub Actions workflows
├── Dockerfile           # Docker 构建文件
├── k8s-deployment.yaml  # Kubernetes 部署配置
├── Makefile             # 构建和运行命令
└── pyproject.toml       # 项目配置
```

## 详细文档

- **[CLI 工具文档](doc/cli.md)** - 测试单个域名的命令行工具使用说明
- **[Monitor 监控程序文档](doc/monitor.md)** - 批量监控所有 VPS 节点的使用说明
- **[Gateway API 服务器文档](doc/gateway.md)** - Web API 和前端界面的使用说明

## CI/CD

项目使用 GitHub Actions 自动构建 Docker 镜像。

### 自动构建

- **推送到 main/master 分支**：自动构建并推送到 GitHub Container Registry
- **创建标签（v*）**：自动构建并推送带版本标签的镜像
- **Pull Request**：仅构建镜像，不推送

### 使用构建的镜像

```bash
# 从 GitHub Container Registry 拉取
docker pull ghcr.io/YOUR_USERNAME/vps-network-monitor:latest

# 运行容器
docker run -d \
  --name vps-monitor \
  -p 5000:5000 \
  -p 8000:8000 \
  ghcr.io/YOUR_USERNAME/vps-network-monitor:latest
```

## 生产环境部署（Kubernetes）

本项目已优化为生产级别，支持部署到 Kubernetes 集群，并提供 Prometheus metrics 和健康检查。

### 部署到 Kubernetes

```bash
# 应用部署配置
kubectl apply -f k8s-deployment.yaml

# 检查部署状态
kubectl get pods -l app=vps-network-monitor
```

### Prometheus Metrics

服务在 `http://localhost:8000/metrics` 暴露 Prometheus metrics，包括：

- `vps_ping_total` - Ping 测试总数（按状态分类）
- `vps_ping_latency_ms` - Ping 延迟（直方图）
- `vps_ping_packet_loss_percent` - 丢包率（Gauge）
- `vps_mtr_hops_total` - MTR 路径跳数
- `vps_mtr_hop_latency_ms` - MTR 每跳延迟
- `vps_test_duration_seconds` - 测试耗时
- `vps_errors_total` - 错误计数
- `vps_config_reload_total` - 配置重载次数

### 环境变量

- `LOG_LEVEL` - 日志级别（DEBUG, INFO, WARNING, ERROR），默认：INFO
- `METRICS_PORT` - Metrics 服务端口，默认：8000
- `LOG_FILE` - 日志文件路径（可选）

## 开发

### 开发环境设置

```bash
# 安装开发依赖
poetry install --with dev

# 运行代码格式化
poetry run black src/

# 运行代码检查
poetry run ruff check src/

# 运行类型检查
poetry run mypy src/
```

### 项目结构说明

项目采用模块化设计，每个模块职责单一：

- **tester/** - 测试器模块：提供 ping 和 MTR 测试功能
- **cli/** - 命令行接口：测试单个域名并输出报告
- **monitor/** - 监控程序：批量监控所有配置的 VPS 节点
- **gateway/** - API 网关：提供 RESTful API 和前端界面
- **log/** - 日志模块：统一的日志配置和管理
- **metric/** - 指标模块：Prometheus metrics 收集
- **utils/** - 工具模块：地理位置等通用工具
- **reports/** - 报告生成：多格式报告生成和可视化

## 注意事项

1. **网络环境**：不同时间段（白天/晚上）的网络表现可能不同，建议多时段测试
2. **防火墙**：某些 VPS 可能禁 ping，如果测试失败，可能是防火墙设置
3. **DNS 解析**：使用域名测试时，确保本地 DNS 解析正常
4. **配置文件**：确保 `config/vps.json` 文件存在且格式正确

## 许可证

[根据项目实际情况添加许可证信息]
