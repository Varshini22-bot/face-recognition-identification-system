import { useState, useEffect } from 'react'

const API = '/api'

export default function Settings() {
  const [identities, setIdentities] = useState([])
  const [loading, setLoading]       = useState(true)
  const [enrollName, setEnrollName] = useState('')
  const [enrollFile, setEnrollFile] = useState(null)
  const [msg, setMsg]               = useState(null)   // { type: 'success'|'error', text }
  const [enrolling, setEnrolling]   = useState(false)

  const loadIdentities = async () => {
    setLoading(true)
    try {
      const data = await fetch(`${API}/identities`).then(r => r.json())
      setIdentities(data)
    } catch {
      setIdentities([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadIdentities() }, [])

  const handleEnroll = async (e) => {
    e.preventDefault()
    if (!enrollName.trim() || !enrollFile) {
      setMsg({ type: 'error', text: 'Please provide both name and image.' })
      return
    }
    setEnrolling(true)
    setMsg(null)
    const fd = new FormData()
    fd.append('name', enrollName.trim())
    fd.append('file', enrollFile)
    try {
      const res = await fetch(`${API}/enroll`, { method: 'POST', body: fd })
      const data = await res.json()
      if (data.success) {
        setMsg({ type: 'success', text: data.message })
        setEnrollName('')
        setEnrollFile(null)
        e.target.reset()
        await loadIdentities()
      } else {
        setMsg({ type: 'error', text: data.message })
      }
    } catch (err) {
      setMsg({ type: 'error', text: String(err) })
    } finally {
      setEnrolling(false)
    }
  }

  const handleDelete = async (name) => {
    if (!window.confirm(`Delete '${name}' from the database?`)) return
    try {
      await fetch(`${API}/identities/${encodeURIComponent(name)}`, { method: 'DELETE' })
      await loadIdentities()
    } catch (err) {
      setMsg({ type: 'error', text: String(err) })
    }
  }

  return (
    <>
      <div className="page-title">Settings</div>
      <div className="page-subtitle">Manage enrolled identities and system configuration</div>

      {/* Enroll form */}
      <div className="form-card">
        <h3>📷 Enroll New Face</h3>
        {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}
        <form onSubmit={handleEnroll}>
          <div className="form-row">
            <label className="field-label">Person Name</label>
            <input
              type="text"
              placeholder="e.g. Varshini"
              value={enrollName}
              onChange={e => setEnrollName(e.target.value)}
              required
            />
          </div>
          <div className="form-row">
            <label className="field-label">Face Image (JPG / PNG)</label>
            <input
              type="file"
              accept="image/*"
              onChange={e => setEnrollFile(e.target.files[0])}
              required
            />
          </div>
          <button className="btn primary" type="submit" disabled={enrolling}>
            {enrolling ? '⏳ Enrolling…' : '✅ Enroll'}
          </button>
        </form>
      </div>

      {/* Registered identities */}
      <div className="section-title">Registered Identities ({identities.length})</div>
      {loading ? <div className="spinner" /> : (
        identities.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">👤</div>
            <div>No identities enrolled yet</div>
          </div>
        ) : (
          <div className="id-grid">
            {identities.map(id => (
              <div key={id.name} className="id-card">
                <div className="id-avatar">👤</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="id-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {id.name}
                  </div>
                  <div className="id-count">{id.sample_count} sample{id.sample_count !== 1 ? 's' : ''}</div>
                </div>
                <button className="btn icon-btn" onClick={() => handleDelete(id.name)} title="Delete">🗑</button>
              </div>
            ))}
          </div>
        )
      )}
    </>
  )
}
