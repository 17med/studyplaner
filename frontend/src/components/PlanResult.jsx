import { useState } from 'react'
import WeekCard from './WeekCard'

export default function PlanResult({ plan, review, timeReport, approved, rounds }) {
  if (!plan || !plan.topic) {
    return (
      <div className="card">
        <p style={{ color: 'var(--text-muted)' }}>
          No structured plan could be parsed from the AI response. Try again.
        </p>
      </div>
    )
  }

  const qualityScore = review?.quality_score ?? '?'
  const timeScore = timeReport?.overall_score ?? '?'
  const feasible = timeReport?.feasible

  return (
    <>
      {/* ── Plan overview ──────────────────────────────────────── */}
      <div className="card">
        <div className="result-header">
          <h2>📖 {plan.topic}</h2>
          <span className={`badge ${approved ? 'badge-success' : 'badge-warning'}`}>
            {approved ? '✅ Approved' : `⚠️ Best effort (${rounds} rounds)`}
          </span>
        </div>

        <div className="meta-row">
          <div className="meta-item">
            <span className="label">Duration:</span>
            <span className="value">{plan.total_weeks} weeks</span>
          </div>
          <div className="meta-item">
            <span className="label">Hours/week:</span>
            <span className="value">{plan.hours_per_week}h</span>
          </div>
          <div className="meta-item">
            <span className="label">Level:</span>
            <span className="value">{plan.difficulty_level}</span>
          </div>
          {plan.prerequisites?.length > 0 && (
            <div className="meta-item">
              <span className="label">Prerequisites:</span>
              <span className="value">{plan.prerequisites.join(', ')}</span>
            </div>
          )}
        </div>

        {/* Scores */}
        <div className="scores">
          <div className="score-box">
            <div className="number" style={{ color: qualityScore >= 7 ? 'var(--success)' : 'var(--warning)' }}>
              {qualityScore}<span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>/10</span>
            </div>
            <div className="score-label">Quality</div>
          </div>
          <div className="score-box">
            <div className="number" style={{ color: timeScore >= 7 ? 'var(--success)' : 'var(--warning)' }}>
              {timeScore}<span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>/10</span>
            </div>
            <div className="score-label">Feasibility</div>
          </div>
          <div className="score-box">
            <div className="number" style={{ color: feasible ? 'var(--success)' : 'var(--danger)' }}>
              {feasible ? '✓' : '✗'}
            </div>
            <div className="score-label">Schedule OK</div>
          </div>
          <div className="score-box">
            <div className="number" style={{ color: 'var(--primary)' }}>{rounds}</div>
            <div className="score-label">Rounds</div>
          </div>
        </div>
      </div>

      {/* ── Weekly plan ────────────────────────────────────────── */}
      <div className="card">
        <h2>📅 Weekly Roadmap</h2>
        {(plan.weekly_plan || []).map((week, idx) => (
          <WeekCard key={idx} week={week} />
        ))}
        {plan.final_outcome && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--surface2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <strong>🎯 Final Outcome:</strong> {plan.final_outcome}
          </div>
        )}
      </div>

      {/* ── Critic review ──────────────────────────────────────── */}
      {review && (
        <div className="card">
          <h2>🔍 Critic Review</h2>
          {review.strengths?.length > 0 && (
            <>
              <h3 style={{ fontSize: '0.9rem', color: 'var(--success)', marginBottom: '0.4rem' }}>Strengths</h3>
              <ul className="review-list">
                {review.strengths.map((s, i) => (
                  <li key={i}><span className="icon">✅</span> {s}</li>
                ))}
              </ul>
            </>
          )}
          {review.weaknesses?.length > 0 && (
            <>
              <h3 style={{ fontSize: '0.9rem', color: 'var(--warning)', margin: '0.75rem 0 0.4rem' }}>Weaknesses</h3>
              <ul className="review-list">
                {review.weaknesses.map((w, i) => (
                  <li key={i}><span className="icon">⚠️</span> {w}</li>
                ))}
              </ul>
            </>
          )}
          {review.verdict && (
            <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.9rem' }}>
              {review.verdict}
            </p>
          )}
        </div>
      )}
    </>
  )
}
