# Fraud Detection Pipeline

Producer → Redis Stream → Worker (Isolation Forest) → PostgreSQL → WebSocket → React dashboard

## Requirements (MacBook Air)
- Docker Desktop (open it and wait until it says "running")
- Python 3.10+  (`python3 --version`)
- Node.js 18+   (`node --version`)

## Run it (4 terminals in VS Code: Terminal > New Terminal)

**Terminal 1 – databases (from project root)**
    docker compose up -d

**Terminal 2 – train model + start API/worker**
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r backend/requirements.txt
    python ml/train.py
    cd backend
    uvicorn app.main:app --reload --port 8000

**Terminal 3 – transaction generator**
    cd backend
    source ../.venv/bin/activate
    python producer.py --rate 2

**Terminal 4 – dashboard**
    cd frontend
    npm install
    npm run dev

Open http://localhost:5173

## Useful
- API docs: http://localhost:8000/docs
- More fraud: `python producer.py --fraud-ratio 0.2`
- Stop databases: `docker compose down` (add `-v` to wipe data)
