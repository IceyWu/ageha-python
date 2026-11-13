"""Ageha: a Python toolkit."""

__version__ = "0.0.0"  # x-release-please-version

__all__ = ["__version__", "greet"]


def greet(name: str = "World") -> str:
    """Return a greeting for the supplied name."""
    return f"Hello, {name}!"
