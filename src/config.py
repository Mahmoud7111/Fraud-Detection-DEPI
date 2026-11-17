"""
Central configuration — paths, random seed, and thresholds.

Rule 8: No hard-coded absolute paths anywhere else in the project.
        Import from here instead.
"""
import pathlib

# ── Repo root (src/config.py → src/ → root) ───────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent.resolve()

# ── Data directories ──────────────────────────────────────────────────────────
DATA_RAW       = ROOT / "data" / "raw"
DATA_INTERIM   = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"

# ── Raw files (never edited) ──────────────────────────────────────────────────
RAW_TRANSACTIONS   = DATA_RAW / "Fraud_Data.csv"
IP_COUNTRY_FILE    = DATA_RAW / "IpAddress_to_Country.csv"   # static file from Kaggle download

# ── Interim files ─────────────────────────────────────────────────────────────
UNIQUE_IPS_CSV     = DATA_INTERIM / "unique_ips.csv"
IP_LOOKUP_CSV      = DATA_INTERIM / "ip_lookup.csv"
CPI_CSV            = DATA_INTERIM / "cpi.csv"
CPI_RAW_HTML       = DATA_INTERIM / "cpi_raw.html"
COUNTRY_MAP_CSV    = DATA_INTERIM / "country_name_map.csv"
TRANSACTIONS_CLEAN = DATA_INTERIM / "transactions_clean.csv"

# ── Processed files ───────────────────────────────────────────────────────────
TRANSACTIONS_MERGED = DATA_PROCESSED / "transactions_merged.csv"
FEATURES_CSV        = DATA_PROCESSED / "features.csv"

# ── Model artefacts ───────────────────────────────────────────────────────────
MODELS_DIR       = ROOT / "models"
MODEL_PIPELINE   = MODELS_DIR / "fraud_pipeline.joblib"
INPUT_SPEC_JSON  = MODELS_DIR / "input_spec.json"
THRESHOLD_JSON   = MODELS_DIR / "threshold.json"

# ── Docs and scripts ──────────────────────────────────────────────────────────
DOCS_DIR    = ROOT / "docs"
SCRIPTS_DIR = ROOT / "scripts"

# ── Tests ─────────────────────────────────────────────────────────────────────
FIXTURES_DIR        = ROOT / "tests" / "fixtures"
SAMPLE_TRANSACTIONS = FIXTURES_DIR / "sample_transactions.csv"

# ── Reproducibility ───────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ── ip-api.com settings (free, non-commercial tier) ───────────────────────────
IP_API_BATCH_SIZE          = 100   # max IPs per request
IP_API_MAX_BATCHES_PER_MIN = 15    # free-tier rate limit
IP_API_URL                 = "http://ip-api.com/batch"
IP_API_FIELDS              = "status,message,country,countryCode,proxy,hosting,query"

# ── Decision threshold ────────────────────────────────────────────────────────
# Placeholder only; the real value is chosen on validation data and written to
# models/threshold.json by the training script.
DEFAULT_THRESHOLD = 0.5
