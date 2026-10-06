import { useState, useEffect } from 'react'

const API = '/api'

export default function Unknowns() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)

  const fetch_ = async () => {
    setLoading(true)
    try {
      const data = await fetch(`${API}/attendance?limit=200&name=unknown`).then(r => r.json())
      setRecords(data)
    } catch {
      setRecords([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch_()
    const id = setInterval(fetch_, 10_000)
    return () => clearInterval(id)
  }, [])

  return (
    <>
      <div className="page-title">Unknowns</div>
      <div className="page-subtitle">
        Unidentified faces detected below the recognition threshold
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <button className="btn primary" onClick={fetch_}>🔄 Refresh</button>
      </div>

      {loading ? <div className="spinner" /> : (
        records.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">🎉</div>
            <div>No unknown faces detected</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 14 }}>
            {records.map(rec => (
              <div key={rec.id} className="card" style={{ padding: 12 }}>
                {rec.photo
                  ? <img
                      src={`data:image/jpeg;base64,${rec.photo}`}
                      alt="unknown"
                      style={{ width: '100%', borderRadius: 6, marginBottom: 8, objectFit: 'cover', maxHeight: 120 }}
                    />
                  : <div style={{ width: '100%', height: 90, background: '#252550', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem', marginBottom: 8 }}>👤</div>
                }
                <div style={{ fontSize: '0.75rem', color: '#aaa' }}>
                  {rec.timestamp.replace('T', ' ').slice(0, 19)}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#ffa726', marginTop: 2 }}>
                  sim: {(rec.similarity * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </>
  )
}
