import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Transaction
from .websocket import manager
from .worker import run_worker


def init_db(retries: int = 15) -> None:
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            print(f"Waiting for PostgreSQL... ({attempt + 1}/{retries})")
            time.sleep(2)
    raise RuntimeError("Could not connect to PostgreSQL. Is `docker compose up -d` running?")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(init_db)
    task = asyncio.create_task(run_worker())
    yield
    task.cancel()


app = FastAPI(title="Fraud Detection Pipeline", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/transactions")
def list_transactions(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Transaction).order_by(Transaction.id.desc()).limit(limit).all()
    return [r.to_dict() for r in reversed(rows)]


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    T = Transaction
    total, fraud, volume, flagged_volume, actual, caught = db.query(
        func.count(T.id),
        func.count(T.id).filter(T.is_fraud.is_(True)),
        func.coalesce(func.sum(T.amount), 0),
        func.coalesce(func.sum(T.amount).filter(T.is_fraud.is_(True)), 0),
        func.count(T.id).filter(T.true_class.is_(True)),
        func.count(T.id).filter(and_(T.is_fraud.is_(True), T.true_class.is_(True))),
    ).one()
    return {
        "total": total,
        "fraud": fraud,
        "fraud_rate": round(fraud / total * 100, 2) if total else 0,
        "volume": round(float(volume), 2),
        "flagged_volume": round(float(flagged_volume), 2),
        "actual_fraud": actual,
        "caught": caught,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep the connection open
    except WebSocketDisconnect:
        manager.disconnect(ws)
