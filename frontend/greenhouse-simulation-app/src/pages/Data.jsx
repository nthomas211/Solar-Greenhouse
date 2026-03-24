import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import './Data.css'

export default function Data() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingRun, setLoadingRun] = useState(false)
  const [error, setError] = useState(null)

  // Fetch history list on mount
  useEffect(() => {
    fetch('http://localhost:8000/history')
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') setRuns(data.runs)
        else setError('Failed to load history.')
      })
      .catch(() => setError('Could not reach the backend.'))
      .finally(() => setLoadingList(false))
  }, [])

  const handleSelect = async (run) => {
    setLoadingRun(true)
    setSelectedRun(null)
    try {
      const res = await fetch(`http://localhost:8000/history/${run.id}`)
      const data = await res.json()
      if (data.status === 'ok') setSelectedRun(data.run)
    } catch {
      setError('Failed to load run.')
    } finally {
      setLoadingRun(false)
    }
  }

  const formatDate = (str) => {
    if (!str) return '—'
    return new Date(str).toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  }

  return (
    <div className="data-page">

      {/* Hero */}
      <div className="data-hero">
        <h1 className="data-hero-title">Simulation History</h1>
        <p className="data-hero-sub">Browse past runs and inspect their results.</p>
      </div>

      {/* Workspace */}
      <div className="data-workspace">

        {/* LEFT: Run list */}
        <div className="data-card data-list-panel">
          <h2 className="data-card-heading">Past Runs</h2>

          {loadingList && <p className="data-status">Loading…</p>}
          {error && <p className="data-status data-error">{error}</p>}
          {!loadingList && !error && runs.length === 0 && (
            <p className="data-status">No simulations yet. Run one from the Simulator page.</p>
          )}

          <div className="data-run-list">
            {runs.map(run => (
              <button
                key={run.id}
                className={`data-run-item${selectedRun?.doc_id === run.id ? ' active' : ''}`}
                onClick={() => handleSelect(run)}
              >
                <div className="run-item-header">
                  <span className="run-name">{run.name || 'Unnamed Run'}</span>
                  <span className="run-date-badge">{run.start_date}</span>
                </div>
                <div className="run-item-meta">
                  <span className="run-meta-row">
                    <span className="run-meta-label">Run at</span>
                    <span className="run-meta-value">{formatDate(run.run_at)}</span>
                  </span>
                  <span className="run-meta-row">
                    <span className="run-meta-label">Location</span>
                    <span className="run-meta-value">
                      {run.location?.lat?.toFixed(4)}, {run.location?.lon?.toFixed(4)}
                    </span>
                  </span>
                  <span className="run-meta-row">
                    <span className="run-meta-label">Start date</span>
                    <span className="run-meta-value">{run.start_date}</span>
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* RIGHT: Chart panel */}
        <div className="data-card data-chart-panel">
          <h2 className="data-card-heading">Results</h2>

          {loadingRun && (
            <div className="data-placeholder">
              <span className="data-placeholder-icon">⏳</span>
              <p className="data-placeholder-label">Loading run…</p>
            </div>
          )}

          {!loadingRun && !selectedRun && (
            <div className="data-placeholder">
              <span className="data-placeholder-icon">👈</span>
              <p className="data-placeholder-label">Select a run from the list to view its results.</p>
            </div>
          )}

          {!loadingRun && selectedRun && (
            <div className="data-chart-content">
              <div className="data-run-summary">
                <div className="summary-pill">📛 {selectedRun.name}</div>
                <div className="summary-pill">📅 {selectedRun.start_date} → {selectedRun.end_date}</div>
                <div className="summary-pill">📍 {selectedRun.location?.lat?.toFixed(4)}, {selectedRun.location?.lon?.toFixed(4)}</div>
                <div className="summary-pill">🕒 {formatDate(selectedRun.run_at)}</div>
              </div>
              <ResultsChart rows={selectedRun.rows} />
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

function ResultsChart({ rows }) {
  const data = rows.map(r => ({
    time: r.datetime.slice(11, 16),
    date: r.datetime.slice(5, 10),
    Tin: +r.Tin.toFixed(2),
    Tout: +r.Tout.toFixed(2),
    T_mass: +r.T_mass.toFixed(2),
    Q_heater: +r.Q_heater.toFixed(0),
  }))

  const tickFormatter = (_, i) => i % 12 === 0 ? data[i]?.date ?? '' : ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

      <div>
        <p className="chart-label">Temperature Over Time (°C)</p>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" tickFormatter={tickFormatter} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit="°C" />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: '1px solid #d1fae5' }}
              formatter={(v, name) => [`${v}°C`, name]}
            />
            <Legend />
            <Line type="monotone" dataKey="Tin"    stroke="#0d9488" strokeWidth={2} dot={false} name="Inside Air" />
            <Line type="monotone" dataKey="Tout"   stroke="#6b7280" strokeWidth={1.5} dot={false} name="Outside" strokeDasharray="4 2" />
            <Line type="monotone" dataKey="T_mass" stroke="#6ee7b7" strokeWidth={1.5} dot={false} name="Thermal Mass" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <p className="chart-label">Heater Power (W)</p>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" tickFormatter={tickFormatter} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit="W" />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: '1px solid #d1fae5' }}
              formatter={(v) => [`${v}W`, 'Heater']}
            />
            <Line type="monotone" dataKey="Q_heater" stroke="#f59e0b" strokeWidth={2} dot={false} name="Heater" />
          </LineChart>
        </ResponsiveContainer>
      </div>

    </div>
  )
}
