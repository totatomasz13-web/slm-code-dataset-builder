import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"
REPOS_DIR = DATA_DIR / "repositories"
CLEANED_DIR = DATA_DIR / "cleaned"
DATASETS_DIR = DATA_DIR / "datasets"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
REPOS_JSON = DATA_DIR / "repos.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

SEARCH_QUERIES = [
    "language:python stars:>500",
    "language:javascript stars:>500",
    "language:typescript stars:>500",
    "language:java stars:>500",
    "language:cpp stars:>500",
    "language:c stars:>500",
    "language:go stars:>500",
    "language:rust stars:>500",
    "language:ruby stars:>500",
    "language:php stars:>500",
]

MAX_REPOS_PER_QUERY = 100
MIN_STARS = 100
MAX_CLONE_SIZE_MB = 5000

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "build", "dist", ".tox", ".eggs", "*.egg-info", "target",
    ".idea", ".vscode", ".gradle", "vendor", ".bundle",
    "coverage", ".nyc_output", ".mypy_cache", ".pytest_cache",
    "bower_components", "tmp", "temp",
}

IGNORED_FILES = {
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.svg", "*.bmp", "*.webp",
    "*.exe", "*.dll", "*.so", "*.dylib", "*.o", "*.a", "*.lib",
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z", "*.bz2",
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.pptx",
    "*.mp3", "*.mp4", "*.avi", "*.mov", "*.wav",
    "*.woff", "*.woff2", "*.ttf", "*.eot",
    "*.pyc", "*.pyo", "*.class", "*.jar",
    "*.lock", "*.min.js", "*.min.css",
    "*.map", "*.wasm",
}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".kts",
    ".scala", ".r", ".m", ".mm", ".dart", ".lua", ".pl", ".sh", ".bash",
    ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    ".html", ".css", ".scss", ".less", ".sass",
    ".sql", ".graphql", ".gql",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".json", ".xml",
    ".md", ".rst", ".txt",
    ".dockerfile", ".makefile", ".cmake",
    ".vue", ".svelte",
}

TRAIN_SPLIT = 0.8
VALIDATION_SPLIT = 0.1
TEST_SPLIT = 0.1

MAX_TOKENS_PER_SAMPLE = 2048
MIN_LINES_PER_FILE = 5
MAX_LINES_PER_FILE = 500

for d in [DATA_DIR, REPOS_DIR, CLEANED_DIR, DATASETS_DIR, LOGS_DIR, MODELS_DIR / "checkpoints"]:
    d.mkdir(parents=True, exist_ok=True)
