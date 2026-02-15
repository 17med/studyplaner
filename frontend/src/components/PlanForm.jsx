import { useState } from 'react'

export default function PlanForm({ onSubmit, disabled }) {
  const [form, setForm] = useState({
    topic: '',
    skill_level: 'beginner',
    available_hours: 10,
    duration_weeks: 4,
    goals: '',
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.topic.trim()) return
    onSubmit({
      ...form,
      available_hours: Number(form.available_hours),
      duration_weeks: Number(form.duration_weeks),
    })
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>📝 Plan Configuration</h2>

      <div className="form-grid">
        <div className="form-group full">
          <label htmlFor="topic">What do you want to study?</label>
          <input
            id="topic"
            name="topic"
            type="text"
            placeholder="e.g. Machine Learning, Rust, Web Development…"
            value={form.topic}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="skill_level">Skill Level</label>
          <select
            id="skill_level"
            name="skill_level"
            value={form.skill_level}
            onChange={handleChange}
          >
            <option value="beginner">🟢 Beginner</option>
            <option value="intermediate">🟡 Intermediate</option>
            <option value="advanced">🔴 Advanced</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="available_hours">Hours per Week</label>
          <input
            id="available_hours"
            name="available_hours"
            type="number"
            min="1"
            max="80"
            value={form.available_hours}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="duration_weeks">Duration (weeks)</label>
          <input
            id="duration_weeks"
            name="duration_weeks"
            type="number"
            min="1"
            max="52"
            value={form.duration_weeks}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="goals">Specific Goals (optional)</label>
          <input
            id="goals"
            name="goals"
            type="text"
            placeholder="e.g. Build a portfolio project"
            value={form.goals}
            onChange={handleChange}
          />
        </div>
      </div>

      <button type="submit" className="btn btn-primary" disabled={disabled || !form.topic.trim()}>
        {disabled ? '⏳ Generating…' : '🚀 Generate Study Plan'}
      </button>
    </form>
  )
}
