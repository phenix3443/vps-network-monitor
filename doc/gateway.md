# Gateway API 服务器使用文档

## 简介

Gateway 是一个 Flask RESTful API 服务器，提供 HTTP 接口用于查询测试结果、执行测试，并托管前端界面。

## 启动服务

### 基本启动

```bash
# 使用默认配置启动（监听 0.0.0.0:5000）
poetry run python -m src.gateway

# 或使用 Makefile
make start
```

### 自定义配置

```bash
# 指定主机和端口
poetry run python -m src.gateway --host 127.0.0.1 --port 8080

# 使用自定义配置文件
poetry run python -m src.gateway --config /path/to/config.json

# 启用调试模式
poetry run python -m src.gateway --debug
```

## 命令行参数

- `--host`: 绑定的主机地址（默认: `0.0.0.0`）
- `--port`: 绑定的端口（默认: `5000`）
- `--config`: 配置文件路径（默认: `config/vps.json`）
- `--debug`: 启用调试模式

## API 端点

### 前端界面

- `GET /`: 返回前端 HTML 界面（交互式地图）

### 服务状态

- `GET /api/status`: 获取服务状态
  ```json
  {
    "status": "running",
    "timestamp": "2026-01-11T23:00:00",
    "vps_count": 10
  }
  ```

### VPS 列表

- `GET /api/vps/list`: 获取所有配置的 VPS 节点列表
  ```json
  {
    "vps_list": [
      {
        "name": "Vultr-日本",
        "provider": "Vultr",
        "region": "日本东京",
        "ip": "hnd-jp-ping.vultr.com",
        "location": {
          "lat": 35.6762,
          "lng": 139.6503
        }
      }
    ]
  }
  ```

### 测试结果

- `GET /api/results`: 获取完整的测试结果（TestSession 格式）
- `GET /api/results/latest`: 获取最新测试结果（简化版，用于地图展示）
  ```json
  {
    "results": [
      {
        "name": "Vultr-日本",
        "provider": "Vultr",
        "region": "日本东京",
        "ip": "hnd-jp-ping.vultr.com",
        "ping": {
          "success": true,
          "avg": 89.45,
          "packet_loss": 0.0
        },
        "mtr": null
      }
    ]
  }
  ```

### 执行测试

- `POST /api/test/domain`: 测试指定的域名或 IP
  ```json
  // 请求体
  {
    "domain": "example.com",
    "name": "测试节点",
    "provider": "Vultr",
    "region": "日本东京",
    "ping_count": 10,
    "use_mtr": false
  }
  
  // 响应
  {
    "success": true,
    "result": {
      "timestamp": "2026-01-11T23:00:00",
      "name": "测试节点",
      "provider": "Vultr",
      "region": "日本东京",
      "ip": "example.com",
      "ping": {
        "success": true,
        "avg": 89.45,
        "packet_loss": 0.0
      },
      "mtr": null
    }
  }
  ```

### 健康检查

- `GET /api/health`: 健康检查端点（用于 Kubernetes liveness/readiness probe）

## 使用示例

### 使用 curl 查询

```bash
# 获取服务状态
curl http://localhost:5000/api/status

# 获取 VPS 列表
curl http://localhost:5000/api/vps/list

# 获取最新测试结果
curl http://localhost:5000/api/results/latest

# 测试指定域名
curl -X POST http://localhost:5000/api/test/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "8.8.8.8",
    "name": "Google DNS",
    "provider": "Google",
    "region": "美国",
    "ping_count": 10,
    "use_mtr": false
  }'
```

### 使用 Python requests

```python
import requests

# 获取 VPS 列表
response = requests.get("http://localhost:5000/api/vps/list")
vps_list = response.json()["vps_list"]

# 测试域名
response = requests.post(
    "http://localhost:5000/api/test/domain",
    json={
        "domain": "example.com",
        "ping_count": 10,
        "use_mtr": False
    }
)
result = response.json()
```

## 前端界面

访问 `http://localhost:5000` 可以打开交互式地图界面，显示：
- 所有配置的 VPS 节点位置
- 实时连接状态
- Ping 延迟和丢包率
- MTR 路径追踪结果（如果可用）

## 部署

### Docker

```bash
# 构建镜像
docker build -t vps-network-monitor .

# 运行容器
docker run -d \
  -p 5000:5000 \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  vps-network-monitor
```

### Kubernetes

```bash
# 应用部署配置
kubectl apply -f k8s-deployment.yaml

# 检查服务状态
kubectl get pods -l app=vps-network-monitor
```

## 环境变量

- `LOG_LEVEL`: 日志级别（默认: `INFO`）
- `METRICS_PORT`: Metrics 服务端口（默认: `8000`）
- `LOG_FILE`: 日志文件路径（可选）

## 注意事项

1. **CORS**: API 服务器已启用 CORS，支持跨域请求

2. **配置文件**: 确保 `config/vps.json` 文件存在，否则服务可能无法正常工作

3. **前端静态文件**: 前端文件位于 `src/frontend/index.html`，由 Flask 自动提供

4. **Prometheus Metrics**: Metrics 服务在端口 8000 上运行，可以通过 `http://localhost:8000/metrics` 访问

5. **生产环境**: 在生产环境中，建议使用 Gunicorn 或 uWSGI 等 WSGI 服务器，而不是直接运行 Flask 开发服务器
