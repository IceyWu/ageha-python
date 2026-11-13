"""Version changes must produce consistent distribution and module metadata."""
import subprocess
import sys
import tomllib
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "set_version.py"


def test_ci_version_updates_both_metadata_sources(tmp_path):
    (tmp_path / "src/ageha").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.0.0"\n')
    module = tmp_path / "src/ageha/__init__.py"
    module.write_text('__version__ = "0.0.0"\n')
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "0.1.0.dev1231"], cwd=tmp_path,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    project = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert project["project"]["version"] == "0.1.0.dev1231"
    assert '__version__ = "0.1.0.dev1231"' in module.read_text()


def test_invalid_ci_version_leaves_files_untouched(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "not-a-version"], cwd=tmp_path,
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert not list(tmp_path.iterdir())
