import { useState } from 'react'

export default function WeekCard({ week }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="week-card">
      <div className="week-header" onClick={() => setOpen(!open)}>
        <h3>
          <span className="week-num">{week.week}</span>
          {week.theme}
        </h3>
        <span style={{ fontSize: '1.2rem', transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'none' }}>
          ▾
        </span>
      </div>

      {open && (
        <div className="week-body">
          {(week.topics || []).map((topic, idx) => (
            <div className="topic-item" key={idx}>
              <div className="topic-name">
                📘 {topic.name}
                <span className="topic-hours">({topic.estimated_hours}h)</span>
              </div>

              {topic.learning_objectives?.length > 0 && (
                <ul className="objectives">
                  {topic.learning_objectives.map((obj, i) => (
                    <li key={i}>{obj}</li>
                  ))}
                </ul>
              )}

              {topic.resources?.length > 0 && (
                <div className="resources">
                  📚 {topic.resources.join(' · ')}
                </div>
              )}
            </div>
          ))}

          {week.milestone && (
            <div className="milestone">🏁 {week.milestone}</div>
          )}
        </div>
      )}
    </div>
  )
}
