function Metric({ label, value }) {
  return (
    <div style={{ padding: '12px 20px', background: '#f1f5f9', borderRadius: 8, minWidth: 140 }}>
      <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 600, marginTop: 4 }}>{value ?? '—'}</div>
    </div>
  )
}

export default function MetricRow({ storms = [], prices = [] }) {
  const activeStorms = storms.length
  const maxWind = storms.length ? Math.max(...storms.map(s => s.wind_speed_kt ?? 0)) : null
  const latestPrice = prices.length
    ? `$${Number(prices[prices.length - 1]?.price_usd).toFixed(3)}`
    : null

  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
      <Metric label="Active Storms" value={activeStorms} />
      <Metric label="Max Wind (kt)" value={maxWind} />
      <Metric label="Latest Price" value={latestPrice} />
    </div>
  )
}
