import { useEffect, useState } from 'react'
import StormMap from './components/StormMap'
import PriceChart from './components/PriceChart'
import BuySignalCard from './components/BuySignalCard'
import MetricRow from './components/MetricRow'
import WeatherBackground, { WeatherChip } from './components/WeatherBackground'
import { useWeather, DEFAULT_CITY } from './hooks/useWeather'

const API = import.meta.env.VITE_API_URL || '/api'

// Cards and panels need enough opacity to read on any sky colour.
// We use a frosted-glass treatment so the background still bleeds through subtly.
const glass = {
  background: 'rgba(255,255,255,0.82)',
  backdropFilter: 'blur(10px)',
  WebkitBackdropFilter: 'blur(10px)',
  borderRadius: 16,
  border: '1px solid rgba(255,255,255,0.55)',
  boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
}

function useBuyNotification(signal) {
  useEffect(() => {
    if (signal?.signal !== 'BUY') return
    if (!('Notification' in window)) return
    const notify = () => {
      if (Notification.permission === 'granted') {
        new Notification('Hurricane Gas Predictor', {
          body: `BUY signal — ${Math.round((signal.probability ?? 0) * 100)}% confidence. Fill up before prices spike.`,
          icon: '/vite.svg',
        })
      }
    }
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(p => { if (p === 'granted') notify() })
    } else {
      notify()
    }
  }, [signal?.signal])
}

export default function App() {
  const [signal, setSignal] = useState(null)
  const [accuracy, setAccuracy] = useState(null)
  const [prices, setPrices] = useState({ regular: [], midgrade: [], premium: [] })
  const [storms, setStorms] = useState([])
  const [buyBannerDismissed, setBuyBannerDismissed] = useState(false)
  const [selectedCity, setSelectedCity] = useState(DEFAULT_CITY)
  const weather = useWeather(selectedCity)

  useBuyNotification(signal)

  useEffect(() => {
    fetch(`${API}/signal/latest`).then(r => r.json()).then(setSignal).catch(console.error)
    fetch(`${API}/signal/accuracy`).then(r => r.json()).then(setAccuracy).catch(console.error)
    fetch(`${API}/storm/active`).then(r => r.json()).then(d => setStorms(d.storms ?? [])).catch(console.error)

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
    <>
      {/* Dynamic Florida sky — fixed behind everything */}
      <WeatherBackground weather={weather} />

      {/* All content sits above the sky at z-index 1 */}
      <div style={{
        position: 'relative', zIndex: 1,
        fontFamily: 'system-ui, sans-serif',
        maxWidth: 1200, margin: '0 auto',
        padding: '24px 24px 48px',
        minHeight: '100vh',
      }}>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <h1 style={{
            margin: '0 0 4px',
            color: '#fff',
            textShadow: '0 2px 8px rgba(0,0,0,0.45)',
            fontSize: 32,
          }}>
            Hurricane Gas Predictor
          </h1>
          <p style={{
            margin: '0 0 10px',
            color: 'rgba(255,255,255,0.85)',
            textShadow: '0 1px 4px rgba(0,0,0,0.4)',
          }}>
            Optimal gas buying windows during Atlantic hurricane events
          </p>
          <WeatherChip
            weather={weather}
            selectedCity={selectedCity}
            onCityChange={setSelectedCity}
          />
        </div>

        {/* Dismissable BUY banner */}
        {signal?.signal === 'BUY' && !buyBannerDismissed && (
          <div style={{
            background: '#166534', color: '#fff',
            borderRadius: 10, padding: '12px 20px', marginBottom: 16,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            boxShadow: '0 2px 12px rgba(0,0,0,0.25)',
          }}>
            <span style={{ fontWeight: 600 }}>
              ⚡ BUY SIGNAL ACTIVE — Hurricane activity threatens Gulf Coast refineries. Fill up now.
            </span>
            <button
              onClick={() => setBuyBannerDismissed(true)}
              style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
              aria-label="Dismiss"
            >✕</button>
          </div>
        )}

        {/* Signal card — already has coloured background, just lift slightly */}
        {signal && (
          <div style={{ marginBottom: 20 }}>
            <BuySignalCard signal={signal} accuracy={accuracy} />
          </div>
        )}

        {/* Metrics row — wrap in glass */}
        <div style={{ ...glass, padding: '16px 20px', marginBottom: 20 }}>
          <MetricRow storms={storms} prices={prices.regular} />
        </div>

        {/* Storm map — wrap in glass */}
        <div style={{ ...glass, padding: 16, marginBottom: 20, overflow: 'hidden' }}>
          <StormMap storms={storms} />
        </div>

        {/* Price chart — wrap in glass */}
        <div style={{ ...glass, padding: '16px 20px' }}>
          <PriceChart prices={prices} />
        </div>
      </div>
    </>
  )
}
