"""Verify registry SHA-256 hashes, download and install the published wheel."""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

index, directory = sys.argv[1:3]
wheel = next(Path(directory).glob("*.whl"))
with zipfile.ZipFile(wheel) as archive:
    metadata = archive.read(next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA")))
version = next(line.split(": ", 1)[1] for line in metadata.decode().splitlines()
               if line.startswith("Version: "))
host = {"testpypi": "test.pypi.org", "pypi": "pypi.org"}[index]
url = f"https://{host}/pypi/ageha/{version}/json"
for attempt in range(8):
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.load(response)
        files = {row["filename"]: row for row in data["urls"]}
        for artifact in Path(directory).iterdir():
            assert files[artifact.name]["digests"]["sha256"] == hashlib.sha256(
                artifact.read_bytes()
            ).hexdigest(), f"Hash mismatch: {artifact.name}"
        published = files[wheel.name]
        with urllib.request.urlopen(published["url"], timeout=30) as response:
            downloaded = response.read()
        assert hashlib.sha256(downloaded).hexdigest() == published["digests"]["sha256"]
        wheel.write_bytes(downloaded)
        break
    except Exception:
        if attempt == 7:
            raise
        time.sleep(10)
subprocess.run(["uv", "venv", "smoke-env"], check=True)
python = Path("smoke-env/bin/python").resolve()
subprocess.run(["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)], check=True)
subprocess.run([str(python), "-I", "-c",
                ("import ageha; from importlib.metadata import version; "
                 "assert ageha.__version__ == version('ageha'); print(version('ageha'))")], check=True)
print(f"Verified registry hashes and installed ageha=={version} from {host}")
