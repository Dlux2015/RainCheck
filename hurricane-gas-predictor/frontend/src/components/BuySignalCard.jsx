export default function BuySignalCard({ signal }) {
  const isBuy = signal?.signal === 'BUY'
  const prob = ((signal?.probability ?? 0) * 100).toFixed(1)

  return (
    <div
      style={{
        padding: 24,
        borderRadius: 12,
        background: isBuy ? '#dcfce7' : '#fef9c3',
        border: `2px solid ${isBuy ? '#16a34a' : '#ca8a04'}`,
        maxWidth: 360,
        marginBottom: 24,
      }}
    >
      <div style={{ fontSize: 36, fontWeight: 700, color: isBuy ? '#16a34a' : '#b45309' }}>
        {isBuy ? 'BUY NOW' : 'WAIT'}
      </div>
      <div style={{ marginTop: 8, color: '#374151' }}>
        Model confidence: <strong>{prob}%</strong>
      </div>
      <div style={{ marginTop: 4, fontSize: 12, color: '#6b7280' }}>
        Threshold: {((signal?.threshold ?? 0) * 100).toFixed(0)}% &nbsp;|&nbsp; Signal as of latest poll
      </div>
    </div>
  )
}
