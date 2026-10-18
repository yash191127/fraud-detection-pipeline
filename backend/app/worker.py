"""Redis consumer + ML inference.

Reads transactions from a Redis Stream, scores them with the Isolation Forest,
saves the result to PostgreSQL and broadcasts it to connected dashboards.
"""
import asyncio
import math
import os
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd
import redis.asyncio as aioredis

from .database import SessionLocal
from .models import Transaction
from .websocket import manager

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM = "transactions"
GROUP = "fraud-workers"
CONSUMER = "worker-1"

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "ml" / "models" / "fraud_model.pkl"


def load_model():
    if not MODEL_PATH.exists():
        print("Model not found - training one now (ml/train.py)...")
        subprocess.run([sys.executable, str(ROOT / "ml" / "train.py")], check=True)
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["numeric"], bundle["categorical"], bundle["threshold"]


def save_transaction(row: dict) -> dict:
    with SessionLocal() as db:
        txn = Transaction(**row)
        db.add(txn)
        db.commit()
        db.refresh(txn)
        return txn.to_dict()


async def run_worker() -> None:
    model, numeric, categorical, threshold = load_model()
    r = aioredis.from_url(REDIS_URL, decode_responses=True)

    try:
        await r.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
    except aioredis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    print("Worker listening on Redis stream:", STREAM)
    while True:
        try:
            resp = await r.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=20, block=2000)
            for _, messages in resp or []:
                for msg_id, data in messages:
                    try:
                        await process(data, model, numeric, categorical, threshold)
                    except Exception as e:  # a bad message must not stop the stream
                        print("Skipping bad message:", repr(e))
                    await r.xack(STREAM, GROUP, msg_id)
        except asyncio.CancelledError:
            break
        except Exception as e:  # brief Redis outage etc.
            print("Worker error:", repr(e))
            await asyncio.sleep(1)
    await r.aclose()


def clean(v):
    return None if isinstance(v, float) and math.isnan(v) else v


async def process(data: dict, model, numeric: list[str], categorical: list[str], threshold: float) -> None:
    row = {c: float(data[c]) for c in numeric}
    row.update({c: data.get(c, "unknown") for c in categorical})
    x = pd.DataFrame([row])
    score = float(model.predict_proba(x)[0, 1])
    is_fraud = score >= threshold

    saved = await asyncio.to_thread(save_transaction, {
        "txn_id": data["txn_id"],
        "source_id": data.get("transaction_id"),
        "amount": row["transaction_amount"],
        "merchant_category": data.get("merchant_category"),
        "merchant_country": data.get("merchant_country"),
        "channel": data.get("transaction_channel"),
        "fraud_probability": score,
        "is_fraud": is_fraud,
        "true_class": data.get("is_fraud") == "1",
        "fraud_type": data.get("fraud_type"),
        "features": {k: clean(v) for k, v in row.items()},
    })
    await manager.broadcast({"type": "transaction", "data": saved})
