import { useState, useEffect } from 'react'

// Central Florida (Orlando) — representative of the majority of the state
const LAT = 28.5
const LON = -81.4
const REFRESH_MS = 10 * 60 * 1000  // re-fetch every 10 minutes

export const WEATHER_LABELS = {
  clear:         'Clear',
  partly_cloudy: 'Partly Cloudy',
  cloudy:        'Overcast',
  rain:          'Rain',
  storm:         'Thunderstorm',
}

function getCategory(code) {
  if (code === 0)            return 'clear'
  if (code <= 3)             return 'partly_cloudy'
  if (code <= 48)            return 'cloudy'         // fog / depositing rime
  if (code <= 67)            return 'rain'            // drizzle + rain
  if (code <= 77)            return 'cloudy'          // snow (won't happen in FL)
  if (code <= 82)            return 'rain'            // rain showers
  if (code >= 95)            return 'storm'           // thunderstorm
  return 'cloudy'
}

function getPhase(isDay, sunrise, sunset) {
  if (!sunrise || !sunset) return isDay ? 'day' : 'night'
  const now = Date.now()
  const sr  = new Date(sunrise).getTime()
  const ss  = new Date(sunset).getTime()
  const buf = 40 * 60 * 1000  // 40-min golden-hour buffer
  if (now >= sr - buf && now < sr + buf) return 'dawn'
  if (now >= ss - buf && now < ss + buf) return 'dusk'
  return isDay ? 'day' : 'night'
}

function fallback() {
  const h = new Date().getHours()
  return { code: 0, category: 'clear', phase: h >= 6 && h < 20 ? 'day' : 'night', tempC: null }
}

export function useWeather() {
  const [weather, setWeather] = useState(fallback)

  useEffect(() => {
    const load = () =>
      fetch(
        `https://api.open-meteo.com/v1/forecast` +
        `?latitude=${LAT}&longitude=${LON}` +
        `&current=weather_code,is_day,temperature_2m` +
        `&daily=sunrise,sunset` +
        `&timezone=America%2FNew_York&forecast_days=1`
      )
        .then(r => r.json())
        .then(d => {
          const code   = d.current?.weather_code  ?? 0
          const isDay  = (d.current?.is_day ?? 1)  === 1
          const tempC  = d.current?.temperature_2m ?? null
          const sr     = d.daily?.sunrise?.[0]
          const ss     = d.daily?.sunset?.[0]
          setWeather({ code, category: getCategory(code), phase: getPhase(isDay, sr, ss), tempC })
        })
        .catch(() => setWeather(fallback()))

    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [])

  return weather
}
