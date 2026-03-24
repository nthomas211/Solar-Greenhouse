import { useState } from 'react'
import './Simulation.css'

const TABS = [
  { id: 'structure', label: '🏗️ Structure' },
  { id: 'thermal',   label: '🌡️ Thermal'   },
  { id: 'initial',   label: '🔬 Initial'   },
]

const FIELDS = {
  structure: [
    {
      legend: 'Physical Dimensions',
      fields: [
        { label: 'Glass Area',           name: 'glassArea',           unit: 'm²',    min: 0,   max: 200,  step: 0.1  },
        { label: 'Floor Area',           name: 'floorArea',           unit: 'm²',    min: 0,   max: 500,  step: 0.1  },
        { label: 'Volume',               name: 'volume',              unit: 'm³',    min: 0,   max: 5000, step: 1    },
        { label: 'Glass Transmissivity', name: 'glassTransmissivity', unit: '0–1',   min: 0,   max: 1,    step: 0.01 },
      ],
    },
    {
      legend: 'Heat Loss',
      fields: [
        { label: 'U-Value Day',   name: 'uValueDay',   unit: 'W/m²K', min: 0, max: 10, step: 0.01 },
        { label: 'U-Value Night', name: 'uValueNight', unit: 'W/m²K', min: 0, max: 10, step: 0.01 },
        { label: 'Air Changes / Hour (ACH)', name: 'ach', unit: 'ACH', min: 0, max: 10, step: 0.1  },
      ],
    },
  ],
  thermal: [
    {
      legend: 'Thermal Mass',
      fields: [
        { label: 'Mass',                   name: 'mass',             unit: 'kg',    min: 0, max: 20000, step: 1   },
        { label: 'Surface Area',           name: 'surfaceArea',      unit: 'm²',    min: 0, max: 2000,  step: 0.1 },
        { label: 'Heat Transfer Coeff',    name: 'heatTransferCoeff',unit: 'W/m²K', min: 0, max: 100,   step: 0.1 },
      ],
    },
    {
      legend: 'Solar & Heating',
      fields: [
        { label: 'Solar to Air Fraction',  name: 'solarToAirFraction', unit: '0–1', min: 0,   max: 1,     step: 0.01 },
        { label: 'Heater Max Power',       name: 'heaterMaxPower',     unit: 'W',   min: 0,   max: 20000, step: 10   },
        { label: 'SetPoint Temperature',   name: 'setPoint',           unit: '°C',  min: -10, max: 40,    step: 0.1  },
      ],
    },
  ],
  initial: [
    {
      legend: 'Initial Conditions',
      fields: [
        { label: 'Air Temperature',  name: 'airTemp',  unit: '°C', min: -30, max: 60, step: 0.1 },
        { label: 'Mass Temperature', name: 'massTemp', unit: '°C', min: -30, max: 60, step: 0.1 },
        { label: 'Soil Temperature', name: 'soilTemp', unit: '°C', min: -30, max: 60, step: 0.1 },
      ],
    },
  ],
}

export default function Simulation() {
  const [activeTab, setActiveTab] = useState('structure')
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState({
    glassArea: 50,
    floorArea: 100,
    volume: 300,
    glassTransmissivity: 0.85,
    uValueDay: 2.5,
    uValueNight: 3.0,
    ach: 1.0,
    mass: 5000,
    surfaceArea: 200,
    heatTransferCoeff: 5,
    solarToAirFraction: 0.7,
    heaterMaxPower: 5000,
    setPoint: 20,
    airTemp: 15,
    massTemp: 18,
    soilTemp: 12,
  })

  const update = (key, value) =>
    setConfig(prev => ({ ...prev, [key]: parseFloat(value) }))

  const handleSimulate = async () => {
    setLoading(true)
    const payload = {
      name: 'run_1',
      location: { lat: 41.8781, lon: -87.6298 },
      start_date: '2026-02-10',
      end_date: '2026-02-14',
      parameters: {
        A_glass: config.glassArea,
        A_floor: config.floorArea,
        V: config.volume,
        tau_glass: config.glassTransmissivity,
        U_day: config.uValueDay,
        U_night: config.uValueNight,
        ACH: config.ach,
        thermal_mass_kg: config.mass,
        A_mass: config.surfaceArea,
        h_am: config.heatTransferCoeff,
        fraction_solar_to_air: config.solarToAirFraction,
        heater_max_w: config.heaterMaxPower,
        setpoint: config.setPoint,
        T_init: config.airTemp,
        T_mass_init: config.massTemp,
        T_soil_init: config.soilTemp,
      },
    }
    try {
      const res = await fetch('http://localhost:8000/run-simulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      console.log(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="sim-page">

      {/* ── Page header ── */}
      <div className="sim-hero">
        <h1 className="sim-hero-title">Greenhouse Simulator</h1>
        <p className="sim-hero-sub">Configure your structure, run the model, and explore the results.</p>
      </div>

      {/* ── Two-column workspace ── */}
      <div className="sim-workspace">

        {/* ── LEFT: Inputs ── */}
        <div className="sim-card sim-inputs">
          <h2 className="sim-card-heading">Parameters</h2>

          {/* Tabs */}
          <div className="sim-tabs">
            {TABS.map(t => (
              <button
                key={t.id}
                className={`sim-tab${activeTab === t.id ? ' active' : ''}`}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Fieldsets for active tab */}
          <div className="sim-fields">
            {FIELDS[activeTab].map(group => (
              <fieldset key={group.legend} className="sim-fieldset">
                <legend className="sim-legend">{group.legend}</legend>
                {group.fields.map(f => (
                  <FieldRow key={f.name} field={f} value={config[f.name]} onChange={update} />
                ))}
              </fieldset>
            ))}
          </div>

          {/* Simulate button */}
          <div className="sim-actions">
            <button
              className={`sim-btn${loading ? ' loading' : ''}`}
              onClick={handleSimulate}
              disabled={loading}
            >
              {loading ? 'Running…' : '▶ Run Simulation'}
            </button>
          </div>
        </div>

        {/* ── RIGHT: Output placeholder ── */}
        <div className="sim-card sim-output">
          <h2 className="sim-card-heading">Results</h2>
          <div className="sim-output-placeholder">
            <span className="sim-output-icon">📊</span>
            <p className="sim-output-label">
              Results will appear here after you run the simulation.
            </p>
            <p className="sim-output-hint">
              Configure your parameters on the left, then click <strong>Run Simulation</strong>.
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}

/* ── Field row: label + slider + number input ── */
function FieldRow({ field, value, onChange }) {
  const { label, name, unit, min, max, step } = field
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div className="field-row">
      <div className="field-label-row">
        <span className="field-label">{label}</span>
        <span className="field-unit">{unit}</span>
      </div>
      <div className="field-controls">
        <div className="slider-track">
          <div className="slider-fill" style={{ width: `${pct}%` }} />
          <input
            type="range"
            min={min} max={max} step={step}
            value={value}
            onChange={e => onChange(name, e.target.value)}
            className="field-slider"
            style={{ '--pct': `${((value - min) / (max - min)) * 100}%` }}
          />
        </div>
        <input
          type="number"
          min={min} max={max} step={step}
          value={value}
          onChange={e => onChange(name, e.target.value)}
          className="field-number"
        />
      </div>
    </div>
  )
}
