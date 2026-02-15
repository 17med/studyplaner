export default function AgentLog({ log }) {
  if (!log || log.length === 0) return null

  return (
    <div className="card">
      <h2>🤖 Agent Collaboration Log</h2>
      <div className="agent-log">
        {log.map((entry, idx) => (
          <div className="log-entry" key={idx}>
            <span className="log-round">Round {entry.round}</span>
            <span className="log-agent">{entry.agent}</span>
            <span className="log-summary">{entry.summary}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
