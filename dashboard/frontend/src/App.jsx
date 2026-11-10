import React, { useState, useEffect } from 'react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts'
import { 
  Flame, BatteryCharging, Wind, Cpu, ShieldAlert, CheckCircle2, RefreshCw, Zap
} from 'lucide-react'

export default function App() {
  const [telemetry, setTelemetry] = useState([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchTelemetry = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/telemetry')
      const data = await res.json()
      setTelemetry(data)
      setLoading(false)
    } catch (err) {
      console.warn("Backend not running or offline, using fallback data:", err)
      setLoading(false)
    }
  }

  const triggerDemoSpike = async () => {
    try {
      await fetch('http://localhost:8000/api/simulate_spike', { method: 'POST' })
      fetchTelemetry()
    } catch (err) {
      console.error("Spike trigger failed", err)
    }
  }

  useEffect(() => {
    fetchTelemetry()
    if (!autoRefresh) return
    const interval = setInterval(fetchTelemetry, 3000)
    return () => clearInterval(interval)
  }, [autoRefresh])

  const latest = telemetry.length > 0 ? telemetry[telemetry.length - 1] : {
    device_id: 'm5stamp-s3-edge-01',
    temperature_c: 24.5,
    gas_resistance_kohm: 45.2,
    battery_voltage: 3.28,
    battery_soc_pct: 95.0,
    fire_alert: false,
    rl_action: 'NORMAL_CYCLE'
  }

  const chartData = telemetry.map(pt => ({
    time: new Date(pt.received_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    temperature: pt.temperature_c,
    gas_kohm: pt.gas_resistance_kohm,
    soc: pt.battery_soc_pct,
    action: pt.rl_action
  }))

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8">
      {/* Header */}
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600/20 rounded-xl border border-blue-500/30">
              <Cpu className="w-7 h-7 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                RL Edge AI Telemetry Dashboard
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  M5Stamp ESP32-S3
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Reinforcement Learning-driven adaptive heating & Wi-Fi power conservation
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={triggerDemoSpike}
            className="flex items-center gap-2 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white font-medium px-4 py-2 rounded-lg text-sm shadow-lg shadow-red-500/20 transition-all active:scale-95"
          >
            <Flame className="w-4 h-4" />
            Simulate Fire Hazard
          </button>

          <button 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border font-medium transition-all ${
              autoRefresh 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-slate-800 border-slate-700 text-slate-300'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Live Polling' : 'Paused'}
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      <main className="max-w-7xl mx-auto mt-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Temperature */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Temperature</span>
              <Flame className={`w-5 h-5 ${latest.temperature_c > 50 ? 'text-red-500 animate-pulse' : 'text-orange-400'}`} />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{latest.temperature_c.toFixed(1)}</span>
              <span className="text-lg text-slate-400">°C</span>
            </div>
            <div className="mt-2 text-xs">
              {latest.temperature_c > 50 ? (
                <span className="text-red-400 font-semibold flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5" /> Thermal Hazard Level!
                </span>
              ) : (
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Normal Ambient Range
                </span>
              )}
            </div>
          </div>

          {/* Gas VOC Resistance */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Gas Resistance</span>
              <Wind className="w-5 h-5 text-blue-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{latest.gas_resistance_kohm.toFixed(1)}</span>
              <span className="text-lg text-slate-400">kΩ</span>
            </div>
            <div className="mt-2 text-xs">
              {latest.gas_resistance_kohm < 12 ? (
                <span className="text-red-400 font-semibold flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5" /> High Smoke / VOC Spike!
                </span>
              ) : (
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Clean Baseline Air
                </span>
              )}
            </div>
          </div>

          {/* LiFePO4 Battery */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">3.2V LiFePO4 Cell</span>
              <BatteryCharging className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{latest.battery_soc_pct.toFixed(0)}</span>
              <span className="text-lg text-slate-400">%</span>
              <span className="text-xs text-slate-500 ml-1">({latest.battery_voltage.toFixed(2)}V)</span>
            </div>
            <div className="mt-2 text-xs text-emerald-400 font-medium">
              Healthy Chemistry (Flat Discharge)
            </div>
          </div>

          {/* RL Policy Action */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">RL Agent Action</span>
              <Zap className="w-5 h-5 text-yellow-400" />
            </div>
            <div className="text-xl font-bold truncate text-white">
              {latest.rl_action}
            </div>
            <div className="mt-2 text-xs">
              {latest.rl_action === 'EMERGENCY_ALERT' ? (
                <span className="text-red-400 font-bold uppercase tracking-wide">
                  Wi-Fi Radio Engaged (576 mJ)
                </span>
              ) : latest.rl_action === 'DEEP_SLEEP_LONG' ? (
                <span className="text-indigo-400 font-medium">
                  Deep Sleep 600s (~15 µA)
                </span>
              ) : (
                <span className="text-blue-400 font-medium">
                  Pulsed Micro-Heater (1.2 mJ)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Live Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Temperature & Gas Trend */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
            <h2 className="text-base font-bold text-white mb-4 flex items-center justify-between">
              <span>Environmental Hazard Dynamics</span>
              <span className="text-xs font-normal text-slate-400">BME680 Sensor Stream</span>
            </h2>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="left" stroke="#f97316" fontSize={11} domain={[15, 80]} />
                  <YAxis yAxisId="right" orientation="right" stroke="#38bdf8" fontSize={11} domain={[0, 60]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                  />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="temperature" name="Temp (°C)" stroke="#f97316" strokeWidth={2.5} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="gas_kohm" name="Gas Resistance (kΩ)" stroke="#38bdf8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Battery Degradation & SoC Trend */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
            <h2 className="text-base font-bold text-white mb-4 flex items-center justify-between">
              <span>Battery Discharge & Energy Preservation</span>
              <span className="text-xs font-normal text-slate-400">INA219 Coulomb Counting</span>
            </h2>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#10b981" fontSize={11} domain={[85, 100]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="soc" name="Battery SoC (%)" stroke="#10b981" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Audit Log Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-white mb-4">
            Recent RL Decision Audit Stream
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/50 text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Temp</th>
                  <th className="py-3 px-4">Gas Resistance</th>
                  <th className="py-3 px-4">Battery Voltage</th>
                  <th className="py-3 px-4">RL Policy Decision</th>
                  <th className="py-3 px-4">Fire Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {telemetry.slice(-8).reverse().map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {new Date(row.received_at * 1000).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">
                      {row.temperature_c.toFixed(1)} °C
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {row.gas_resistance_kohm.toFixed(1)} kΩ
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {row.battery_voltage.toFixed(3)} V
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold ${
                        row.rl_action === 'EMERGENCY_ALERT' 
                          ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                          : row.rl_action === 'ELEVATED_SCAN'
                          ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                          : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      }`}>
                        {row.rl_action}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {row.fire_alert ? (
                        <span className="text-red-400 font-bold flex items-center gap-1.5">
                          <Flame className="w-4 h-4 animate-bounce" /> HAZARD ACTIVE
                        </span>
                      ) : (
                        <span className="text-emerald-400 text-xs font-medium">
                          Normal Baseline
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}
