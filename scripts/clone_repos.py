#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Clone Repos
Rownolegle klonowanie repo z GitHub (shallow clone).
Obsluguje wznawianie, limit rozmiaru, timeout.
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
from config import REPOS_JSON, REPOS_DIR, LOGS_DIR

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "settings.json"
CLONE_LOG = LOGS_DIR / "clone_log.json"


def load_settings():
    defaults = {"github_token": "", "max_clone_size_mb": 500, "clone_workers": 8, "clone_timeout": 120}
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            defaults.update(saved)
    return defaults


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


def clone_repo(repo, settings):
    full_name = repo["full_name"]
    target = REPOS_DIR / repo_dir_name(full_name)

    if target.exists():
        return full_name, True, "exists"

    size_kb = repo.get("size_kb", 0)
    if size_kb > settings["max_clone_size_mb"] * 1024:
        return full_name, False, "too_large"

    clone_url = repo.get("clone_url", "")
    token = settings.get("github_token", "")
    if token:
        clone_url = clone_url.replace("https://", f"https://x-access-token:{token}@")

    cmd = ["git", "clone", "--depth", "1", "--single-branch", "--filter=blob:none", clone_url, str(target)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=settings["clone_timeout"])
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

    settings = load_settings()

    with open(REPOS_JSON, "r", encoding="utf-8") as f:
        repos = json.load(f)

    log = load_clone_log()
    to_skip = set(log["completed"] + log["failed"] + log["skipped"])

    pending = [r for r in repos if r["full_name"] not in to_skip]

    print(f"Clone Repos — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total: {len(repos)} | Done: {len(to_skip)} | Pending: {len(pending)}")
    print(f"Workers: {settings['clone_workers']} | Timeout: {settings['clone_timeout']}s\n")

    cloned = 0
    failed = 0
    skipped = 0
    total = len(pending)

    with ThreadPoolExecutor(max_workers=settings["clone_workers"]) as executor:
        futures = {executor.submit(clone_repo, repo, settings): repo for repo in pending}

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
