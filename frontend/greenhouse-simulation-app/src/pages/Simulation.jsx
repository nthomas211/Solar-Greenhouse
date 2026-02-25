import { useState } from 'react'
import './Simulation.css'

function Simulation() {
  const [activeTab, setActiveTab] = useState('structure')
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

  const update = (key, value) => setConfig(prev => ({ ...prev, [key]: parseFloat(value) }))

  const Field = ({ label, name, min, max, step }) => (
    <>
      <label>{label}</label>
      <div className="cfg-row">
        <input
          type="range"
          min={min} max={max} step={step}
          value={config[name]}
          onChange={e => update(name, e.target.value)}
          className="cfg-range"
        />
        <input
          type="number"
          min={min} max={max} step={step}
          value={config[name]}
          onChange={e => update(name, e.target.value)}
          className="cfg-input-number"
        />
      </div>
    </>
  )

  return (
    <div>
      <h1>Calculation Based Simulator</h1>
      <div className="config-section" style={{border: '1px solid #ddd', padding: 12, borderRadius: 6}}>

        <div className="cfg-tabs">
          <button className={`cfg-tab-btn ${activeTab === 'structure' ? 'active' : ''}`} onClick={() => setActiveTab('structure')}>Structure</button>
          <button className={`cfg-tab-btn ${activeTab === 'thermal' ? 'active' : ''}`} onClick={() => setActiveTab('thermal')}>Thermal</button>
          <button className={`cfg-tab-btn ${activeTab === 'initial' ? 'active' : ''}`} onClick={() => setActiveTab('initial')}>Initial</button>
        </div>

        {activeTab === 'structure' && (
          <div>
            <fieldset>
              <legend className="cfg-section-title">Physical Dimensions</legend>
              <div className="cfg-grid">
                <Field label="Glass Area (m²)" name="glassArea" min={0} max={200} step={0.1} />
                <Field label="Floor Area (m²)" name="floorArea" min={0} max={500} step={0.1} />
                <Field label="Volume (m³)" name="volume" min={0} max={5000} step={1} />
                <Field label="Glass Transmissivity (0-1)" name="glassTransmissivity" min={0} max={1} step={0.01} />
              </div>
            </fieldset>
            <fieldset style={{marginTop:10}}>
              <legend className="cfg-section-title">Heat Loss</legend>
              <div className="cfg-grid">
                <Field label="U-Value Day (W/m²K)" name="uValueDay" min={0} max={10} step={0.01} />
                <Field label="U-Value Night (W/m²K)" name="uValueNight" min={0} max={10} step={0.01} />
                <Field label="Air Changes / Hour (ACH)" name="ach" min={0} max={10} step={0.1} />
              </div>
            </fieldset>
          </div>
        )}

        {activeTab === 'thermal' && (
          <div>
            <fieldset>
              <legend className="cfg-section-title">Thermal Mass</legend>
              <div className="cfg-grid">
                <Field label="Mass (kg)" name="mass" min={0} max={20000} step={1} />
                <Field label="Surface Area (m²)" name="surfaceArea" min={0} max={2000} step={0.1} />
                <Field label="Heat Transfer Coeff (W/m²K)" name="heatTransferCoeff" min={0} max={100} step={0.1} />
              </div>
            </fieldset>
            <fieldset style={{marginTop:10}}>
              <legend className="cfg-section-title">Solar & Heating</legend>
              <div className="cfg-grid">
                <Field label="Solar to Air Fraction" name="solarToAirFraction" min={0} max={1} step={0.01} />
                <Field label="Heater Max Power (W)" name="heaterMaxPower" min={0} max={20000} step={10} />
                <Field label="SetPoint Temperature (°C)" name="setPoint" min={-10} max={40} step={0.1} />
              </div>
            </fieldset>
          </div>
        )}

        {activeTab === 'initial' && (
          <div>
            <fieldset>
              <legend className="cfg-section-title">Initial Conditions</legend>
              <div className="cfg-grid">
                <Field label="Air Temperature (°C)" name="airTemp" min={-30} max={60} step={0.1} />
                <Field label="Mass Temperature (°C)" name="massTemp" min={-30} max={60} step={0.1} />
                <Field label="Soil Temperature (°C)" name="soilTemp" min={-30} max={60} step={0.1} />
              </div>
            </fieldset>
          </div>
        )}

        <div style={{display:'flex', justifyContent:'flex-end'}}>
          <button className="cfg-button" type="button" onClick={() => console.log(config)}>Simulate</button>
        </div>
      </div>
    </div>
  )
}

export default Simulation