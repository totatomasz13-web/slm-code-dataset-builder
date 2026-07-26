#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Create Dataset
Converts cleaned source code files into JSONL training format for LLM fine-tuning.
Supports both instruction and conversation formats.
"""

import json
import random
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    CLEANED_DIR, DATASETS_DIR, CODE_EXTENSIONS,
    TRAIN_SPLIT, VALIDATION_SPLIT, TEST_SPLIT,
    MIN_LINES_PER_FILE, MAX_LINES_PER_FILE, MAX_TOKENS_PER_SAMPLE,
)

INSTRUCTION_TEMPLATES = [
    "Explain what this code does:",
    "Write documentation for this code:",
    "Describe the logic of this code:",
    "What is the purpose of this code?",
    "Analyze this code and explain its functionality:",
]

CODE_TASK_TEMPLATES = [
    "Write a {lang} function based on this code:",
    "Rewrite this code in {lang}:",
    "Refactor this code for better readability:",
    "Write unit tests for this code:",
    "Fix any bugs in this code:",
]


def read_code_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        line_count = len(lines)
        if line_count < MIN_LINES_PER_FILE or line_count > MAX_LINES_PER_FILE:
            return None

        content = "".join(lines)
        if len(content) > MAX_TOKENS_PER_SAMPLE * 4:
            return None

        return content.strip()

    except (PermissionError, OSError):
        return None


def estimate_lang(filepath):
    ext = filepath.suffix.lower()
    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".java": "Java", ".c": "C", ".cpp": "C++", ".h": "C",
        ".cs": "C#", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
        ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
        ".html": "HTML", ".css": "CSS", ".sql": "SQL",
        ".sh": "Shell", ".dart": "Dart", ".lua": "Lua",
        ".scala": "Scala", ".r": "R",
    }
    return lang_map.get(ext, "code")


def extract_repo_name(filepath, cleaned_dir):
    parts = filepath.relative_to(cleaned_dir).parts
    return parts[0] if parts else "unknown"


def make_instruction_sample(code, filepath, cleaned_dir):
    repo = extract_repo_name(filepath, cleaned_dir)
    lang = estimate_lang(filepath)
    template = random.choice(INSTRUCTION_TEMPLATES)

    return {
        "messages": [
            {
                "role": "system",
                "content": f"You are a helpful programming assistant. The user will show you code from a {lang} project called '{repo}'."
            },
            {
                "role": "user",
                "content": f"{template}\n\n```{lang.lower()}\n{code}\n```"
            },
            {
                "role": "assistant",
                "content": f"This is a {lang} code file from the '{repo}' project.\n\n```{lang.lower()}\n{code}\n```"
            },
        ],
        "metadata": {
            "repo": repo,
            "language": lang,
            "type": "instruction",
        }
    }


def make_completion_sample(code, filepath, cleaned_dir):
    repo = extract_repo_name(filepath, cleaned_dir)
    lang = estimate_lang(filepath)

    code_lines = code.split("\n")
    split_point = max(1, len(code_lines) // 3)
    prefix = "\n".join(code_lines[:split_point])
    completion = "\n".join(code_lines[split_point:])

    return {
        "messages": [
            {
                "role": "system",
                "content": f"You are an expert {lang} programmer."
            },
            {
                "role": "user",
                "content": f"Complete this {lang} code:\n\n```{lang.lower()}\n{prefix}\n"
            },
            {
                "role": "assistant",
                "content": f"{completion}\n```"
            },
        ],
        "metadata": {
            "repo": repo,
            "language": lang,
            "type": "completion",
        }
    }


def create_dataset():
    print(f"Create Dataset — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    all_samples = []
    repos = [d for d in CLEANED_DIR.iterdir() if d.is_dir()]

    print(f"Scanning {len(repos)} cleaned repos...\n")

    for repo_dir in repos:
        for filepath in repo_dir.rglob("*"):
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() not in CODE_EXTENSIONS:
                continue

            code = read_code_file(filepath)
            if not code:
                continue

            sample_type = random.choice(["instruction", "completion"])
            if sample_type == "instruction":
                sample = make_instruction_sample(code, filepath, CLEANED_DIR)
            else:
                sample = make_completion_sample(code, filepath, CLEANED_DIR)

            all_samples.append(sample)

    print(f"Generated {len(all_samples)} samples\n")

    if not all_samples:
        print("ERROR: No samples generated. Check cleaned data.")
        return

    random.shuffle(all_samples)

    n = len(all_samples)
    train_end = int(n * TRAIN_SPLIT)
    val_end = int(n * (TRAIN_SPLIT + VALIDATION_SPLIT))

    splits = {
        "train.jsonl": all_samples[:train_end],
        "validation.jsonl": all_samples[train_end:val_end],
        "test.jsonl": all_samples[val_end:],
    }

    for filename, data in splits.items():
        filepath = DATASETS_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            for sample in data:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        print(f"  {filename}: {len(data)} samples")

    stats = {
        "timestamp": datetime.now().isoformat(),
        "total_samples": len(all_samples),
        "splits": {k: len(v) for k, v in splits.items()},
        "sample_type_distribution": {
            "instruction": sum(1 for s in all_samples if s["metadata"]["type"] == "instruction"),
            "completion": sum(1 for s in all_samples if s["metadata"]["type"] == "completion"),
        },
    }

    stats_file = DATASETS_DIR / "dataset_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"\nDataset created at: {DATASETS_DIR}")
    print(f"Stats saved to: {stats_file}")


if __name__ == "__main__":
    create_dataset()
