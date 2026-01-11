.PHONY: help install dev backend frontend start stop clean test build docker-build docker-run

# 默认配置
PYTHON := python3
POETRY := poetry
API_PORT := 5000
API_HOST := 0.0.0.0
CONFIG_FILE := vps.json

help: ## 显示帮助信息
	@echo "VPS 网络监控 - Makefile 命令"
	@echo ""
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	$(POETRY) install --no-root

dev: ## 开发模式启动（自动重载）
	$(POETRY) run $(PYTHON) -m src.gateway --host $(API_HOST) --port $(API_PORT) --debug

backend: ## 启动后端 API 服务器
	@echo "启动后端 API 服务器..."
	$(POETRY) run $(PYTHON) -m src.gateway --host $(API_HOST) --port $(API_PORT)

start: backend ## 启动服务（默认启动后端，前端由后端服务）

frontend: ## 仅启动前端（需要先启动后端）
	@echo "前端由后端服务器提供服务，访问: http://localhost:$(API_PORT)"
	@echo "请先运行 'make backend' 或 'make start'"

run: start ## 启动服务（别名）

stop: ## 停止服务（查找并杀死进程）
	@echo "查找并停止 API 服务器..."
	@pkill -f "src.gateway" || echo "未找到运行中的服务"

restart: stop start ## 重启服务

test: ## 运行测试
	$(POETRY) run pytest

test-once: ## 执行一次测试（CLI模式）
	$(POETRY) run $(PYTHON) -m src.cli --once

test-continuous: ## 持续监控模式
	$(POETRY) run $(PYTHON) -m src.cli -i 60

clean: ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	@echo "清理完成"

build: ## 构建项目
	$(POETRY) build

docker-build: ## 构建 Docker 镜像
	docker build -t vps-network-monitor:latest .

docker-run: ## 运行 Docker 容器
	docker run -d \
		--name vps-monitor \
		-p $(API_PORT):5000 \
		-p 8000:8000 \
		-v $$(pwd)/$(CONFIG_FILE):/app/$(CONFIG_FILE) \
		vps-network-monitor:latest

docker-stop: ## 停止 Docker 容器
	docker stop vps-monitor || true
	docker rm vps-monitor || true

docker-logs: ## 查看 Docker 容器日志
	docker logs -f vps-monitor

format: ## 格式化代码
	$(POETRY) run black src/
	$(POETRY) run ruff check --fix src/

lint: ## 代码检查
	$(POETRY) run ruff check src/
	$(POETRY) run mypy src/

check: lint ## 代码检查（别名）

discover-nodes: ## 自动发现测试节点
	$(POETRY) run $(PYTHON) -m src.cli --discover-nodes

verify-nodes: ## 验证现有节点
	$(POETRY) run $(PYTHON) -m src.cli --verify-nodes

update-config: ## 更新配置（DNS解析）
	$(POETRY) run $(PYTHON) -m src.cli --resolve-dns --update-config

logs: ## 查看日志（如果启用了日志文件）
	@if [ -f "vps_monitor.log" ]; then \
		tail -f vps_monitor.log; \
	else \
		echo "日志文件不存在"; \
	fi

status: ## 检查服务状态
	@echo "检查服务状态..."
	@if pgrep -f "src.gateway" > /dev/null; then \
		echo "✓ 后端服务正在运行"; \
		curl -s http://localhost:$(API_PORT)/api/status | python3 -m json.tool || echo "✗ API 无法访问"; \
	else \
		echo "✗ 后端服务未运行"; \
	fi
