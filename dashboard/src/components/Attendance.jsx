import { useState, useEffect } from 'react'

const API = '/api'

export default function Attendance() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [date, setDate]       = useState('')
  const [name, setName]       = useState('')

  const fetch_ = async () => {
    setLoading(true)
    const params = new URLSearchParams({ limit: 200 })
    if (date) params.set('date', date)
    if (name) params.set('name', name)
    try {
      const data = await fetch(`${API}/attendance?${params}`).then(r => r.json())
      setRecords(data)
    } catch {
      setRecords([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch_() }, [])

  return (
    <>
      <div className="page-title">Attendance</div>
      <div className="page-subtitle">Face recognition & attendance verification logs</div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div>
          <label className="field-label">Filter by date</label>
          <input
            type="text"
            placeholder="YYYY-MM-DD"
            value={date}
            onChange={e => setDate(e.target.value)}
            style={{ width: 150 }}
          />
        </div>
        <div>
          <label className="field-label">Filter by name</label>
          <input
            type="text"
            placeholder="person name"
            value={name}
            onChange={e => setName(e.target.value)}
            style={{ width: 160 }}
          />
        </div>
        <div style={{ alignSelf: 'flex-end' }}>
          <button className="btn primary" onClick={fetch_}>🔍 Search</button>
        </div>
        <div style={{ alignSelf: 'flex-end' }}>
          <button className="btn" style={{ background: '#252550' }} onClick={() => { setDate(''); setName(''); setTimeout(fetch_, 0) }}>
            ✕ Clear
          </button>
        </div>
      </div>

      {loading ? <div className="spinner" /> : (
        <div className="table-wrap">
          {records.length === 0 ? (
            <div className="empty">
              <div className="empty-icon">📋</div>
              <div>No records found</div>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Photo</th>
                  <th>Name</th>
                  <th>Similarity</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec, i) => (
                  <tr key={rec.id}>
                    <td style={{ color: '#555', fontSize: '0.75rem' }}>{i + 1}</td>
                    <td>
                      {rec.photo
                        ? <img className="thumb" src={`data:image/jpeg;base64,${rec.photo}`} alt={rec.name} />
                        : <div className="thumb-placeholder">👤</div>
                      }
                    </td>
                    <td>
                      <span className={`badge ${rec.name === 'unknown' ? 'unknown' : 'known'}`}>
                        {rec.name}
                      </span>
                    </td>
                    <td>{(rec.similarity * 100).toFixed(1)}%</td>
                    <td style={{ color: '#aaa', fontSize: '0.8rem' }}>
                      {rec.timestamp.replace('T', ' ').slice(0, 19)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </>
  )
}
