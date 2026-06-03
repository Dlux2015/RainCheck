const FMT = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })

function Metric({ label, value, sub }) {
  return (
    <div style={{ padding: '12px 20px', minWidth: 140 }}>
      <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 600, marginTop: 4 }}>{value ?? '—'}</div>
      {sub && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export default function MetricRow({ storms = [], prices = [] }) {
  const activeStorms = storms.length
  const maxWind = storms.length ? Math.max(...storms.map(s => s.wind_speed_kt ?? 0)) : null

  // Most recent price by period date
  const sortedPrices = [...prices].sort((a, b) => (a.period > b.period ? 1 : -1))
  const latestRegular = sortedPrices.filter(p => p.grade === 'regular').slice(-1)[0]
  const latestPrice = latestRegular ? `$${Number(latestRegular.price_usd).toFixed(3)}` : null
  const latestPriceDate = latestRegular
    ? `Updated ${FMT.format(new Date(latestRegular.period + 'T00:00:00Z'))}`
    : null

  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <Metric label="Active Storms" value={activeStorms} sub={activeStorms === 0 ? 'Off-season / clear' : `${activeStorms} active`} />
      <Metric label="Max Wind (kt)" value={maxWind} sub={maxWind ? 'Current advisory' : 'No active storm'} />
      <Metric label="Regular Gas (Gulf)" value={latestPrice} sub={latestPriceDate} />
    </div>
  )
}
