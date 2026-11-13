<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/ageha-mark-light.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/brand/ageha-mark.svg">
    <img src="assets/brand/ageha-mark.svg" alt="Ageha butterfly mark" width="128" height="128">
  </picture>
  <h1>Ageha</h1>
  <p><strong>A Python toolkit.</strong></p>
  <p>Created and maintained by Lev Wu.</p>
  <p><a href="#development">Development</a> · <a href="#documentation">Documentation</a></p>
  <p><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>
  <p>
    <a href="https://github.com/IceyWu/ageha-python/actions/workflows/ci.yml"><img src="https://github.com/IceyWu/ageha-python/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
    <a href="https://github.com/IceyWu/ageha-python/actions/workflows/preview.yml"><img src="https://github.com/IceyWu/ageha-python/actions/workflows/preview.yml/badge.svg?branch=main" alt="Preview Release"></a>
    <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.11+">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-555555?style=flat-square" alt="MIT license"></a>
  </p>
</div>

---

Ageha is a Python toolkit by **Lev Wu**, currently under development.

## Development

Requires **Python 3.11+** and [uv](https://docs.astral.sh/uv/).

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

## Documentation

- [Release guide](docs/publishing.md)
- [Releases](https://github.com/IceyWu/ageha-python/releases)
- [Issues](https://github.com/IceyWu/ageha-python/issues)

## License

[MIT](LICENSE) · **Lev Wu**
