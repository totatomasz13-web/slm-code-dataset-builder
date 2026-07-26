#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Run Pipeline
Uruchamia cały pipeline krok po kroku z menu wyboru.
Obsługuje auto-aktualizację z GitHub.
"""

import io
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))
from version import VERSION, REPO, BRANCH


def get_local_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_remote_commit():
    url = f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["sha"]
    except Exception:
        return None


def check_for_updates():
    print(f"  Wersja: {VERSION}")

    local = get_local_commit()
    remote = get_remote_commit()

    if not local or not remote:
        print("  Nie można sprawdzić aktualizacji (brak internetu lub Git)")
        return False

    if local == remote:
        print("  Aktualna wersja — nic do aktualizacji")
        return False

    print(f"  Lokalna:    {local[:12]}")
    print(f"  Zdalna:     {remote[:12]}")
    print(f"  Dostępna aktualizacja!")
    return True


def do_update():
    print("\n  Pobieranie aktualizacji...")
    result = subprocess.run(
        ["git", "pull", "origin", BRANCH],
        capture_output=True, text=True, cwd=str(BASE_DIR)
    )
    if result.returncode == 0:
        print("  Aktualizacja zakończona pomyślnie!")
        print("  Uruchamiam ponownie...\n")
        subprocess.run([sys.executable, str(BASE_DIR / "run_pipeline.py")])
        sys.exit(0)
    else:
        print(f"  BŁĄD aktualizacji: {result.stderr}")
        return False


STEPS = [
    {
        "id": 1,
        "name": "GitHub Crawler",
        "script": "github_crawler.py",
        "desc": "Przeskanuje GitHub i zbierze metadane repozytoriów",
        "depends": [],
    },
    {
        "id": 2,
        "name": "Clone Repos",
        "script": "clone_repos.py",
        "desc": "Sklonuje repozytoria (shallow clone)",
        "depends": [1],
    },
    {
        "id": 3,
        "name": "Clean Repos",
        "script": "clean_repos.py",
        "desc": "Usunie śmieci, zostawi tylko kod",
        "depends": [2],
    },
    {
        "id": 4,
        "name": "Analyze Dataset",
        "script": "analyze_dataset.py",
        "desc": "Przeanalizuje ile mamy plików, języków, LOC",
        "depends": [3],
    },
    {
        "id": 5,
        "name": "Create Dataset",
        "script": "create_dataset.py",
        "desc": "Stworzy dataset JSONL do fine-tuningu",
        "depends": [3],
    },
]


def run_step(step):
    script_path = SCRIPTS_DIR / step["script"]
    if not script_path.exists():
        print(f"  BŁĄD: Nie znaleziono {script_path}")
        return False

    print(f"\n{'='*60}")
    print(f"  KROK {step['id']}: {step['name']}")
    print(f"  {step['desc']}")
    print(f"{'='*60}\n")

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n  OK ({elapsed:.1f}s)")
        return True
    else:
        print(f"\n  BŁĄD (kod: {result.returncode})")
        return False


def show_menu():
    print(f"\n{'='*60}")
    print(f"  SLM Code Dataset Builder v{VERSION}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    for step in STEPS:
        deps = ""
        if step["depends"]:
            deps = f" (wymaga: {', '.join(str(d) for d in step['depends'])})"
        print(f"  [{step['id']}] {step['name']}{deps}")
        print(f"      {step['desc']}\n")

    print(f"  [U]  Sprawdź aktualizacje")
    print(f"  [A]  Uruchom WSZYSTKO po kolei")
    print(f"  [Q]  Wyjście")
    print()


def main():
    check_for_updates()
    show_menu()
    choice = input("  Wybierz numer kroku (1-5), U = aktualizuj, A = wszystko, Q = wyjście: ").strip().upper()

    if choice == "Q":
        print("  Koniec.")
        return

    if choice == "U":
        has_update = check_for_updates()
        if has_update:
            answer = input("  Pobrać aktualizację? (T/N): ").strip().upper()
            if answer == "T":
                do_update()
            else:
                print("  Pominięto aktualizację.")
        show_menu()
        choice = input("  Wybierz numer kroku: ").strip().upper()

    if choice == "A":
        print("\nUruchamiam cały pipeline...")
        for step in STEPS:
            if not run_step(step):
                print(f"\nPipeline przerwany na kroku {step['id']}: {step['name']}")
                print("Popraw błąd i uruchom ponownie.")
                return
        print(f"\n{'='*60}")
        print("  CAŁKOWITY SUKCES!")
        print("  Dataset gotowy w data/datasets/")
        print(f"{'='*60}")
        return

    if choice in [str(s["id"]) for s in STEPS]:
        step = next(s for s in STEPS if s["id"] == int(choice))
        run_step(step)
        return

    print("  Nieprawidłowy wybór.")


if __name__ == "__main__":
    main()
