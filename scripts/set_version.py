"""Set an ephemeral CI test version without changing the release manifest."""
import re
import sys
from pathlib import Path

version = sys.argv[1]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.dev[0-9]+)?", version):
    raise SystemExit("Expected x.y.z or x.y.z.devN")
for filename, pattern, replacement in [
    ("pyproject.toml", r'(?m)^version = "[^"]+"$', f'version = "{version}"'),
    ("src/ageha/__init__.py", r'__version__ = "[^"]+"', f'__version__ = "{version}"'),
]:
    path = Path(filename)
    path.write_text(re.sub(pattern, replacement, path.read_text()), encoding="utf-8")
