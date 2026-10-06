import { useState } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Attendance from './components/Attendance'
import Unknowns from './components/Unknowns'
import Settings from './components/Settings'

const NAV = [
  { path: '/',           icon: '🏠', label: 'Dashboard' },
  { path: '/attendance', icon: '✅', label: 'Attendance' },
  { path: '/unknowns',   icon: '👤', label: 'Unknowns' },
  { path: '/settings',   icon: '⚙️',  label: 'Settings' },
]

function Sidebar({ apiOk }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h2>Face Rec ID</h2>
        <p>AIO2025 Dashboard</p>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ path, icon, label }) => (
          <div
            key={path}
            className={`nav-item${pathname === path ? ' active' : ''}`}
            onClick={() => navigate(path)}
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className={`dot ${apiOk ? 'green' : 'red'}`} />
        {apiOk ? 'API Connected' : 'API Offline'}
      </div>
    </aside>
  )
}

export default function App() {
  const [apiOk, setApiOk] = useState(true)

  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar apiOk={apiOk} />
        <main className="main">
          <Routes>
            <Route path="/"           element={<Dashboard onApiStatus={setApiOk} />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/unknowns"   element={<Unknowns />} />
            <Route path="/settings"   element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
