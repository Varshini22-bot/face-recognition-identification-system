import { useState, useEffect, useCallback } from 'react'

const API = '/api'

function StatCard({ label, value, sub, color = '' }) {
  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className={`card-value ${color}`}>{value ?? '–'}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  )
}

function SimBar({ value }) {
  return (
    <div className="sim-bar-wrap">
      <div className="sim-bar">
        <div className="sim-bar-fill" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span>{(value * 100).toFixed(1)}%</span>
    </div>
  )
}

export default function Dashboard({ onApiStatus }) {
  const [stats, setStats]       = useState(null)
  const [records, setRecords]   = useState([])
  const [inference, setInference] = useState(false)
  const [loading, setLoading]   = useState(true)

  const fetchAll = useCallback(async () => {
    try {
      const [h, s, r] = await Promise.all([
        fetch(`${API}/health`).then(r => r.json()),
        fetch(`${API}/attendance/stats`).then(r => r.json()),
        fetch(`${API}/attendance?limit=20`).then(r => r.json()),
      ])
      onApiStatus?.(true)
      setInference(h.inference)
      setStats(s)
      setRecords(r)
    } catch {
      onApiStatus?.(false)
    } finally {
      setLoading(false)
    }
  }, [onApiStatus])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 5_000)
    return () => clearInterval(id)
  }, [fetchAll])

  const toggleInference = async () => {
    const ep = inference ? 'stop' : 'start'
    await fetch(`${API}/inference/${ep}`, { method: 'POST' })
    setInference(!inference)
  }

  return (
    <>
      <div className="page-title">Dashboard</div>
      <div className="page-subtitle">Tự động cập nhật mỗi 5 giây</div>

      {loading ? <div className="spinner" /> : (
        <>
          {/* Stat cards */}
          <div className="cards">
            <StatCard
              label="Attendance Today"
              value={stats?.today}
              sub={`Total: ${stats?.total}`}
              color="blue"
            />
            <StatCard
              label="Unique People"
              value={stats?.unique_today}
              color="green"
            />
            <StatCard
              label="Unknown Today"
              value={stats?.unknown_today}
              color="yellow"
            />
            <StatCard
              label="Inference Status"
              value={inference ? 'ON' : 'OFF'}
              color={inference ? 'green' : 'red'}
            />
          </div>

          {/* Inference toggle */}
          <div className="inference-bar">
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>Inference Engine</div>
              <p>Khi bật, mỗi khung hình camera sẽ được nhận dạng khuôn mặt.</p>
            </div>
            <span className={`inference-status ${inference ? 'on' : 'off'}`}>
              {inference ? '● Running' : '○ Stopped'}
            </span>
            <button
              className={`btn ${inference ? 'danger' : 'success'}`}
              onClick={toggleInference}
            >
              {inference ? '⛔ Stop Inference' : '▶ Start Inference'}
            </button>
          </div>

          {/* Recent attendance */}
          <div className="section-title">Recent Attendance</div>
          <div className="table-wrap">
            {records.length === 0 ? (
              <div className="empty">
                <div className="empty-icon">📋</div>
                <div>No attendance records yet</div>
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Photo</th>
                    <th>Name</th>
                    <th>Similarity</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map(rec => (
                    <tr key={rec.id}>
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
                      <td><SimBar value={rec.similarity} /></td>
                      <td style={{ color: '#aaa', fontSize: '0.8rem' }}>
                        {rec.timestamp.replace('T', ' ').slice(0, 19)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </>
  )
}
