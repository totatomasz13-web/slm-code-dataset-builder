#!/usr/bin/env python3
"""
SLM Code Dataset Builder — Settings
Zarządzanie ustawieniami projektu (token, limity, itp.)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BASE_DIR

SETTINGS_FILE = BASE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "github_token": "",
    "max_stars": 500,
    "max_clone_size_mb": 5000,
    "clone_workers": 16,
    "clone_timeout": 120,
    "auto_update": True,
}


def load_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            settings = DEFAULT_SETTINGS.copy()
            settings.update(saved)
            return settings
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_github_token():
    settings = load_settings()
    return settings.get("github_token") or os.environ.get("GITHUB_TOKEN", "")


def show_settings():
    settings = load_settings()
    token = settings.get("github_token", "")

    print(f"\n{'='*60}")
    print(f"  USTAWIENIA")
    print(f"{'='*60}\n")

    print(f"  [1] Token GitHub:     {'***' + token[-6:] if len(token) > 6 else 'NIE USTAWIONY'}")
    print(f"  [2] Min. gwiazdki:    {settings['max_stars']}")
    print(f"  [3] Max rozmiar repo:  {settings['max_clone_size_mb']} MB")
    print(f"  [4] Workerów:         {settings['clone_workers']}")
    print(f"  [5] Timeout clone:    {settings['clone_timeout']}s")
    print(f"  [6] Auto-aktualizacja: {'TAK' if settings['auto_update'] else 'NIE'}")
    print()
    print(f"  [T]  Jak utworzyć token GitHub")
    print(f"  [Z]  Zapisz zmiany")
    print(f"  [W]  Wróć")
    print()


def setup_token_wizard():
    print(f"\n{'='*60}")
    print(f"  TOKEN GITHUB — KROK PO KROKU")
    print(f"{'='*60}\n")

    print("  1. Wejdź na:")
    print("     https://github.com/settings/tokens\n")
    print("  2. Kliknij 'Generate new token (classic)'\n")
    print("  3. Nazwa: np. 'SLM Dataset Builder'\n")
    print("  4. Zaznacz:")
    print("     [x] public_repo   (odczyt publicznych repo)\n")
    print("  5. Kliknij 'Generate token'\n")
    print("  6. SKOPIUJ token (ghp_xxxxx)\n")
    print("  7. Wklej poniżej:\n")

    token = input("  Token: ").strip()

    if not token:
        print("  Anulowano.")
        return None

    if not token.startswith("ghp_"):
        print("  Token powinien zaczynać się od 'ghp_'. Spróbuj ponownie.")
        return None

    settings = load_settings()
    settings["github_token"] = token
    save_settings(settings)

    print(f"\n  Token zapisany! ({token[:7]}...{token[-4:]})")
    print(f"  Limit: 5000 zapytań/godzinę (zamiast 60)")
    return token


def edit_settings():
    settings = load_settings()

    while True:
        show_settings()
        choice = input("  Wybierz (1-6/T/Z/W): ").strip().upper()

        if choice == "W":
            return

        if choice == "T":
            setup_token_wizard()
            continue

        if choice == "Z":
            save_settings(settings)
            print("  Zapisano!")
            continue

        if choice == "1":
            token = setup_token_wizard()
            if token:
                settings["github_token"] = token
        elif choice == "2":
            val = input(f"  Min. gwiazdki [{settings['max_stars']}]: ").strip()
            if val.isdigit():
                settings["max_stars"] = int(val)
        elif choice == "3":
            val = input(f"  Max rozmiar MB [{settings['max_clone_size_mb']}]: ").strip()
            if val.isdigit():
                settings["max_clone_size_mb"] = int(val)
        elif choice == "4":
            val = input(f"  Workerów [{settings['clone_workers']}]: ").strip()
            if val.isdigit() and int(val) >= 1:
                settings["clone_workers"] = int(val)
        elif choice == "5":
            val = input(f"  Timeout sekundy [{settings['clone_timeout']}]: ").strip()
            if val.isdigit():
                settings["clone_timeout"] = int(val)
        elif choice == "6":
            settings["auto_update"] = not settings["auto_update"]
        else:
            print("  Nieprawidłowy wybór.")


if __name__ == "__main__":
    show_settings()
    input("\n  Naciśnij Enter aby wrócić...")
