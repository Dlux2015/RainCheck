import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

export default function PriceChart({ prices = [] }) {
  const data = prices.map(p => ({
    date: new Date(p.ingested_at).toLocaleDateString(),
    price: p.price_usd,
  }))

  return (
    <div style={{ marginTop: 24 }}>
      <h2>Gas Price History (Gulf Coast — Regular)</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis domain={['auto', 'auto']} tickFormatter={v => `$${v.toFixed(2)}`} />
          <Tooltip formatter={v => [`$${Number(v).toFixed(3)}`, 'Price']} />
          <Legend />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#2563eb"
            dot={false}
            name="Price (USD/gal)"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
