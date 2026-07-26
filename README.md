# SLM Code Dataset Builder

Pipeline do tworzenia własnego zbioru danych (datasetu) do trenowania modeli LLM specjalizujących się w programowaniu.

## Cel

Stworzenie asystenta programistycznego AI, który potrafi:
- pisać kod w wielu językach
- analizować i naprawiać błędy
- tworzyć funkcje i moduły
- tłumaczyć kod między językami
- pomagać w tworzeniu aplikacji

## Pipeline

```
GitHub API -> Klonowanie -> Czyszczenie -> Analiza -> Dataset JSONL -> Fine-tuning LoRA
```

## Struktura

```
SLM_DATA/
├── scripts/
│   ├── config.py           # Centralna konfiguracja
│   ├── version.py          # Wersja projektu
│   ├── github_crawler.py   # Skanowanie GitHub
│   ├── clone_repos.py      # Klonowanie repo
│   ├── clean_repos.py      # Czyszczenie danych
│   ├── analyze_dataset.py  # Analiza datasetu
│   └── create_dataset.py   # Tworzenie JSONL
├── run_pipeline.py         # Główny plik uruchamiający
├── setup.py                # Instalacja globalna
├── install.bat             # Szybka instalacja (Windows)
├── data/
│   ├── repos.json
│   ├── repositories/
│   ├── cleaned/
│   └── datasets/
├── models/checkpoints/
└── logs/
```

## Szybki start

### 1. Instalacja globalna (zalecane)

```bash
# Z folderu projektu
pip install -e .

# Lub na Windows kliknij
install.bat
```

Po instalacji komenda dostępna z dowolnego miejsca:

```bash
slm-pipeline
```

### 2. Token GitHub (opcjonalnie, ale zalecane)

Bez tokena limit to 60 zapytań/godzinę. Z tokenem: 5000/godzinę.

```bash
set GITHUB_TOKEN=ghp_twoj_token_tutaj
```

Utwórz token na: https://github.com/settings/tokens
Potrzebne uprawnienia: `public_repo` (read-only)

### 3. Uruchamianie

```bash
# Globalna komenda (po instalacji)
slm-pipeline

# Lub bezpośrednio
python run_pipeline.py
```

Menu wygląda tak:

```
  [1] GitHub Crawler       — skanuje GitHub
  [2] Clone Repos          — klonuje repo
  [3] Clean Repos          — czyści dane
  [4] Analyze Dataset      — analiza
  [5] Create Dataset       — tworzy JSONL

  [U]  Sprawdź aktualizacje
  [A]  Uruchom WSZYSTKO po kolei
  [Q]  Wyjście
```

Wybierz `A` aby uruchomić cały pipeline, lub numer kroku aby uruchomić pojedynczo.

### 4. Auto-aktualizacja

Przy każdym uruchomieniu program sprawdza GitHub czy jest nowsza wersja.
Jak jest dostępna aktualizacja — zapyta czy pobrać.

## Wymagania

- Python 3.10+
- Git
- Dysk: min. 100 GB wolnego miejsca
- Token GitHub (zalecane)

## Odinstalowanie

```bash
pip uninstall slm-code-dataset-builder
```

## Licencja

MIT
