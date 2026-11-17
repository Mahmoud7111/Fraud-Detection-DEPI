"""
Resumable IP geolocation collector using ip-api.com (free, non-commercial).

Rate limits (free tier):
    - Up to 100 IPs per batch request (HTTP POST to /batch).
    - Maximum 15 batch requests per minute.
    - HTTP only on the free tier — not HTTPS.
    - Non-commercial use only.

Resumable design: already-looked-up IPs are skipped on restart; every
completed batch is appended to the output file immediately.

Usage (from scripts/01_collect_ips.py):
    from src.collect.ip_lookup import collect_ips
    collect_ips()
"""
import logging
import time
from pathlib import Path

import pandas as pd
import requests

from src.config import (
    IP_API_BATCH_SIZE,
    IP_API_FIELDS,
    IP_API_MAX_BATCHES_PER_MIN,
    IP_API_URL,
    IP_LOOKUP_CSV,
    UNIQUE_IPS_CSV,
)
from src.common.ips import ip_int_to_str

logger = logging.getLogger(__name__)


def _already_done(output_path: Path) -> set:
    """Return the set of ip_int values already written to the output file."""
    if output_path.exists():
        return set(pd.read_csv(output_path, usecols=["ip_int"])["ip_int"].tolist())
    return set()


def _batch_lookup(ip_ints: list) -> list:
    """POST one batch of IPs to ip-api and return a list of result dicts."""
    payload = [
        {"query": ip_int_to_str(i), "fields": IP_API_FIELDS}
        for i in ip_ints
    ]
    try:
        resp = requests.post(IP_API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        results = resp.json()
    except Exception as exc:
        logger.warning("Batch request failed: %s", exc)
        results = [{"status": "fail", "message": str(exc)} for _ in ip_ints]

    rows = []
    for ip_int, entry in zip(ip_ints, results):
        ok = entry.get("status") == "success"
        rows.append({
            "ip_int":        ip_int,
            "ip_str":        ip_int_to_str(ip_int),
            "lookup_status": "success" if ok else "fail",
            "fail_reason":   "" if ok else entry.get("message", ""),
            "country":       entry.get("country", ""),
            "country_code":  entry.get("countryCode", ""),
            "proxy":         entry.get("proxy", ""),
            "hosting":       entry.get("hosting", ""),
            "queried_at":    pd.Timestamp.utcnow().isoformat(),
        })
    return rows


def collect_ips(
    unique_ips_path: Path = UNIQUE_IPS_CSV,
    output_path: Path = IP_LOOKUP_CSV,
    batch_size: int = IP_API_BATCH_SIZE,
    max_batches_per_min: int = IP_API_MAX_BATCHES_PER_MIN,
) -> None:
    """Collect country data for all unique IPs; resumes if interrupted.

    Parameters
    ----------
    unique_ips_path : Path
        CSV from T2.1 with column ``ip_int``.
    output_path : Path
        Destination for ip_lookup.csv (Contract C2).
    batch_size : int
        IPs per request (max 100 for free tier).
    max_batches_per_min : int
        Rate limit (15 for free tier).
    """
    all_ips = pd.read_csv(unique_ips_path)["ip_int"].tolist()
    done    = _already_done(output_path)
    todo    = [i for i in all_ips if i not in done]
    logger.info(
        "Total IPs: %d | Already done: %d | Remaining: %d",
        len(all_ips), len(done), len(todo),
    )

    min_interval = 60.0 / max_batches_per_min
    first_write  = not output_path.exists()
    total_batches = -(-len(todo) // batch_size)  # ceiling division

    for idx, start in enumerate(range(0, len(todo), batch_size), 1):
        t0    = time.monotonic()
        batch = todo[start: start + batch_size]
        rows  = _batch_lookup(batch)

        df_batch = pd.DataFrame(rows)
        df_batch.to_csv(output_path, mode="w" if first_write else "a",
                        header=first_write, index=False)
        first_write = False

        elapsed = time.monotonic() - t0
        wait    = max(0.0, min_interval - elapsed)
        logger.info("Batch %d/%d (%.1fs). Waiting %.1fs.", idx, total_batches, elapsed, wait)
        time.sleep(wait)

    logger.info("IP collection complete → %s", output_path)
