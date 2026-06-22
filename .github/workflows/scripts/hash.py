#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download_sha256(url: str) -> str:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return sha256_bytes(response.content)


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)

    return h.hexdigest()


def find_package_manifests(root: Path) -> list[Path]:
    manifests = []

    for json_file in root.rglob("*.json"):
        if json_file.name != "repo.json":
            manifests.append(json_file)

    return sorted(manifests)


def find_repo_files(root: Path) -> list[Path]:
    return sorted(root.rglob("repo.json"))


def update_package_manifest(path: Path) -> bool:
    with path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    changed = False

    scripts = manifest.get("scripts", {})
    install_hash = None

    if "install" in scripts:
        install = scripts["install"]

        url = install.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            new_hash = download_sha256(url)

            if install.get("hash") != new_hash:
                install["hash"] = new_hash
                changed = True

            install_hash = new_hash

    for script_name, script in scripts.items():
        if script_name == "install":
            continue

        url = script.get("url", "")
        script_type = script.get("$type")

        if isinstance(url, str) and url.startswith(("http://", "https://")):
            new_hash = download_sha256(url)

            if script.get("hash") != new_hash:
                script["hash"] = new_hash
                changed = True

        elif script_type == "key" and install_hash:
            if script.get("hash") != install_hash:
                script["hash"] = install_hash
                changed = True

    if changed:
        manifest["date"] = utc_timestamp()
        write_json(path, manifest)
        print(f"[UPDATED] {path}")
    else:
        print(f"[UNCHANGED] {path}")

    return changed


def update_repo_file(repo_path: Path) -> bool:
    with repo_path.open("r", encoding="utf-8") as f:
        repo = json.load(f)

    changed = False
    repo_dir = repo_path.parent

    for package in repo.get("packages", []):
        package_file = repo_dir / package["url"]

        new_hash = file_sha256(package_file)

        if package.get("hash") != new_hash:
            package["hash"] = new_hash
            changed = True

    if changed:
        now = datetime.now(timezone.utc)

        repo["date"] = (
            now.isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

        repo["valid_until"] = (
            (now + timedelta(days=3))
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

        write_json(repo_path, repo)
        print(f"[UPDATED] {repo_path}")
    else:
        print(f"[UNCHANGED] {repo_path}")

    return changed


def main() -> int:
    root = Path.cwd()

    print("=== Updating package manifests ===")

    package_manifests = find_package_manifests(root)

    for manifest in package_manifests:
        update_package_manifest(manifest)

    print()
    print("=== Updating repositories ===")

    repo_files = find_repo_files(root)

    for repo_file in repo_files:
        update_repo_file(repo_file)

    print()
    print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
