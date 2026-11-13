# Ageha

**A Python SDK for unified model integrations.**
Created and maintained by **Lev Wu**.

Ageha is being developed as an independent foundation for connecting applications
to multiple model providers. This initial infrastructure release establishes
package distribution, quality checks and automated version management.
Model-provider APIs will be introduced in subsequent releases.

## Development

    uv sync --group dev
    uv run ruff check src tests scripts
    uv run pytest -q
    uv build
    uv run twine check dist/*

## Release workflow

- **CI** checks Python 3.11, 3.13 and 3.14 on Linux, plus Python 3.13 on Windows.
- **Preview Release** builds a unique development version, publishes to TestPyPI,
  verifies distribution hashes and installs the published wheel in isolation.
- **Release** maintains a version PR and changelog using Conventional Commits.
  Merging that PR creates the version tag and GitHub release. Production PyPI
  uploads require PYPI_ENABLED=true and a configured Trusted Publisher.

See the [Release Guide](docs/publishing.md) for account setup, publishing and recovery.

## 中文

Ageha 是 **Lev Wu** 维护的独立 Python SDK，计划提供统一的多模型接入能力。
当前基础设施版本已建立代码校验、包构建、预发布和自动版本管理流程。
模型供应商适配及聊天 API 将在后续版本加入。
使用 feat:、fix: 等提交前缀后，Release 流水线自动维护版本 PR。
Preview Release 用于验证实际分发与安装；正式发布通过 Release 流水线执行。
