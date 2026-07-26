#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Clone Repos
Równoległe klonowanie repo z GitHub (shallow clone).
Obsługuje wznawianie, limit rozmiaru, timeout.
"""

import json
import subprocess
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import REPOS_JSON, REPOS_DIR, LOGS_DIR, GITHUB_TOKEN, MAX_CLONE_SIZE_MB

CLONE_LOG = LOGS_DIR / "clone_log.json"
MAX_WORKERS = 8
CLONE_TIMEOUT = 120


def load_clone_log():
    if CLONE_LOG.exists():
        with open(CLONE_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "failed": [], "skipped": []}


def save_clone_log(log):
    with open(CLONE_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False)


def repo_dir_name(full_name):
    return full_name.replace("/", "_").replace("\\", "_")


def clone_repo(repo):
    full_name = repo["full_name"]
    target = REPOS_DIR / repo_dir_name(full_name)

    if target.exists():
        return full_name, True, "exists"

    size_kb = repo.get("size_kb", 0)
    if size_kb > MAX_CLONE_SIZE_MB * 1024:
        return full_name, False, "too_large"

    clone_url = repo.get("clone_url", "")
    if GITHUB_TOKEN:
        clone_url = clone_url.replace("https://", f"https://x-access-token:{GITHUB_TOKEN}@")

    cmd = ["git", "clone", "--depth", "1", "--single-branch", "--filter=blob:none", clone_url, str(target)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CLONE_TIMEOUT)
        if result.returncode != 0:
            return full_name, False, f"git_error: {result.stderr[:80]}"
        return full_name, True, "cloned"
    except subprocess.TimeoutExpired:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        return full_name, False, "timeout"
    except Exception as e:
        return full_name, False, str(e)[:80]


def clone_all():
    if not REPOS_JSON.exists():
        print("ERROR: repos.json not found. Run github_crawler.py first.")
        return

    with open(REPOS_JSON, "r", encoding="utf-8") as f:
        repos = json.load(f)

    log = load_clone_log()
    to_skip = set(log["completed"] + log["failed"] + log["skipped"])

    pending = [r for r in repos if r["full_name"] not in to_skip]

    print(f"Clone Repos — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total: {len(repos)} | Done: {len(to_skip)} | Pending: {len(pending)}")
    print(f"Workers: {MAX_WORKERS} | Timeout: {CLONE_TIMEOUT}s\n")

    cloned = 0
    failed = 0
    skipped = 0
    total = len(pending)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(clone_repo, repo): repo for repo in pending}

        for i, future in enumerate(as_completed(futures), 1):
            name, ok, reason = future.result()

            if ok:
                if reason == "exists":
                    pass
                else:
                    cloned += 1
                log["completed"].append(name)
                status = "OK" if reason == "cloned" else "EXISTS"
            else:
                if reason == "too_large":
                    skipped += 1
                    log["skipped"].append(name)
                    status = "SKIP"
                else:
                    failed += 1
                    log["failed"].append(name)
                    status = "FAIL"

            print(f"  [{i}/{total}] {status}: {name} ({reason})")

            if i % 20 == 0:
                save_clone_log(log)
                print(f"  --- checkpoint: {cloned} cloned, {failed} failed, {skipped} skipped ---")

    save_clone_log(log)

    print(f"\n{'='*50}")
    print(f"CLONE COMPLETE")
    print(f"  Cloned:  {cloned}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")


if __name__ == "__main__":
    clone_all()
