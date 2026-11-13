<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/ageha-mark-light.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/brand/ageha-mark.svg">
    <img src="assets/brand/ageha-mark.svg" alt="Ageha butterfly mark" width="128" height="128">
  </picture>
  <h1>Ageha</h1>
  <p><strong>一个 Python 工具包。</strong></p>
  <p>Lev Wu 创建并维护。</p>
  <p><a href="#项目介绍">项目介绍</a> · <a href="#本地开发">本地开发</a> · <a href="#开发方向">开发方向</a> · <a href="#项目文档">项目文档</a></p>
  <p><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>
  <p>
    <a href="https://github.com/IceyWu/ageha-python/actions/workflows/ci.yml"><img src="https://github.com/IceyWu/ageha-python/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
    <a href="https://github.com/IceyWu/ageha-python/actions/workflows/preview.yml"><img src="https://github.com/IceyWu/ageha-python/actions/workflows/preview.yml/badge.svg?branch=main" alt="Preview Release"></a>
    <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.11+">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-555555?style=flat-square" alt="MIT license"></a>
  </p>
</div>

---

Ageha 是 **Lev Wu** 维护的 Python 工具包，目前正在开发中。

## 安装使用

~~~bash
pip install ageha
~~~

~~~python
from ageha import greet

print(greet("Lev Wu"))  # Hello, Lev Wu!
~~~

## 本地开发

需要 **Python 3.11+** 和 [uv](https://docs.astral.sh/uv/)。

~~~bash
git clone https://github.com/IceyWu/ageha-python.git
cd ageha-python
uv sync --locked
~~~

~~~bash
uv run ruff check src tests scripts
uv run pytest -q
uv build
~~~

## 项目文档

- [发布指南](docs/publishing.md)
- [版本记录](https://github.com/IceyWu/ageha-python/releases)
- [问题反馈](https://github.com/IceyWu/ageha-python/issues)

## 许可证

[MIT](LICENSE) · **Lev Wu**
