"""Check that installed distribution metadata matches the public version."""
from importlib.metadata import version

import ageha


def test_installed_version_matches_module():
    assert version("ageha") == ageha.__version__
