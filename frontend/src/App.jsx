import { useState } from 'react'
import PlanForm from './components/PlanForm'
import PlanResult from './components/PlanResult'
import AgentLog from './components/AgentLog'

const AGENT_STEPS = [
  '🧠 Curriculum Agent is designing your roadmap…',
  '⏱️ Time Estimation Agent is validating feasibility…',
  '🔍 Critic Agent is reviewing the plan…',
  '🔄 Agents are collaborating on revisions…',
]

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [agentStep, setAgentStep] = useState(0)

  const handleGenerate = async (formData) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setAgentStep(0)

    // Simulate agent step progression while waiting
    const interval = setInterval(() => {
      setAgentStep((prev) => (prev + 1) % AGENT_STEPS.length)
    }, 4000)

    try {
      const resp = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      const data = await resp.json()

      if (!resp.ok || !data.success) {
        throw new Error(data.error || 'Failed to generate plan')
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      clearInterval(interval)
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🎓 AI Study Planner</h1>
        <p>Multi-agent system powered by NVIDIA NIM · GPT-OSS-120B</p>
      </header>

      <PlanForm onSubmit={handleGenerate} disabled={loading} />

      {loading && (
        <div className="card loading">
          <div className="spinner" />
          <p>Agents are collaborating to build your study plan…</p>
          <p className="agent-step">{AGENT_STEPS[agentStep]}</p>
        </div>
      )}

      {error && (
        <div className="card">
          <div className="error">⚠️ {error}</div>
        </div>
      )}

      {result && (
        <>
          <PlanResult
            plan={result.plan}
            review={result.review}
            timeReport={result.time_report}
            approved={result.approved}
            rounds={result.rounds}
          />
          <AgentLog log={result.log} />
        </>
      )}
    </div>
  )
}
