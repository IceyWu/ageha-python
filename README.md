# Ageha

A Python SDK by **Lev Wu** for reusable model integrations.

**Bootstrap stage:** this version validates packaging and CI publishing only.
Chat clients, model-provider adapters and audio features are not implemented yet.
The first test release goes to TestPyPI.

## Development

    uv sync --group dev
    uv run ruff check src tests scripts
    uv run pytest -q
    uv build
    uv run twine check dist/*

## Releases

Conventional commits (feat:, fix:, feat!:) maintain an automated release PR.
Merge that PR to create a version tag and GitHub release.
TestPyPI publishing is manually triggered from Actions > test-publish.
Production publishing is disabled until PYPI_ENABLED=true and a PyPI Trusted
Publisher is configured. See [the walkthrough](docs/publishing.md).

## 中文

Ageha 是 **Lev Wu** 维护的 Python SDK，计划支持多个模型供应商。
当前只验证仓库、测试、构建和发布流水线，尚未提供模型调用 API。
先通过 TestPyPI 验证上传、分发包哈希和独立环境安装，再开发真实功能。
