"use client"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

import type React from "react"

import { useEffect, useState } from "react"
import TemperatureGraph from "../components/graphDisplay"
import RawDataDisplay from "../components/rawDataDisplay"
import StatsDisplay from "../components/statsDisplay"
import { AlertCircle } from "lucide-react"

// Updated interface to match the actual API response format
interface TemperatureDataPoint {
  Timestamp: string
  "Internal Temperature (°C)": number
  "External Temperature (°C)": number
  // Add any other fields that your API returns
}

const fetchTemperatureData = async (
  city: string,
  startDate: string,
  endDate: string,
  heatingPower: number,
  matToggle: boolean
): Promise<TemperatureDataPoint []> => {
  try {
    // Replace with your actual API URL
    const apiUrl = `https://${API_BASE_URL}/simulate?city=${encodeURIComponent(city)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&heating_power=${heatingPower}&mat_toggle=${matToggle}`

    console.log("Fetching data from:", apiUrl)

    const response = await fetch(apiUrl, {
      method: "GET",
      mode: "cors", // Explicitly set CORS mode
      headers: {
        Accept: "application/json",
      },
    })

    const responseText = await response.text()
    console.log("Raw response:", responseText)

    let data
    try {
      data = JSON.parse(responseText)
    } catch (e) {
      throw new Error(`Failed to parse response as JSON: ${responseText}`)
    }

    console.log("Parsed response:", data)

    if (!response.ok) {
      throw new Error(`API error: ${response.status} - ${data.message || responseText}`)
    }

    if (data.status === "success" && Array.isArray(data.data)) {
      return data.data
    } else {
      throw new Error(`Invalid response format: ${JSON.stringify(data)}`)
    }
  } catch (error) {
    console.error("Error fetching data:", error)
    throw error
  }
}

export default function TemperatureAnalysisDashboard() {
  const [city, setCity] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [heatingPower, setHeatingPower] = useState(0) // Default to 500 watts
  const [matOn, setMatOn] = useState(true) // Default to on
  const [temperatureData, setTemperatureData] = useState<TemperatureDataPoint[]>([])
  const [visibleData, setVisibleData] = useState<TemperatureDataPoint[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // When temperature data changes, update visible data
  useEffect(() => {
    setVisibleData(temperatureData)
  }, [temperatureData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate inputs
    if (!city) {
      setError("Please enter a city")
      return
    }

    if (!startDate) {
      setError("Please enter a start date")
      return
    }

    if (!endDate) {
      setError("Please enter an end date")
      return
    }

    // Validate date range
    const start = new Date(startDate)
    const end = new Date(endDate)

    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      setError("Please enter valid dates")
      return
    }

    if (end < start) {
      setError("End date must be after start date")
      return
    }

    // Calculate date difference
    const diffTime = Math.abs(end.getTime() - start.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    // Optional: Add a warning for large date ranges
    if (diffDays > 30 && !confirm(`You've selected a ${diffDays} day range. This might be slow to load. Continue?`)) {
      return
    }

    setIsLoading(true)

    try {
      let data: TemperatureDataPoint[]
      data = await fetchTemperatureData(city, startDate, endDate, heatingPower, matOn)

      console.log("Data received:", data)
      console.log(`Received ${data.length} data points spanning ${diffDays} days`)

      if (data.length === 0) {
        setError("No data returned for the selected date range")
      } else {
        setTemperatureData(data)
        setVisibleData(data) // Initialize visible data with all data
      }
    } catch (error) {
      console.error("Error fetching temperature data:", error)
      setError(`Failed to fetch temperature data: ${error instanceof Error ? error.message : "Unknown error"}`)
      setTemperatureData([])
      setVisibleData([])
    } finally {
      setIsLoading(false)
    }
  }

  // Handle visible data change from graph component
  const handleVisibleDataChange = (data: TemperatureDataPoint[]) => {
    setVisibleData(data)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* INPUT SECTION */}
      <div className="lg:col-span-1 bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">INPUT</h2>
        </div>
        <div className="p-4">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="city" className="block text-sm font-medium text-gray-700">
                City
              </label>
              <input
                id="city"
                type="text"
                placeholder="Enter city name (e.g., New York, Tokyo)"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
                Start Date
              </label>
              <input
                id="startDate"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
                End Date
              </label>
              <input
                id="endDate"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            { /*
            <div className="space-y-2">
              <label htmlFor="heatingPower" className="block text-sm font-medium text-gray-700">
                Heating Power (Watts)
              </label>
              <input
                disabled={false}
                id="heatingPower"
                type="number"
                min="0"
                step="1"
                value={heatingPower}
                onChange={(e) => setHeatingPower(Number.parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter power in watts"
              />
              <div className="text-xs text-gray-500">If no heating, set to 0</div>
            </div>
      
            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  id="matOn"
                  disabled={false}
                  type="checkbox"
                  checked={matOn}
                  onChange={(e) => setMatOn(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="matOn" className="ml-2 block text-sm text-gray-700">
                  Rolling Mat
                </label>
              </div>
            </div>
            */}
            <div className="flex flex-col space-y-2">
              <span className="text-sm text-gray-500">Date Range Presets:</span>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const today = new Date()
                    const yesterday = new Date(today)
                    yesterday.setDate(yesterday.getDate() - 1)
                    setStartDate(yesterday.toISOString().split("T")[0])
                    setEndDate(today.toISOString().split("T")[0])
                  }}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Last 24h
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const today = new Date()
                    const weekAgo = new Date(today)
                    weekAgo.setDate(weekAgo.getDate() - 7)
                    setStartDate(weekAgo.toISOString().split("T")[0])
                    setEndDate(today.toISOString().split("T")[0])
                  }}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Last 7 days
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const today = new Date()
                    const monthAgo = new Date(today)
                    monthAgo.setDate(monthAgo.getDate() - 30)
                    setStartDate(monthAgo.toISOString().split("T")[0])
                    setEndDate(today.toISOString().split("T")[0])
                  }}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Last 30 days
                </button>
              </div>
            </div>

            {error && (
              <div className="text-red-500 text-sm p-3 bg-red-50 border border-red-200 rounded flex items-start">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md shadow transition-colors duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-blue-600"
              disabled={isLoading}
            >
              {isLoading ? "Loading..." : "Analyze Temperature"}
            </button>
          </form>
        </div>
      </div>

      {/* RIGHT COLUMN - GRAPH AND RAW DATA */}
      <div className="lg:col-span-2 space-y-4">
        {/* STATISTICS SECTION */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">STATISTICS</h2>
          </div>
          <div className="p-4">
            <StatsDisplay data={visibleData} />
          </div>
        </div>

        {/* GRAPH SECTION */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">GRAPH</h2>
          </div>
          <div className="p-4">
            <TemperatureGraph data={temperatureData} onVisibleDataChange={handleVisibleDataChange} />
          </div>
        </div>

        {/* RAW DATA SECTION */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">RAW DATA</h2>
          </div>
          <div className="p-4">
            <RawDataDisplay data={temperatureData} />
          </div>
        </div>
      </div>
    </div>
  )
}
