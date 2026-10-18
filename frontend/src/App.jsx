import { useEffect, useRef, useState } from "react";
import MetricCards from "./components/MetricCards.jsx";
import RealTimeChart from "./components/RealTimeChart.jsx";
import LatestAlert from "./components/LatestAlert.jsx";
import CategoryBreakdown from "./components/CategoryBreakdown.jsx";
import TransactionTable from "./components/TransactionTable.jsx";

const API = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws";
const MAX_ROWS = 200;

function Logo() {
  return (
    <svg width="38" height="38" viewBox="0 0 38 38" aria-hidden="true">
      <rect width="38" height="38" rx="11" fill="#2F4BFF" />
      <path d="M19 8l9 3.5v6.2c0 5.4-3.6 9.2-9 11.3-5.4-2.1-9-5.9-9-11.3v-6.2L19 8z" fill="none" stroke="#fff" strokeWidth="2" strokeLinejoin="round" />
      <path d="M14.5 19.5l3.2 3.2 6-6.4" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function App() {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({ total: 0, fraud: 0, fraud_rate: 0, volume: 0, flagged_volume: 0, actual_fraud: 0, caught: 0 });
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  // Initial load from the REST API
  useEffect(() => {
    fetch(`${API}/api/transactions?limit=${MAX_ROWS}`)
      .then((r) => r.json())
      .then(setTransactions)
      .catch(() => {});
    fetch(`${API}/api/stats`).then((r) => r.json()).then(setStats).catch(() => {});
  }, []);

  // Live updates over WebSocket (auto-reconnects)
  useEffect(() => {
    let retry;
    let closed = false;

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closed) retry = setTimeout(connect, 2000);
      };
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type !== "transaction") return;
        const t = msg.data;
        setTransactions((prev) => [...prev, t].slice(-MAX_ROWS));
        setStats((s) => {
          const total = s.total + 1;
          const fraud = s.fraud + (t.is_fraud ? 1 : 0);
          return {
            total,
            fraud,
            fraud_rate: Math.round((fraud / total) * 10000) / 100,
            volume: s.volume + t.amount,
            flagged_volume: s.flagged_volume + (t.is_fraud ? t.amount : 0),
            actual_fraud: s.actual_fraud + (t.true_class ? 1 : 0),
            caught: s.caught + (t.is_fraud && t.true_class ? 1 : 0),
          };
        });
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, []);

  return (
    <>
      <div className="hero">
        <div className="inner">
          <header className="topbar">
            <div className="brand">
              <Logo />
              <div>
                <h1>Fraud Watch</h1>
                <p>Real card transactions, scored the moment they arrive.</p>
              </div>
            </div>
            <div className={`status ${connected ? "on" : "off"}`}>
              <span className="dot" />
              {connected ? "Live" : "Reconnecting..."}
            </div>
          </header>
          <MetricCards stats={stats} />
        </div>
      </div>

      <main className="inner main">
        <div className="grid">
          <RealTimeChart transactions={transactions.slice(-60)} />
          <aside className="side">
            <LatestAlert transactions={transactions} />
            <CategoryBreakdown transactions={transactions} />
          </aside>
        </div>
        <TransactionTable transactions={transactions} />
      </main>
    </>
  );
}
