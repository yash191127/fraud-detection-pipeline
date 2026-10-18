const money = (n) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export default function MetricCards({ stats }) {
  const caughtPct = stats.actual_fraud ? Math.round((stats.caught / stats.actual_fraud) * 100) : 0;

  return (
    <section className="metrics" aria-label="Summary">
      <div className="metric">
        <span className="metric-label">Transactions scored</span>
        <span className="metric-value">{stats.total.toLocaleString()}</span>
        <span className="metric-sub">since the pipeline started</span>
      </div>

      <div className="metric">
        <span className="metric-label">Flagged as suspicious</span>
        <span className={`metric-value ${stats.fraud > 0 ? "alert" : ""}`}>{stats.fraud.toLocaleString()}</span>
        <span className="metric-sub">{stats.fraud_rate}% of all transactions</span>
      </div>

      <div className="metric">
        <span className="metric-label">Real fraud caught</span>
        <span className="metric-value">
          {stats.caught} <small>of {stats.actual_fraud}</small>
        </span>
        <span className="meter" aria-hidden="true">
          <span style={{ width: `${caughtPct}%` }} />
        </span>
        <span className="metric-sub">{caughtPct}% of known fraud</span>
      </div>

      <div className="metric">
        <span className="metric-label">Money held for review</span>
        <span className={`metric-value ${stats.flagged_volume > 0 ? "alert" : ""}`}>{money(stats.flagged_volume)}</span>
        <span className="metric-sub">from flagged transactions</span>
      </div>
    </section>
  );
}
