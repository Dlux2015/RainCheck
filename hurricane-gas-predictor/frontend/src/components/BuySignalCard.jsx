const FMT = new Intl.DateTimeFormat('en-US', {
  month: 'short', day: 'numeric', year: 'numeric',
  hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
})

function ConfidenceBar({ probability, threshold }) {
  const pct = Math.round(probability * 100)
  const threshPct = Math.round(threshold * 100)

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#6b7280', marginBottom: 4 }}>
        <span>0% — No storm risk</span>
        <span>100% — Extreme risk</span>
      </div>
      <div style={{ position: 'relative', background: '#e5e7eb', borderRadius: 6, height: 10, overflow: 'visible' }}>
        {/* Threshold marker */}
        <div style={{
          position: 'absolute',
          left: `${threshPct}%`,
          top: -4, bottom: -4,
          width: 2,
          background: '#dc2626',
          borderRadius: 2,
          zIndex: 2,
        }} />
        {/* Fill bar */}
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: pct >= threshPct ? '#16a34a' : '#3b82f6',
          borderRadius: 6,
          transition: 'width 0.4s ease',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginTop: 4 }}>
        <span style={{ color: '#3b82f6', fontWeight: 600 }}>{pct}% current</span>
        <span style={{ color: '#dc2626' }}>▲ {threshPct}% BUY threshold</span>
      </div>
    </div>
  )
}

export default function BuySignalCard({ signal }) {
  const isBuy = signal?.signal === 'BUY'
  const prob = signal?.probability ?? 0
  const threshold = signal?.threshold ?? 0.65
  const updatedAt = signal?.created_at ? FMT.format(new Date(signal.created_at)) : null

  return (
    <div style={{
      padding: 24,
      borderRadius: 12,
      background: isBuy ? '#dcfce7' : '#fef9c3',
      border: `2px solid ${isBuy ? '#16a34a' : '#ca8a04'}`,
      maxWidth: 480,
      marginBottom: 24,
    }}>
      <div style={{ fontSize: 36, fontWeight: 700, color: isBuy ? '#16a34a' : '#b45309' }}>
        {isBuy ? 'BUY NOW' : 'WAIT'}
      </div>

      <div style={{ marginTop: 6, color: '#374151', fontSize: 14 }}>
        {isBuy
          ? 'Hurricane activity near Gulf Coast refineries detected — prices likely to spike.'
          : 'No significant hurricane risk to Gulf Coast refineries detected.'}
      </div>

      <ConfidenceBar probability={prob} threshold={threshold} />

      <div style={{ marginTop: 14, fontSize: 12, color: '#6b7280', borderTop: '1px solid #e5e7eb', paddingTop: 10 }}>
        <div><strong>How to read this:</strong> The model scores hurricane risk to Gulf Coast
        oil infrastructure. Above {Math.round(threshold * 100)}% = BUY (fill up before supply
        disruptions). Below {Math.round(threshold * 100)}% = WAIT (no unusual risk).</div>
        <div style={{ marginTop: 6, color: '#9ca3af' }}>
          Key signals: active storm count, max wind speed, storm proximity to refineries,
          and recent price momentum.
        </div>
        {updatedAt && (
          <div style={{ marginTop: 6 }}>Last updated: {updatedAt}</div>
        )}
      </div>
    </div>
  )
}
