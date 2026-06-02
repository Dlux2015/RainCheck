import { useEffect, useState } from 'react'
import StormMap from './components/StormMap'
import PriceChart from './components/PriceChart'
import BuySignalCard from './components/BuySignalCard'
import MetricRow from './components/MetricRow'

export default function App() {
  const [signal, setSignal] = useState(null)
  const [prices, setPrices] = useState([])
  const [storms, setStorms] = useState([])

  useEffect(() => {
    fetch('/api/signal/latest').then(r => r.json()).then(setSignal).catch(console.error)
    fetch('/api/prices/history?days=14').then(r => r.json()).then(d => setPrices(d.prices ?? [])).catch(console.error)
    fetch('/api/storm/active').then(r => r.json()).then(d => setStorms(d.storms ?? [])).catch(console.error)
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Hurricane Gas Predictor</h1>
      <p style={{ color: '#6b7280', marginTop: 0 }}>
        Optimal gas buying windows during Atlantic hurricane events
      </p>
      {signal && <BuySignalCard signal={signal} />}
      <MetricRow storms={storms} prices={prices} />
      <StormMap storms={storms} />
      <PriceChart prices={prices} />
    </div>
  )
}
