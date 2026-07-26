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
SETTINGS_FILE = BASE_DIR / "settings.json"

sys.path.insert(0, str(SCRIPTS_DIR))
from version import VERSION, REPO, BRANCH


# ── Settings ──────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "github_token": "",
    "max_stars": 500,
    "max_clone_size_mb": 500,
    "clone_workers": 8,
    "clone_timeout": 120,
    "auto_update": True,
}


def load_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            s = DEFAULT_SETTINGS.copy()
            s.update(saved)
            return s
    return DEFAULT_SETTINGS.copy()


def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)


def get_token():
    s = load_settings()
    import os
    return s.get("github_token") or os.environ.get("GITHUB_TOKEN", "")


# ── Token wizard ──────────────────────────────────────────

def setup_token():
    print(f"\n{'='*60}")
    print(f"  TOKEN GITHUB — INSTRUKCJA")
    print(f"{'='*60}\n")

    print("  1. Wejdź na:")
    print("     https://github.com/settings/tokens\n")
    print("  2. Kliknij 'Generate new token (classic)'\n")
    print("  3. Nazwa: np. 'SLM Dataset Builder'\n")
    print("  4. Zaznacz:")
    print("     [x] public_repo   (odczyt publicznych repo)\n")
    print("  5. Kliknij 'Generate token'\n")
    print("  6. SKOPIUJ token (ghp_xxxxx)\n")

    token = input("  Wklej token tutaj: ").strip()

    if not token:
        print("  Anulowano.")
        return

    if not token.startswith("ghp_"):
        print("  Token powinien zaczynać się od 'ghp_'. Spróbuj ponownie.")
        return

    s = load_settings()
    s["github_token"] = token
    save_settings(s)

    print(f"\n  Token zapisany! ({token[:7]}...{token[-4:]})")
    print(f"  Limit: 5000 zapytań/godzinę (zamiast 60)")
    input("\n  Naciśnij Enter aby kontynuować...")


# ── Settings menu ─────────────────────────────────────────

def show_settings():
    s = load_settings()
    token = s.get("github_token", "")

    while True:
        print(f"\n{'='*60}")
        print(f"  USTAWIENIA")
        print(f"{'='*60}\n")

        token_display = f"***{token[-6:]}" if len(token) > 6 else "BRAK"
        print(f"  [1] Token GitHub:      {token_display}")
        print(f"  [2] Min. gwiazdki:     {s['max_stars']}")
        print(f"  [3] Max rozmiar repo:   {s['max_clone_size_mb']} MB")
        print(f"  [4] Workerów:          {s['clone_workers']}")
        print(f"  [5] Timeout clone:     {s['clone_timeout']}s")
        print(f"  [6] Auto-aktualizacja: {'TAK' if s['auto_update'] else 'NIE'}")
        print()
        print(f"  [T]  Jak utworzyć token (link + instrukcja)")
        print(f"  [Z]  Zapisz i wróć")
        print(f"  [W]  Wróć bez zapisywania")
        print()

        choice = input("  Wybierz: ").strip().upper()

        if choice == "W":
            return

        if choice == "Z":
            save_settings(s)
            print("  Zapisano!")
            return

        if choice == "T":
            setup_token()
            s = load_settings()
            continue

        if choice == "1":
            setup_token()
            s = load_settings()
        elif choice == "2":
            val = input(f"  Min. gwiazdki [{s['max_stars']}]: ").strip()
            if val.isdigit():
                s["max_stars"] = int(val)
        elif choice == "3":
            val = input(f"  Max rozmiar MB [{s['max_clone_size_mb']}]: ").strip()
            if val.isdigit():
                s["max_clone_size_mb"] = int(val)
        elif choice == "4":
            val = input(f"  Workerów [{s['clone_workers']}]: ").strip()
            if val.isdigit() and int(val) >= 1:
                s["clone_workers"] = int(val)
        elif choice == "5":
            val = input(f"  Timeout sekundy [{s['clone_timeout']}]: ").strip()
            if val.isdigit():
                s["clone_timeout"] = int(val)
        elif choice == "6":
            s["auto_update"] = not s["auto_update"]
        else:
            print("  Nieprawidłowy wybór.")


# ── Auto-update ───────────────────────────────────────────

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
    s = load_settings()
    if not s.get("auto_update", True):
        return False

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


# ── Progress stats ────────────────────────────────────────

def show_progress():
    repos_json = BASE_DIR / "data" / "repos.json"
    repos_dir = BASE_DIR / "data" / "repositories"
    cleaned_dir = BASE_DIR / "data" / "cleaned"
    datasets_dir = BASE_DIR / "data" / "datasets"

    total_repos = 0
    if repos_json.exists():
        with open(repos_json, "r", encoding="utf-8") as f:
            total_repos = len(json.load(f))

    cloned = len([d for d in repos_dir.iterdir() if d.is_dir()]) if repos_dir.exists() else 0
    cleaned = len([d for d in cleaned_dir.iterdir() if d.is_dir()]) if cleaned_dir.exists() else 0

    has_dataset = (datasets_dir / "train.jsonl").exists()

    print(f"\n{'='*60}")
    print(f"  POSTĘP")
    print(f"{'='*60}\n")

    def bar(done, total, width=30):
        if total == 0:
            return f"[{'.'*width}] 0/0"
        filled = int(width * done / total)
        return f"[{'█'*filled}{'.'*(width-filled)}] {done}/{total}"

    print(f"  Repo w bazie:      {bar(total_repos, total_repos)}")
    print(f"  Sklonowane:        {bar(cloned, total_repos)}")
    print(f"  Wyczyszczone:      {bar(cleaned, total_repos)}")
    print(f"  Dataset:           {'GOTOWY' if has_dataset else 'BRAK'}")

    if total_repos > 0 and cloned < total_repos:
        remaining = total_repos - cloned
        print(f"\n  Zostało: {remaining} repo do sklonowania")


# ── Pipeline steps ────────────────────────────────────────

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
        "desc": "Sklonuje repozytoria (rownoledge, 8 workerow)",
        "depends": [1],
    },
    {
        "id": 3,
        "name": "Clean Repos",
        "script": "clean_repos.py",
        "desc": "Usunie smieci, zostawi tylko kod",
        "depends": [2],
    },
    {
        "id": 4,
        "name": "Analyze Dataset",
        "script": "analyze_dataset.py",
        "desc": "Przeanalizuje ile mamy plikow, jezykow, LOC",
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
        print(f"  BLAD: Nie znaleziono {script_path}")
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
        print(f"\n  BLAD (kod: {result.returncode})")
        return False


# ── Main menu ─────────────────────────────────────────────

def show_menu():
    s = load_settings()
    token = s.get("github_token", "")
    token_ok = "TAK" if token else "NIE"

    print(f"\n{'='*60}")
    print(f"  SLM Code Dataset Builder v{VERSION}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Token: {token_ok} | Workery: {s['clone_workers']}")
    print(f"{'='*60}\n")

    for step in STEPS:
        deps = ""
        if step["depends"]:
            deps = f" (wymaga: {', '.join(str(d) for d in step['depends'])})"
        print(f"  [{step['id']}] {step['name']}{deps}")
        print(f"      {step['desc']}\n")

    print(f"  [S]  Ustawienia (token, workerow, itp.)")
    print(f"  [P]  Postep pipeline")
    print(f"  [U]  Sprawdz aktualizacje")
    print(f"  [A]  Uruchom WSZYSTKO po kolei")
    print(f"  [Q]  Wyjscie")
    print()


def main():
    if not load_settings().get("github_token"):
        print(f"\n{'='*60}")
        print(f"  BRAK TOKENA GITHUB")
        print(f"{'='*60}")
        print(f"  Token jest wymagany do pobierania repozytoriow.")
        print(f"  Bez niego limit to 60 zapytan/godzine.")
        print()
        print(f"  Utworz token tutaj:")
        print(f"  https://github.com/settings/tokens")
        print()
        answer = input("  Czy chcesz ustawić token teraz? (T/N): ").strip().upper()
        if answer == "T":
            setup_token()
        else:
            print("  Mozesz to zrobic pozniej w ustawieniach (S).")

    check_for_updates()

    while True:
        show_menu()
        choice = input("  Wybierz: ").strip().upper()

        if choice == "Q":
            print("  Koniec.")
            return

        if choice == "S":
            show_settings()
            continue

        if choice == "P":
            show_progress()
            input("\n  Naciśnij Enter aby wrócić...")
            continue

        if choice == "U":
            has_update = check_for_updates()
            if has_update:
                answer = input("  Pobrać aktualizację? (T/N): ").strip().upper()
                if answer == "T":
                    do_update()
                else:
                    print("  Pominięto aktualizację.")
            continue

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
            continue

        print("  Nieprawidłowy wybór.")


if __name__ == "__main__":
    main()
