import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const GRADES = [
  { key: 'regular',  label: 'Regular',  color: '#2563eb' },
  { key: 'midgrade', label: 'Midgrade', color: '#7c3aed' },
  { key: 'premium',  label: 'Premium',  color: '#059669' },
]

const FMT_TICK = new Intl.DateTimeFormat('en-US', { month: 'short', year: '2-digit', timeZone: 'UTC' })
const FMT_TIP  = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })

function toDate(periodStr) {
  return new Date(periodStr + 'T00:00:00Z')
}

export default function PriceChart({ prices = {} }) {
  // Merge all grades into a single sorted array keyed by period
  const periodMap = {}
  GRADES.forEach(({ key }) => {
    ;(prices[key] || []).forEach(p => {
      if (!periodMap[p.period]) periodMap[p.period] = { period: p.period }
      periodMap[p.period][key] = Number(p.price_usd)
    })
  })

  const data = Object.values(periodMap).sort((a, b) => (a.period > b.period ? 1 : -1))

  // Show ~12 ticks across the date range
  const tickInterval = Math.max(1, Math.floor(data.length / 12))

  const hasData = data.length > 0
  const newestPeriod = hasData ? data[data.length - 1].period : null

  return (
    <div style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0 }}>Gulf Coast Gas Price History</h2>
        {hasData && (
          <span style={{ fontSize: 13, color: '#6b7280' }}>
            {data.length} weekly observations · latest period&nbsp;
            {FMT_TIP.format(toDate(newestPeriod))}
          </span>
        )}
      </div>

      {!hasData ? (
        <p style={{ color: '#9ca3af' }}>No price data yet — run the ETL pipeline to populate.</p>
      ) : (
        <ResponsiveContainer width="100%" height={320} style={{ marginTop: 12 }}>
          <LineChart data={data} margin={{ top: 4, right: 16, bottom: 28, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="period"
              tickFormatter={p => FMT_TICK.format(toDate(p))}
              interval={tickInterval}
              tick={{ fontSize: 11 }}
              label={{ value: 'EIA weekly survey period', position: 'insideBottom', offset: -18, fontSize: 11, fill: '#9ca3af' }}
            />
            <YAxis
              domain={['auto', 'auto']}
              tickFormatter={v => `$${v.toFixed(2)}`}
              tick={{ fontSize: 11 }}
              width={52}
            />
            <Tooltip
              labelFormatter={p => `Week of ${FMT_TIP.format(toDate(p))}`}
              formatter={(v, name) => [`$${Number(v).toFixed(3)}/gal`, name]}
            />
            <Legend wrapperStyle={{ paddingTop: 8 }} />
            {GRADES.map(({ key, label, color }) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={label}
                stroke={color}
                dot={false}
                strokeWidth={2}
                connectNulls={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
