import { useState, useEffect } from 'react'

const REFRESH_MS = 10 * 60 * 1000  // re-fetch every 10 minutes

// All major Florida locations available for selection
export const FLORIDA_CITIES = [
  { name: 'Daytona Beach',   lat: 29.211, lon: -81.023, region: 'East Coast' },
  { name: 'Fort Lauderdale', lat: 26.122, lon: -80.137, region: 'South' },
  { name: 'Fort Myers',      lat: 26.641, lon: -81.872, region: 'Southwest' },
  { name: 'Gainesville',     lat: 29.652, lon: -82.325, region: 'North Central' },
  { name: 'Jacksonville',    lat: 30.332, lon: -81.656, region: 'Northeast' },
  { name: 'Key West',        lat: 24.555, lon: -81.780, region: 'Keys' },
  { name: 'Miami',           lat: 25.762, lon: -80.192, region: 'South' },
  { name: 'Naples',          lat: 26.142, lon: -81.795, region: 'Southwest' },
  { name: 'Orlando',         lat: 28.538, lon: -81.379, region: 'Central' },
  { name: 'Panama City',     lat: 30.159, lon: -85.660, region: 'Panhandle' },
  { name: 'Pensacola',       lat: 30.421, lon: -87.217, region: 'Panhandle' },
  { name: 'Sarasota',        lat: 27.336, lon: -82.531, region: 'West Coast' },
  { name: 'St. Augustine',   lat: 29.895, lon: -81.315, region: 'Northeast' },
  { name: 'Tallahassee',     lat: 30.452, lon: -84.281, region: 'Capital' },
  { name: 'Tampa',           lat: 27.951, lon: -82.457, region: 'West Coast' },
  { name: 'West Palm Beach', lat: 26.715, lon: -80.053, region: 'South' },
]

export const DEFAULT_CITY = FLORIDA_CITIES.find(c => c.name === 'Orlando')

function getCategory(code) {
  if (code === 0)   return 'clear'
  if (code <= 3)    return 'partly_cloudy'
  if (code <= 48)   return 'cloudy'
  if (code <= 67)   return 'rain'
  if (code <= 82)   return 'rain'
  if (code >= 95)   return 'storm'
  return 'cloudy'
}

function getPhase(isDay, sunrise, sunset) {
  if (!sunrise || !sunset) return isDay ? 'day' : 'night'
  const now = Date.now()
  const sr  = new Date(sunrise).getTime()
  const ss  = new Date(sunset).getTime()
  const buf = 40 * 60 * 1000
  if (now >= sr - buf && now < sr + buf) return 'dawn'
  if (now >= ss - buf && now < ss + buf) return 'dusk'
  return isDay ? 'day' : 'night'
}

function timeBasedFallback() {
  const h = new Date().getHours()
  return { code: 0, category: 'clear', phase: h >= 6 && h < 20 ? 'day' : 'night', tempC: null }
}

export function useWeather(city = DEFAULT_CITY) {
  const [weather, setWeather] = useState(timeBasedFallback)

  useEffect(() => {
    const load = () =>
      fetch(
        `https://api.open-meteo.com/v1/forecast` +
        `?latitude=${city.lat}&longitude=${city.lon}` +
        `&current=weather_code,is_day,temperature_2m` +
        `&daily=sunrise,sunset` +
        `&timezone=America%2FNew_York&forecast_days=1`
      )
        .then(r => r.json())
        .then(d => {
          const code  = d.current?.weather_code  ?? 0
          const isDay = (d.current?.is_day ?? 1)  === 1
          const tempC = d.current?.temperature_2m ?? null
          const sr    = d.daily?.sunrise?.[0]
          const ss    = d.daily?.sunset?.[0]
          setWeather({ code, category: getCategory(code), phase: getPhase(isDay, sr, ss), tempC })
        })
        .catch(() => setWeather(timeBasedFallback()))

    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [city.lat, city.lon])   // re-fetch whenever the selected city changes

  return weather
}
