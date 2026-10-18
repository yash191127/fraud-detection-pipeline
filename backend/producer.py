"""Replays real transactions from the CSV into a Redis Stream, like a live feed.

Usage:  python producer.py [--rate 2] [--fraud-ratio 0.08]
--fraud-ratio = how often a known-fraud row is picked, so the demo shows some.
"""
import argparse
import math
import os
import random
import sys
import time
import uuid
from pathlib import Path

import pandas as pd
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM = "transactions"
DATA_DIR = Path(__file__).resolve().parents[1] / "ml" / "data"
# Prefer rows the model never trained on, so the live demo is an honest test.
DATA_PATH = DATA_DIR / "holdout.csv" if (DATA_DIR / "holdout.csv").exists() else DATA_DIR / "creditcard.csv"


def to_str(v) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "nan"
    return str(v)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rate", type=float, default=2.0, help="transactions per second")
    p.add_argument("--fraud-ratio", type=float, default=0.08)
    args = p.parse_args()

    if not DATA_PATH.exists():
        sys.exit(f"Dataset not found at {DATA_PATH}. Run python ml/train.py first.")

    print(f"Loading {DATA_PATH.name}...")
    df = pd.read_csv(DATA_PATH)
    normal = df[df["is_fraud"] == 0].to_dict("records")
    fraud = df[df["is_fraud"] == 1].to_dict("records")
    print(f"{len(normal):,} genuine and {len(fraud):,} fraudulent transactions loaded.")

    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print(f"Streaming ~{args.rate}/s. Ctrl+C to stop.")

    sent = 0
    try:
        while True:
            pool = fraud if (fraud and random.random() < args.fraud_ratio) else normal
            row = random.choice(pool)
            msg = {k: to_str(v) for k, v in row.items()}
            msg["txn_id"] = str(uuid.uuid4())   # unique even if a row is replayed
            r.xadd(STREAM, msg, maxlen=10_000, approximate=True)
            sent += 1
            if sent % 20 == 0:
                print(f"sent {sent} transactions")
            time.sleep(random.expovariate(args.rate))
    except KeyboardInterrupt:
        print(f"\nStopped after {sent} transactions.")


if __name__ == "__main__":
    main()
