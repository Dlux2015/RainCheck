import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const GULF_CENTER = [25.0, -87.0]

export default function StormMap({ storms = [] }) {
  return (
    <div style={{ marginTop: 24 }}>
      <h2>Active Storms</h2>
      <MapContainer center={GULF_CENTER} zoom={4} style={{ height: 400, borderRadius: 8 }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        {storms.map(storm => (
          <CircleMarker
            key={storm.storm_id}
            center={[storm.lat, storm.lon]}
            radius={Math.max(8, (storm.wind_speed_kt ?? 0) / 10)}
            color="#dc2626"
            fillOpacity={0.5}
          >
            <Popup>
              <strong>{storm.storm_name}</strong>
              <br />
              {storm.wind_speed_kt} kt
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}
