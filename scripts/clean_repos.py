#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Clean Repos
Copies only source code and docs from cloned repos to data/cleaned/.
Removes: binaries, images, node_modules, caches, build artifacts.
"""

import fnmatch
import shutil
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    REPOS_DIR, CLEANED_DIR, IGNORED_DIRS, IGNORED_FILES,
    CODE_EXTENSIONS
)


def should_ignore_dir(dirname):
    for pattern in IGNORED_DIRS:
        if fnmatch.fnmatch(dirname, pattern):
            return True
    return False


def should_ignore_file(filename):
    for pattern in IGNORED_FILES:
        if fnmatch.fnmatch(filename, pattern):
            return True
    ext = Path(filename).suffix.lower()
    if ext not in CODE_EXTENSIONS and ext != "":
        return True
    return False


def clean_repo(repo_dir, target_dir):
    if target_dir.exists():
        shutil.rmtree(target_dir)

    files_copied = 0
    files_skipped = 0

    for root, dirs, files in repo_dir.walk():
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]

        for filename in files:
            if should_ignore_file(filename):
                files_skipped += 1
                continue

            src = Path(root) / filename
            rel = src.relative_to(repo_dir)
            dst = target_dir / rel

            dst.parent.mkdir(parents=True, exist_ok=True)

            try:
                size = src.stat().st_size
                if size > 1_000_000:
                    files_skipped += 1
                    continue

                shutil.copy2(src, dst)
                files_copied += 1
            except (PermissionError, OSError):
                files_skipped += 1

    return files_copied, files_skipped


def clean_all():
    print(f"Clean Repos — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    repos = [d for d in REPOS_DIR.iterdir() if d.is_dir()]
    print(f"Found {len(repos)} cloned repos\n")

    total_copied = 0
    total_skipped = 0
    cleaned_count = 0

    for i, repo_dir in enumerate(repos):
        target_dir = CLEANED_DIR / repo_dir.name
        if target_dir.exists():
            print(f"[{i+1}/{len(repos)}] SKIP (exists): {repo_dir.name}")
            continue

        print(f"[{i+1}/{len(repos)}] Cleaning: {repo_dir.name}")
        copied, skipped = clean_repo(repo_dir, target_dir)

        total_copied += copied
        total_skipped += skipped
        cleaned_count += 1
        print(f"  +{copied} files, -{skipped} skipped")

    print(f"\n{'='*50}")
    print(f"CLEAN COMPLETE")
    print(f"  Repos cleaned:  {cleaned_count}")
    print(f"  Files copied:   {total_copied}")
    print(f"  Files skipped:  {total_skipped}")


if __name__ == "__main__":
    clean_all()
