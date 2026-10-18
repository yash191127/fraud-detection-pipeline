import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function Tip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const t = payload[0].payload;
  return (
    <div className="tip">
      <strong>${t.amount.toLocaleString()}</strong> at {t.merchant_category}
      <div className={t.is_fraud ? "bad" : "good"}>
        {(t.fraud_probability * 100).toFixed(1)}% fraud probability
      </div>
      <div>Actual: {t.true_class ? `fraud (${t.fraud_type})` : "genuine"}</div>
    </div>
  );
}

export default function RealTimeChart({ transactions }) {
  const data = transactions.map((t, i) => ({ ...t, n: i }));

  return (
    <section className="panel chart-panel">
      <div className="panel-head">
        <div>
          <h2>Fraud risk, last {transactions.length || 60} transactions</h2>
          <p className="panel-sub">Each bar is one transaction. Taller means the model is more worried.</p>
        </div>
        <span className="legend">
          <i className="swatch ok" /> Normal
          <i className="swatch bad" /> Flagged
        </span>
      </div>

      {data.length === 0 ? (
        <p className="empty">Waiting for transactions. Start the producer: <code>python producer.py</code></p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 0 }} barCategoryGap={2}>
            <XAxis dataKey="n" hide />
            <YAxis
              domain={[0, 1]}
              ticks={[0, 0.25, 0.5, 0.75, 1]}
              tickFormatter={(v) => `${v * 100}%`}
              tickLine={false}
              axisLine={false}
              width={44}
            />
            <Tooltip content={<Tip />} cursor={{ className: "chart-cursor" }} />
            <Bar dataKey="fraud_probability" radius={[3, 3, 0, 0]} isAnimationActive={false}>
              {data.map((t) => (
                <Cell key={t.txn_id} className={t.is_fraud ? "bar-bad" : "bar-ok"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </section>
  );
}
