#!/usr/bin/env python3
"""Download and verify the two authoritative article inputs from swell.

Authentication order is deliberate: the configured SSH alias is tried first.
If it is not usable non-interactively, an already-installed ``sshpass`` may
read the configured password file.  Password contents are never read by this
process, printed, copied, or added to provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPOSITORY / "config" / "data_sources.toml"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def verify(path: Path, spec: dict) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_size = path.stat().st_size
    if actual_size != spec["size_bytes"]:
        raise ValueError(
            f"size mismatch for {path}: {actual_size} != {spec['size_bytes']}"
        )
    actual_hash = sha256_file(path)
    if actual_hash != spec["sha256"]:
        raise ValueError(
            f"SHA-256 mismatch for {path}: {actual_hash} != {spec['sha256']}"
        )


def auth_prefix(config: dict) -> list[str]:
    host = config["swell"]["host"]
    probe = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode == 0:
        return []

    password_file = Path(config["swell"]["password_file"]).expanduser()
    if shutil.which("sshpass") and password_file.is_file():
        return ["sshpass", "-f", str(password_file)]
    raise RuntimeError(
        "the SSH alias 'swell' is not available non-interactively and the "
        "documented sshpass fallback is unavailable"
    )


def download(config: dict, name: str, force: bool) -> Path:
    spec = config["inputs"][name]
    destination = REPOSITORY / spec["local"]
    if destination.exists() and not force:
        verify(destination, spec)
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    if partial.exists():
        partial.unlink()

    host = config["swell"]["host"]
    command = [*auth_prefix(config), "scp", "-q", f"{host}:{spec['remote']}", str(partial)]
    try:
        subprocess.run(command, check=True)
        verify(partial, spec)
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--check", action="store_true", help="verify the local mirror only")
    parser.add_argument("--force", action="store_true", help="redownload verified inputs")
    args = parser.parse_args()

    config = load_config(args.config)
    for name in ("corrected_cache", "tracks"):
        spec = config["inputs"][name]
        path = REPOSITORY / spec["local"]
        if args.check:
            verify(path, spec)
        else:
            path = download(config, name, args.force)
        print(f"verified {name}: {path.relative_to(REPOSITORY)} {spec['sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
