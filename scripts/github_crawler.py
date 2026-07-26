#!/usr/bin/env python3
"""
SLM Code Dataset Builder — GitHub Crawler
Scans GitHub for high-quality repositories and saves metadata to repos.json.
Supports: token auth, rate-limit handling, resume from checkpoint.
"""

import json
import time
import sys
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    GITHUB_TOKEN, SEARCH_QUERIES, MAX_REPOS_PER_QUERY,
    MIN_STARS, REPOS_JSON, LOGS_DIR
)

API_BASE = "https://api.github.com"
CHECKPOINT_FILE = LOGS_DIR / "crawler_checkpoint.json"


def get_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def wait_for_rate_limit(resp):
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))

    if remaining <= 1:
        now = time.time()
        wait_sec = max(reset_ts - now + 5, 60)
        print(f"  Rate limit hit. Waiting {wait_sec:.0f}s...")
        time.sleep(wait_sec)
        return True

    if resp.status_code == 403 or resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After")
        wait_sec = int(retry_after) if retry_after else 120
        print(f"  Rate limited ({resp.status_code}). Waiting {wait_sec}s...")
        time.sleep(wait_sec)
        return True

    return False


def search_repos(query, page=1, per_page=30):
    url = f"{API_BASE}/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": per_page,
    }
    resp = requests.get(url, headers=get_headers(), params=params, timeout=30)

    if wait_for_rate_limit(resp):
        return search_repos(query, page, per_page)

    resp.raise_for_status()
    return resp.json()


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_queries": [], "repos_found": []}


def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)


def load_existing_repos():
    if REPOS_JSON.exists():
        with open(REPOS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_repos(repos):
    with open(REPOS_JSON, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)


def crawl():
    checkpoint = load_checkpoint()
    existing_repos = load_existing_repos()
    existing_names = {r["full_name"] for r in existing_repos}

    print(f"GitHub Crawler — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Token: {'SET' if GITHUB_TOKEN else 'NOT SET (60 req/hr limit)'}")
    print(f"Already collected: {len(existing_repos)} repos\n")

    new_count = 0

    for query in SEARCH_QUERIES:
        if query in checkpoint["completed_queries"]:
            print(f"SKIP (done): {query}")
            continue

        print(f"Searching: {query}")
        page = 1
        query_count = 0

        while query_count < MAX_REPOS_PER_QUERY:
            try:
                data = search_repos(query, page=page, per_page=30)
            except requests.RequestException as e:
                print(f"  Error: {e}. Retrying in 30s...")
                time.sleep(30)
                continue

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                stars = item.get("stargazers_count", 0)
                if stars < MIN_STARS:
                    continue
                if item["full_name"] in existing_names:
                    continue

                repo_info = {
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "owner": item["owner"]["login"],
                    "stars": stars,
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language", "unknown"),
                    "description": item.get("description", ""),
                    "clone_url": item.get("clone_url", ""),
                    "size_kb": item.get("size", 0),
                    "topics": item.get("topics", []),
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                    "crawled_at": datetime.now().isoformat(),
                }

                existing_repos.append(repo_info)
                existing_names.add(item["full_name"])
                new_count += 1
                query_count += 1

            save_repos(existing_repos)
            print(f"  Page {page}: +{len(items)} repos (total: {len(existing_repos)})")

            page += 1
            time.sleep(2)

            if query_count >= MAX_REPOS_PER_QUERY:
                break

        checkpoint["completed_queries"].append(query)
        save_checkpoint(checkpoint)
        print(f"  Query done. +{query_count} new repos\n")

    existing_repos.sort(key=lambda r: r["stars"], reverse=True)
    save_repos(existing_repos)

    print(f"\n{'='*50}")
    print(f"CRAWL COMPLETE")
    print(f"  New repos:  {new_count}")
    print(f"  Total repos: {len(existing_repos)}")
    print(f"  Saved to:   {REPOS_JSON}")

    languages = {}
    for r in existing_repos:
        lang = r.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1

    print(f"\nLanguages:")
    for lang, count in sorted(languages.items(), key=lambda x: -x[1])[:15]:
        print(f"  {lang}: {count}")

    return existing_repos


if __name__ == "__main__":
    crawl()
