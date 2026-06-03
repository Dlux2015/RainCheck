import { useEffect, useState } from 'react'
import StormMap from './components/StormMap'
import PriceChart from './components/PriceChart'
import BuySignalCard from './components/BuySignalCard'
import MetricRow from './components/MetricRow'

// In production VITE_API_URL points to the deployed Railway/Render API.
// In development the Vite proxy rewrites /api → localhost:8000.
const API = import.meta.env.VITE_API_URL || '/api'

export default function App() {
  const [signal, setSignal]   = useState(null)
  const [prices, setPrices]   = useState({ regular: [], midgrade: [], premium: [] })
  const [storms, setStorms]   = useState([])

  useEffect(() => {
    fetch(`${API}/signal/latest`).then(r => r.json()).then(setSignal).catch(console.error)
    fetch(`${API}/storm/active`).then(r => r.json()).then(d => setStorms(d.storms ?? [])).catch(console.error)

    // Fetch all three grades in parallel — 2 years of weekly history
    Promise.all(
      ['regular', 'midgrade', 'premium'].map(grade =>
        fetch(`${API}/prices/history?grade=${grade}&days=730`)
          .then(r => r.json())
          .then(d => ({ grade, data: d.prices ?? [] }))
          .catch(() => ({ grade, data: [] }))
      )
    ).then(results => {
      const byGrade = {}
      results.forEach(({ grade, data }) => { byGrade[grade] = data })
      setPrices(byGrade)
    })
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Hurricane Gas Predictor</h1>
      <p style={{ color: '#6b7280', marginTop: 0 }}>
        Optimal gas buying windows during Atlantic hurricane events
      </p>
      {signal && <BuySignalCard signal={signal} />}
      <MetricRow storms={storms} prices={prices.regular} />
      <StormMap storms={storms} />
      <PriceChart prices={prices} />
    </div>
  )
}
