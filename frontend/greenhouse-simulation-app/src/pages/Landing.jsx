function Landing() {
  return (
    <div className="main">
      <h1>IPRO Solar Greenhouse - Simulator</h1>

      <h2>Our Goal</h2>
      <p>
        Solar Greenhouse Simulator <br />
        This program is used to simulate and analyze the internal conditions of a solar greenhouse based on real-world weather data for any location and time period, helping greenhouse operators understand how their structure performs in their local climate.

      </p>

      <h2>Guide</h2>
      <p>
        How to Use
        <br />
        Head over to the Simulator page and fill in the following:
        <br />
        1. City — Enter the name of any city (e.g. "Chicago", "London")
        <br />
        2. Start Date — The date you want the simulation to begin
        <br />
        3. End Date — The date you want the simulation to end
        <br />
        Then hit Analyze Temperature and the simulator will generate internal vs. external greenhouse temperature data for that period, along with statistics and a graph.
        <br />
        💡 Tip: Use the preset buttons (Last 24h, Last 7 days, Last 30 days) to quickly fill in the date range.
      </p>

      <h2>Under the Hood</h2>
      <p>
        TODO UNDER THE HOOD CONTENT
      </p>
    </div>
  )
}

export default Landing