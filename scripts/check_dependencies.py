#!/usr/bin/env python3
"""Read-only verification of sibling checkouts; Python 3.9+, no network."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


REPOSITORY = Path(__file__).resolve().parents[1]


def read_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"dependencies"}:
        raise ValueError("manifest schema")
    entries = data["dependencies"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("dependencies must be a nonempty list")
    names = set()
    for item in entries:
        if not isinstance(item, dict) or set(item) != {
            "name", "url", "revision", "files", "purpose"
        }:
            raise ValueError("dependency schema")
        name = item["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
            raise ValueError("invalid checkout name")
        if name in names:
            raise ValueError("duplicate checkout name")
        names.add(name)
        if not isinstance(item["revision"], str) or not re.fullmatch(r"[0-9a-f]{40}", item["revision"]):
            raise ValueError("revision must be an exact 40-character SHA")
        for key in ("url", "purpose"):
            if not isinstance(item[key], str) or not item[key].strip() or any(
                ord(c) < 32 for c in item[key]
            ):
                raise ValueError("invalid dependency metadata")
        files = item["files"]
        if not isinstance(files, list) or not files or len(set(map(str, files))) != len(files):
            raise ValueError("files must be a nonempty unique list")
        for file in files:
            if not isinstance(file, str) or not file or "\\" in file or any(ord(c) < 32 for c in file):
                raise ValueError("invalid relative file")
            relative = PurePosixPath(file)
            if relative.is_absolute() or any(p in ("", ".", "..") for p in file.split("/")):
                raise ValueError("files must stay inside checkout")
    return entries


def git(checkout, *args):
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(checkout), *args],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
    ).stdout


def check_dependency(root, item):
    checkout = root / item["name"]
    if not checkout.is_dir():
        return "missing checkout"
    try:
        top = Path(git(checkout, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        if top != checkout.resolve():
            return "invalid checkout"
        head = git(checkout, "rev-parse", "HEAD").decode().strip()
        problems = []
        if head != item["revision"]:
            problems.append("stale revision")
        for file in item["files"]:
            target = checkout / file
            if not target.is_file() or checkout.resolve() not in target.resolve().parents:
                problems.append("missing/invalid required file")
                break
        if git(checkout, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"):
            problems.append("dirty checkout")
        return ", ".join(problems) if problems else "ok"
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return "unreadable checkout"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY.parent,
                        help="directory containing the named sibling checkouts (default: repository parent)")
    args = parser.parse_args(argv)
    try:
        entries = read_manifest(REPOSITORY / "dependencies.json")
    except (OSError, ValueError, TypeError):
        print("dependencies.json: invalid manifest", file=sys.stderr)
        return 2
    failed = False
    for item in entries:
        status = check_dependency(args.root, item)
        print("{}: {}".format(args.root / item["name"], status))
        failed |= status != "ok"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
