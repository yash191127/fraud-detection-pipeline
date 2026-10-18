function Gauge({ value }) {
  const C = 2 * Math.PI * 40;
  return (
    <svg className="gauge" width="104" height="104" viewBox="0 0 104 104" role="img" aria-label={`${Math.round(value * 100)} percent fraud probability`}>
      <circle cx="52" cy="52" r="40" className="gauge-track" />
      <circle
        cx="52" cy="52" r="40" className="gauge-fill"
        strokeDasharray={`${value * C} ${C}`}
        transform="rotate(-90 52 52)"
      />
      <text x="52" y="58" textAnchor="middle" className="gauge-text">{Math.round(value * 100)}%</text>
    </svg>
  );
}

export default function LatestAlert({ transactions }) {
  const alert = [...transactions].reverse().find((t) => t.is_fraud);

  if (!alert) {
    return (
      <section className="panel">
        <h2>Latest alert</h2>
        <p className="empty">No alerts yet. Flagged transactions will show up here.</p>
      </section>
    );
  }

  return (
    <section className="panel alert-panel" key={alert.txn_id}>
      <h2>Latest alert</h2>
      <div className="alert-body">
        <Gauge value={alert.fraud_probability} />
        <div>
          <div className="alert-amount">${alert.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="alert-meta">{alert.merchant_category}</div>
          <div className="alert-meta">{alert.channel} at {new Date(alert.created_at).toLocaleTimeString()}</div>
        </div>
      </div>
      <p className={`alert-verdict ${alert.true_class ? "confirmed" : "false-alarm"}`}>
        {alert.true_class
          ? `Confirmed fraud: ${alert.fraud_type}`
          : "Turned out to be genuine, a false alarm"}
      </p>
    </section>
  );
}
