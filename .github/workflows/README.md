# GitHub Actions Workflows

## docker-build.yml

自动构建和推送 Docker 镜像到 GitHub Container Registry。

### 触发条件

- 推送到 `main` 或 `master` 分支
- 创建版本标签（`v*`）
- Pull Request（仅构建，不推送）
- 手动触发（workflow_dispatch）

### 功能

- 多平台构建（linux/amd64, linux/arm64）
- 使用 Docker Buildx 和缓存加速
- 自动生成标签（latest, branch, sha, semver）
- 推送到 GitHub Container Registry (ghcr.io)

### 使用

1. 推送到 main 分支会自动触发构建
2. 创建标签 `v1.0.0` 会构建并推送带版本标签的镜像
3. 在 Actions 页面可以手动触发构建

## ci.yml

代码质量检查和测试。

### 触发条件

- 推送到 `main` 或 `master` 分支
- Pull Request

### 功能

- 代码检查（Ruff, Black, MyPy）
- 运行测试
- 构建测试 Docker 镜像
