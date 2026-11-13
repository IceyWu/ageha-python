"""Check that installed distribution metadata matches the public version."""
from importlib.metadata import version

import ageha


def test_installed_version_matches_module():
    assert version("ageha") == ageha.__version__


def test_greet_uses_default_name():
    assert ageha.greet() == "Hello, World!"


def test_greet_supports_custom_and_unicode_names():
    assert ageha.greet("Lev Wu") == "Hello, Lev Wu!"
    assert ageha.greet("世界") == "Hello, 世界!"
