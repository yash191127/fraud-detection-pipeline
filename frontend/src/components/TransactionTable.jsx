export default function TransactionTable({ transactions }) {
  const rows = [...transactions].reverse().slice(0, 15);

  return (
    <section className="panel table-panel">
      <div className="panel-head">
        <h2>Latest transactions</h2>
        <p className="panel-sub">Red rows were flagged by the model.</p>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Merchant</th>
              <th>Channel</th>
              <th className="num">Amount</th>
              <th>Fraud probability</th>
              <th>Model verdict</th>
              <th>Actual label</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="empty">No transactions yet.</td>
              </tr>
            )}
            {rows.map((t) => (
              <tr key={t.txn_id} className={t.is_fraud ? "flagged" : ""}>
                <td>{new Date(t.created_at).toLocaleTimeString()}</td>
                <td>{t.merchant_category}</td>
                <td>{t.channel}</td>
                <td className="num">${t.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td>
                  <span className="prob">
                    <span className="prob-track">
                      <span className={t.is_fraud ? "bad" : ""} style={{ width: `${Math.max(2, t.fraud_probability * 100)}%` }} />
                    </span>
                    {(t.fraud_probability * 100).toFixed(1)}%
                  </span>
                </td>
                <td>
                  <span className={`badge ${t.is_fraud ? "bad" : "ok"}`}>{t.is_fraud ? "Flagged" : "Normal"}</span>
                </td>
                <td>
                  <span className={`badge ${t.true_class ? "bad" : "ok"}`}>
                    {t.true_class ? `Fraud: ${t.fraud_type}` : "Genuine"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
