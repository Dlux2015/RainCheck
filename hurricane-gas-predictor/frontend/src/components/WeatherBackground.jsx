import { useMemo, useState, useEffect, useRef } from 'react'
import { FLORIDA_CITIES } from '../hooks/useWeather'

// ---------------------------------------------------------------------------
// Sky gradients keyed by [category][phase]
// ---------------------------------------------------------------------------
const GRADIENTS = {
  clear: {
    day:   'linear-gradient(to bottom, #1565c0 0%, #42a5f5 40%, #bbdefb 100%)',
    dawn:  'linear-gradient(to bottom, #b71c1c 0%, #ef6c00 25%, #ffa726 50%, #ffe082 75%, #90caf9 100%)',
    dusk:  'linear-gradient(to bottom, #311b92 0%, #7b1fa2 20%, #c62828 45%, #e65100 65%, #f9a825 85%, #fff9c4 100%)',
    night: 'linear-gradient(to bottom, #010b19 0%, #061a35 55%, #0d2244 100%)',
  },
  partly_cloudy: {
    day:   'linear-gradient(to bottom, #1976d2 0%, #64b5f6 45%, #cfd8e8 100%)',
    dawn:  'linear-gradient(to bottom, #8d1a00 0%, #d4622b 35%, #a0c0d8 100%)',
    dusk:  'linear-gradient(to bottom, #1a0a3d 0%, #78194b 35%, #bf4e12 65%, #e8a02a 100%)',
    night: 'linear-gradient(to bottom, #0a1520 0%, #152236 55%, #1e2f45 100%)',
  },
  cloudy: {
    day:   'linear-gradient(to bottom, #455a64 0%, #78909c 45%, #b0bec5 100%)',
    dawn:  'linear-gradient(to bottom, #3e2723 0%, #795548 45%, #9e9e9e 100%)',
    dusk:  'linear-gradient(to bottom, #1a1220 0%, #4a3050 55%, #6d5060 100%)',
    night: 'linear-gradient(to bottom, #121820 0%, #1f2a35 100%)',
  },
  rain: {
    day:   'linear-gradient(to bottom, #263238 0%, #37474f 45%, #546e7a 100%)',
    dawn:  'linear-gradient(to bottom, #1a1520 0%, #2e3f50 100%)',
    dusk:  'linear-gradient(to bottom, #100c18 0%, #1e2d3a 100%)',
    night: 'linear-gradient(to bottom, #060c12 0%, #0d1c2a 100%)',
  },
  storm: {
    day:   'linear-gradient(to bottom, #0d1b24 0%, #1c2d3c 50%, #28404f 100%)',
    dawn:  'linear-gradient(to bottom, #080c10 0%, #12202c 100%)',
    dusk:  'linear-gradient(to bottom, #060810 0%, #0e1820 100%)',
    night: 'linear-gradient(to bottom, #030508 0%, #0a1018 100%)',
  },
}

function getGradient(category, phase) {
  const cat = GRADIENTS[category] || GRADIENTS.clear
  return cat[phase] || cat.day
}

// ---------------------------------------------------------------------------
// Stars
// ---------------------------------------------------------------------------
function Stars() {
  const stars = useMemo(() =>
    Array.from({ length: 160 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 65,
      size: Math.random() * 1.8 + 0.4,
      opacity: Math.random() * 0.5 + 0.45,
      twinkleDur: 2 + Math.random() * 3,
      twinkleDelay: Math.random() * 4,
    })), [])

  return (
    <>
      <style>{`
        @keyframes wx-twinkle {
          0%,100% { opacity: var(--s-op); }
          50%      { opacity: calc(var(--s-op) * 0.25); }
        }
      `}</style>
      {stars.map(s => (
        <div key={s.id} style={{
          position: 'absolute', left: `${s.x}%`, top: `${s.y}%`,
          width: s.size, height: s.size, borderRadius: '50%',
          background: '#fff', '--s-op': s.opacity, opacity: s.opacity,
          animation: `wx-twinkle ${s.twinkleDur}s ease-in-out ${s.twinkleDelay}s infinite`,
        }} />
      ))}
    </>
  )
}

// ---------------------------------------------------------------------------
// Moon
// ---------------------------------------------------------------------------
function Moon() {
  return (
    <div style={{
      position: 'absolute', top: '7%', right: '10%',
      width: 52, height: 52, borderRadius: '50%',
      background: '#fffde7',
      boxShadow: '0 0 18px 5px rgba(255,253,231,0.45), 0 0 50px 12px rgba(255,253,231,0.12)',
    }} />
  )
}

// ---------------------------------------------------------------------------
// Sun
// ---------------------------------------------------------------------------
function Sun({ phase }) {
  const isDawn = phase === 'dawn'
  const isDusk = phase === 'dusk'
  const pos  = isDawn ? { bottom: '12%', left: '12%' }
             : isDusk ? { bottom:  '8%', right: '10%' }
             :           { top:    '8%', right: '12%' }
  const size = isDawn || isDusk ? 60 : 76
  const core = isDawn || isDusk
    ? 'radial-gradient(circle, #fff3e0 25%, #ff8f00 65%, transparent 100%)'
    : 'radial-gradient(circle, #fffde7 25%, #ffd600 65%, transparent 100%)'
  const glow = isDawn || isDusk
    ? '0 0 28px 8px rgba(255,110,0,0.45), 0 0 60px 18px rgba(255,160,0,0.2)'
    : '0 0 28px 8px rgba(255,210,0,0.5),  0 0 70px 22px rgba(255,220,0,0.2)'

  return (
    <div style={{
      position: 'absolute', ...pos,
      width: size, height: size, borderRadius: '50%',
      background: core, boxShadow: glow,
    }} />
  )
}

// ---------------------------------------------------------------------------
// Rain
// ---------------------------------------------------------------------------
function Rain({ heavy }) {
  const count = heavy ? 120 : 80
  const drops = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 112 - 6,
      delay: Math.random() * 2,
      dur: 0.55 + Math.random() * 0.35,
      op: 0.25 + Math.random() * 0.4,
      len: 9 + Math.random() * 10,
    })), [count])

  return (
    <>
      <style>{`
        @keyframes wx-rain {
          0%   { transform: translateY(-20px) rotate(8deg); opacity:0; }
          8%   { opacity: var(--d-op); }
          92%  { opacity: var(--d-op); }
          100% { transform: translateY(110vh) rotate(8deg); opacity:0; }
        }
      `}</style>
      {drops.map(d => (
        <div key={d.id} style={{
          position: 'absolute', left: `${d.x}%`, top: 0,
          width: 1.2, height: d.len,
          background: 'linear-gradient(to bottom, transparent, rgba(174,214,241,0.85))',
          '--d-op': d.op,
          animation: `wx-rain ${d.dur}s linear ${d.delay}s infinite`,
        }} />
      ))}
    </>
  )
}

// ---------------------------------------------------------------------------
// Lightning
// ---------------------------------------------------------------------------
function Lightning() {
  return (
    <>
      <style>{`
        @keyframes wx-bolt {
          0%,88%,90%,92%,100% { opacity:0; }
          89%,91% { opacity:0.18; }
        }
      `}</style>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'white',
        animation: 'wx-bolt 7s ease-in-out infinite',
      }} />
    </>
  )
}

// ---------------------------------------------------------------------------
// Weather info chip — clickable city selector
// ---------------------------------------------------------------------------
export function WeatherChip({ weather, selectedCity, onCityChange }) {
  const { category, phase, tempC } = weather
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handler = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const label = {
    clear:         phase === 'night' ? 'Clear Night' : phase === 'dawn' ? 'Sunrise' : phase === 'dusk' ? 'Sunset' : 'Clear',
    partly_cloudy: 'Partly Cloudy',
    cloudy:        'Overcast',
    rain:          'Rain',
    storm:         'Thunderstorm',
  }[category] || 'Clear'

  const icon = {
    clear:         phase === 'night' ? '🌙' : phase === 'dawn' ? '🌅' : phase === 'dusk' ? '🌇' : '☀️',
    partly_cloudy: '⛅',
    cloudy:        '☁️',
    rain:          '🌧️',
    storm:         '⛈️',
  }[category] || '☀️'

  const tempF = tempC !== null ? Math.round(tempC * 9 / 5 + 32) : null

  // Group cities by region for the dropdown
  const regions = FLORIDA_CITIES.reduce((acc, city) => {
    if (!acc[city.region]) acc[city.region] = []
    acc[city.region].push(city)
    return acc
  }, {})

  const chipStyle = {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    background: 'rgba(0,0,0,0.28)', backdropFilter: 'blur(6px)',
    borderRadius: 20, padding: '4px 12px',
    fontSize: 12, color: 'rgba(255,255,255,0.88)',
    border: `1px solid ${open ? 'rgba(255,255,255,0.45)' : 'rgba(255,255,255,0.15)'}`,
    cursor: 'pointer', userSelect: 'none',
    transition: 'border-color 0.15s, background 0.15s',
  }

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <div style={chipStyle} onClick={() => setOpen(o => !o)}>
        <span>{icon}</span>
        <span>
          {selectedCity.name}, FL · {label}
          {tempF !== null ? ` · ${tempF}°F` : ''}
        </span>
        <span style={{ opacity: 0.7, fontSize: 9, marginLeft: 2 }}>{open ? '▲' : '▼'}</span>
      </div>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', left: 0,
          minWidth: 220, maxHeight: 320, overflowY: 'auto',
          background: 'rgba(10,20,35,0.88)', backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: 12, padding: '6px 0',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          zIndex: 100,
        }}>
          {Object.entries(regions).sort().map(([region, cities]) => (
            <div key={region}>
              <div style={{
                padding: '4px 14px 2px',
                fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase',
              }}>
                {region}
              </div>
              {cities.map(city => (
                <div
                  key={city.name}
                  onClick={() => { onCityChange(city); setOpen(false) }}
                  style={{
                    padding: '7px 14px',
                    fontSize: 13,
                    color: city.name === selectedCity.name
                      ? 'rgba(255,255,255,1)'
                      : 'rgba(255,255,255,0.75)',
                    background: city.name === selectedCity.name
                      ? 'rgba(255,255,255,0.12)'
                      : 'transparent',
                    cursor: 'pointer',
                    transition: 'background 0.1s',
                    fontWeight: city.name === selectedCity.name ? 600 : 400,
                  }}
                  onMouseEnter={e => { if (city.name !== selectedCity.name) e.target.style.background = 'rgba(255,255,255,0.07)' }}
                  onMouseLeave={e => { if (city.name !== selectedCity.name) e.target.style.background = 'transparent' }}
                >
                  {city.name}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------
export default function WeatherBackground({ weather }) {
  const { category, phase } = weather
  const gradient    = getGradient(category, phase)
  const showStars   = phase === 'night' || (phase === 'dawn' && category !== 'storm')
  const showMoon    = phase === 'night' && category !== 'rain' && category !== 'storm'
  const showSun     = ['day','dawn','dusk'].includes(phase) && !['rain','storm'].includes(category)
  const showRain    = category === 'rain' || category === 'storm'
  const showLightn  = category === 'storm'

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 0,
      background: gradient,
      transition: 'background 3s ease',
      overflow: 'hidden',
    }}>
      {showStars   && <Stars />}
      {showMoon    && <Moon />}
      {showSun     && <Sun phase={phase} />}
      {showRain    && <Rain heavy={category === 'storm'} />}
      {showLightn  && <Lightning />}
    </div>
  )
}
