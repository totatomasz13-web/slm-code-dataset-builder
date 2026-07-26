#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Analyze Dataset
Scans cleaned repos and reports: file counts, languages, LOC, size.
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CLEANED_DIR, DATASETS_DIR, CODE_EXTENSIONS

EXTENSION_TO_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "React/JSX", ".tsx": "React/TSX",
    ".java": "Java", ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
    ".hpp": "C++ Header", ".cs": "C#", ".go": "Go", ".rs": "Rust",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    ".scala": "Scala", ".r": "R", ".dart": "Dart", ".lua": "Lua",
    ".sh": "Shell", ".bash": "Shell",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
    ".sql": "SQL", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".json": "JSON", ".xml": "XML", ".md": "Markdown", ".rst": "reST",
    ".vue": "Vue", ".svelte": "Svelte",
    ".dockerfile": "Dockerfile", ".makefile": "Makefile",
}


def analyze():
    print(f"Analyze Dataset — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    languages = defaultdict(lambda: {"files": 0, "lines": 0, "size": 0})
    total_files = 0
    total_lines = 0
    total_size = 0
    repo_count = 0

    repos = [d for d in CLEANED_DIR.iterdir() if d.is_dir()]
    print(f"Scanning {len(repos)} cleaned repos...\n")

    for repo_dir in repos:
        repo_count += 1
        for filepath in repo_dir.rglob("*"):
            if not filepath.is_file():
                continue

            ext = filepath.suffix.lower()
            lang = EXTENSION_TO_LANG.get(ext, "Other")

            try:
                size = filepath.stat().st_size
                if size > 5_000_000:
                    continue

                lines = 0
                if ext in CODE_EXTENSIONS or ext in {".md", ".rst", ".txt"}:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = sum(1 for _ in f)

                languages[lang]["files"] += 1
                languages[lang]["lines"] += lines
                languages[lang]["size"] += size
                total_files += 1
                total_lines += lines
                total_size += size

            except (PermissionError, OSError):
                continue

    print(f"{'='*60}")
    print(f"DATASET ANALYSIS")
    print(f"{'='*60}")
    print(f"Repos scanned:    {repo_count}")
    print(f"Total files:      {total_files:,}")
    print(f"Total lines:      {total_lines:,}")
    print(f"Total size:       {total_size / (1024*1024):.1f} MB")
    print()

    print(f"{'Language':<20} {'Files':>10} {'Lines':>12} {'Size (MB)':>12}")
    print(f"{'-'*56}")

    for lang, stats in sorted(languages.items(), key=lambda x: -x[1]["lines"]):
        size_mb = stats["size"] / (1024 * 1024)
        print(f"{lang:<20} {stats['files']:>10,} {stats['lines']:>12,} {size_mb:>12.1f}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "repos_scanned": repo_count,
        "total_files": total_files,
        "total_lines": total_lines,
        "total_size_mb": round(total_size / (1024 * 1024), 1),
        "languages": {
            lang: stats for lang, stats in
            sorted(languages.items(), key=lambda x: -x[1]["lines"])
        },
    }

    import json
    report_file = DATASETS_DIR / "analysis_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    analyze()
