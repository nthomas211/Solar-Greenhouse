function Landing() {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f0fdf4", padding: "32px", fontFamily: "Segoe UI, sans-serif" }}>

      {/* Header */}
      <div style={{
        backgroundColor: "#0d9488",
        borderRadius: "16px",
        padding: "80px 80px",
        marginBottom: "32px",
        boxShadow: "0 4px 20px rgba(13,148,136,0.3)"
      }}>
        <h1 style={{ fontSize: "56px", fontWeight: "800", color: "#ffffff", margin: "0 0 16px 0" }}>
          IPRO Solar Greenhouse — Simulator
        </h1>
        <p style={{ color: "#99f6e4", fontSize: "22px", margin: 0 }}>
          Powered by real-world weather data
        </p>
      </div>

      {/* Our Goal */}
      <div style={{
        backgroundColor: "#ffffff",
        border: "1px solid #99f6e4",
        borderRadius: "14px",
        padding: "60px 80px",
        marginBottom: "28px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.05)"
      }}>
        <h2 style={{ fontSize: "32px", fontWeight: "700", color: "#0d9488", marginTop: 0, marginBottom: "20px" }}>
          🎯 Our Goal
        </h2>
        <p style={{ color: "#374151", lineHeight: "1.9", margin: 0, fontSize: "20px" }}>
          Simulate and analyze the internal conditions of a solar greenhouse based
          on real-world weather data for any location and time period, helping
          greenhouse operators understand how their structure performs in their
          local climate.
        </p>
      </div>

      {/* Site Guide */}
      <div style={{
        backgroundColor: "#ffffff",
        border: "1px solid #99f6e4",
        borderRadius: "14px",
        padding: "60px 80px",
        marginBottom: "28px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.05)"
      }}>
        <h2 style={{ fontSize: "32px", fontWeight: "700", color: "#0d9488", marginTop: 0, marginBottom: "20px" }}>
          🗺️ Site Guide
        </h2>
        <p style={{ color: "#374151", marginBottom: "24px", fontSize: "20px" }}>
          Head over to the Simulator page and fill in the following:
        </p>

        {[
          { label: "City", desc: 'Enter the name of any city (e.g. "Chicago", "London")' },
          { label: "Start Date", desc: "The date you want the simulation to begin" },
          { label: "End Date", desc: "The date you want the simulation to end" },
        ].map((step, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "flex-start", gap: "22px",
            marginBottom: "20px"
          }}>
            <div style={{
              minWidth: "42px", height: "42px", borderRadius: "50%",
              backgroundColor: "#0d9488", color: "#fff",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "18px", fontWeight: "700"
            }}>
              {i + 1}
            </div>
            <p style={{ margin: 0, color: "#374151", lineHeight: "1.7", fontSize: "20px" }}>
              <strong>{step.label}</strong> — {step.desc}
            </p>
          </div>
        ))}

        <p style={{ color: "#374151", marginTop: "24px", marginBottom: "20px", fontSize: "20px" }}>
          Then hit{" "}
          <span style={{ fontWeight: "700", color: "#0d9488" }}>Analyze Temperature</span>
          {" "}to generate your results.
        </p>

        <div style={{
          backgroundColor: "#f0fdf4",
          border: "1px solid #6ee7b7",
          borderRadius: "10px",
          padding: "20px 28px",
          fontSize: "18px",
          color: "#374151",
          lineHeight: "1.7"
        }}>
          💡 <strong>Tip:</strong> Use the preset buttons (<em>Last 24h</em>, <em>Last 7 days</em>, <em>Last 30 days</em>) to quickly fill in the date range.
        </div>
      </div>

      {/* Under the Hood */}
      <div style={{
        backgroundColor: "#ffffff",
        border: "1px solid #99f6e4",
        borderRadius: "14px",
        padding: "60px 80px",
        marginBottom: "28px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.05)"
      }}>
        <h2 style={{ fontSize: "32px", fontWeight: "700", color: "#0d9488", marginTop: 0, marginBottom: "20px" }}>
          ⚙️ Under the Hood
        </h2>
        <p style={{ color: "#9ca3af", fontStyle: "italic", margin: 0, fontSize: "20px" }}>
          TODO — technical content coming soon.
        </p>
      </div>

    </div>
  );
}

export default Landing;