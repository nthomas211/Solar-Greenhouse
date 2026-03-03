function Landing() {
  return (
    <div className="min-h-screen bg-white px-6 py-12">
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <div className="bg-teal-500 rounded-2xl px-8 py-10 mb-10 shadow-md">
          <h1 className="text-4xl font-bold text-white mb-2">
            IPRO Solar Greenhouse — Simulator
          </h1>
          <p className="text-teal-100 text-sm">
            Powered by real-world weather data
          </p>
        </div>

        {/* Our Goal */}
        <section className="mb-8 bg-teal-50 border border-teal-100 rounded-xl p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-black mb-3">Our Goal</h2>
          <p className="text-black leading-relaxed">
            Simulate and analyze the internal conditions of a solar greenhouse based
            on real-world weather data for any location and time period, helping
            greenhouse operators understand how their structure performs in their
            local climate.
          </p>
        </section>

        {/* Site Guide */}
        <section className="mb-8 bg-white border border-teal-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-black mb-3">Site Guide</h2>
          <p className="text-black mb-3">
            Head over to the Simulator page and fill in the following:
          </p>
          <ol className="list-decimal list-inside space-y-2 text-black">
            <li><span className="font-medium">City</span> — Enter the name of any city (e.g. "Chicago", "London")</li>
            <li><span className="font-medium">Start Date</span> — The date you want the simulation to begin</li>
            <li><span className="font-medium">End Date</span> — The date you want the simulation to end</li>
          </ol>
          <p className="mt-3 text-black">
            Then hit <span className="font-medium text-teal-600">Analyze Temperature</span> to generate your results.
          </p>
          <div className="mt-4 bg-teal-50 border border-teal-200 rounded-lg p-3 text-sm text-black">
            💡 Tip: Use the preset buttons (Last 24h, Last 7 days, Last 30 days) to quickly fill in the date range.
          </div>
        </section>

        {/* Under the Hood */}
        <section className="mb-8 bg-teal-50 border border-teal-100 rounded-xl p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-black mb-3">Under the Hood</h2>
          <p className="text-black leading-relaxed">
            TODO UNDER THE HOOD CONTENT
          </p>
        </section>

      </div>
    </div>
  )
}

export default Landing