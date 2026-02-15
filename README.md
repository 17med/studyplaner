# 🎓 Multi-Agent AI Study Planner

A multi-agent system that generates **realistic, validated study plans** through simulated collaboration between three specialised AI agents. Powered by **NVIDIA NIM API** (`openai/gpt-oss-120b`) and featuring a **React** web interface.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                 │
│                                                                      │
│   ┌─────────────────┐    ┌───────────────────┐    ┌──────────────┐  │
│   │  Curriculum      │───▶│ Time Estimation   │───▶│   Critic     │  │
│   │  Agent           │    │ Agent             │    │   Agent      │  │
│   │                  │    │                   │    │              │  │
│   │ • Learning       │    │ • Validates hours │    │ • Quality    │  │
│   │   roadmap        │    │ • Checks balance  │    │   review     │  │
│   │ • Weekly plan    │    │ • Burnout risk    │    │ • Approves   │  │
│   │ • Resources      │    │ • Feasibility     │    │   or revises │  │
│   └─────────────────┘    └───────────────────┘    └──────┬───────┘  │
│          ▲                                                │          │
│          │              Feedback Loop                      │          │
│          └────────────────────────────────────────────────┘          │
│                                                                      │
│                    ┌─────────────────────┐                           │
│                    │   NVIDIA NIM API    │                           │
│                    │  openai/gpt-oss-120b│                           │
│                    │  (OpenAI SDK)       │                           │
│                    └─────────────────────┘                           │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │                   Flask API  (/api)                          │   │
│   └──────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│   ┌──────────────────────────▼───────────────────────────────────┐   │
│   │              React Frontend (Vite)                           │   │
│   │   PlanForm → Loading → PlanResult + WeekCards + AgentLog    │   │
│   └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Role | Output |
|-------|------|--------|
| **Curriculum Agent** | Proposes a structured week-by-week learning roadmap with topics, objectives, and resources | JSON study plan |
| **Time Estimation Agent** | Validates whether the proposed schedule is feasible given available hours and skill level | Feasibility report with per-week analysis |
| **Critic Agent** | Reviews plan quality, flags issues, and either approves or requests revisions | Approval verdict with actionable feedback |

### Collaboration Flow

1. **Round 1**: Curriculum Agent generates initial plan → Time Agent validates → Critic reviews
2. **Revision**: If Critic rejects, feedback is sent back to Curriculum Agent
3. **Repeat**: Up to 3 rounds (configurable) until approved or best effort returned

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+ (for React frontend)
- NVIDIA NIM API key

### Installation

```bash
cd studyplaner

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### LLM Backend

The system uses **NVIDIA NIM API** via the OpenAI SDK with the `openai/gpt-oss-120b` model.

The API key is configured in `config.py`. To override via environment variable:

```bash
export NVIDIA_API_KEY="your-nvidia-api-key"
export NVIDIA_MODEL="openai/gpt-oss-120b"        # default
export NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1"  # default
```

## Usage

### Web Interface (Recommended)

Start both servers:

```bash
# Terminal 1 – Flask API backend
python api.py

# Terminal 2 – React dev server
cd frontend && npm run dev
```

Then open **http://localhost:5173** in your browser.

The React UI lets you:
- Configure topic, skill level, hours/week, duration, and goals
- Watch real-time agent status while generating
- View the full weekly roadmap with expandable detail cards
- See quality & feasibility scores
- Read the Critic's strengths/weaknesses analysis
- Inspect the agent collaboration log

### CLI Mode

```bash
# Interactive mode (asks questions)
python main.py

# One-liner
python main.py --topic "Machine Learning" --level beginner --hours 12 --weeks 6

# With specific goals
python main.py -t "Web Development" -l intermediate -hr 15 -w 8 -g "Build a full-stack app with React and Node.js"

# Save output to JSON
python main.py -t "Data Structures" -l beginner -hr 10 -w 4 -o plan.json

# Verbose logging (see agent prompts and raw LLM responses)
python main.py -t "Python" -v
```

### CLI Arguments

| Flag | Description | Default |
|------|-------------|---------|
| `--topic, -t` | Subject to study | _(interactive)_ |
| `--level, -l` | beginner / intermediate / advanced | beginner |
| `--hours, -hr` | Study hours available per week | 10 |
| `--weeks, -w` | Plan duration in weeks | 4 |
| `--goals, -g` | Specific learning goals | None |
| `--output, -o` | Save plan to JSON file | None |
| `--verbose, -v` | Debug logging | off |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check, returns model info |
| `POST` | `/api/generate` | Generate a study plan (JSON body) |

**POST `/api/generate`** body:
```json
{
  "topic": "Machine Learning",
  "skill_level": "beginner",
  "available_hours": 12,
  "duration_weeks": 6,
  "goals": "Build an ML project"
}
```

## Configuration

All settings are in `config.py` and can be overridden via environment variables:

```bash
export NVIDIA_API_KEY="nvapi-..."  # NVIDIA NIM API key
export NVIDIA_MODEL="openai/gpt-oss-120b"
export TEMPERATURE=0.7             # Generation temperature
export MAX_TOKENS=2048             # Max response tokens
export MAX_REVISION_ROUNDS=3       # Agent collaboration rounds
```

## Project Structure

```
studyplaner/
├── main.py                          # CLI entry-point
├── api.py                           # Flask API server
├── config.py                        # Configuration (NVIDIA API keys, params)
├── llm_provider.py                  # OpenAI SDK → NVIDIA NIM wrapper
├── orchestrator.py                  # Multi-agent collaboration loop
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                # Base class + message types
│   ├── curriculum_agent.py          # Proposes learning roadmap
│   ├── time_estimation_agent.py     # Validates schedule feasibility
│   └── critic_agent.py             # Flags unrealistic plans
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx                 # React entry-point
│       ├── App.jsx                  # Main app component
│       ├── index.css                # Global styles (dark theme)
│       └── components/
│           ├── PlanForm.jsx         # Input form
│           ├── PlanResult.jsx       # Plan display + scores
│           ├── WeekCard.jsx         # Expandable week details
│           └── AgentLog.jsx         # Agent collaboration log
├── requirements.txt
└── README.md
```

## Example Output

### CLI

```
══════════════════════════════════════════════════════════════════════
  🎓  MULTI-AGENT STUDY PLANNER  🎓
══════════════════════════════════════════════════════════════════════

  Topic          : Machine Learning
  Skill level    : beginner
  Hours/week     : 12
  Duration       : 6 weeks

══════════════════════════════════════════════════════════════════════
  📋  ROUND 1 / 3
══════════════════════════════════════════════════════════════════════

── Step 1 → Curriculum Agent ──
  Generating study plan …

── 📝 Proposed Plan Summary ──
  Week 1: Python & Math Foundations  [NumPy Basics, Linear Algebra Review]
  Week 2: Data Preprocessing         [Pandas, Feature Engineering]
  ...

── Step 2 → Time Estimation Agent ──
  Feasible      : Yes ✅
  Score         : 8 / 10

── Step 3 → Critic Agent ──
  Verdict       : APPROVED ✅
  Quality score : 8 / 10

══════════════════════════════════════════════════════════════════════
  ✅  PLAN APPROVED!
══════════════════════════════════════════════════════════════════════
```

### Web Interface

The React frontend provides a dark-themed dashboard showing:
- **Plan overview** – topic, duration, level, prerequisites
- **Score cards** – quality score, feasibility score, schedule status, rounds taken
- **Weekly roadmap** – expandable cards with topics, learning objectives, resources, and milestones
- **Critic review** – strengths, weaknesses, and final verdict
- **Agent log** – round-by-round collaboration history

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | NVIDIA NIM API – `openai/gpt-oss-120b` via OpenAI SDK |
| Backend | Python, Flask, Flask-CORS |
| Frontend | React 18, Vite |
| Agent Framework | Custom multi-agent orchestrator with structured JSON messaging |

## License

MIT
