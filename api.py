"""
Flask API server for the Multi-Agent Study Planner.

Endpoints
─────────
POST /api/generate   – Generate a study plan (runs the full agent loop)
GET  /api/health     – Health check
"""

from __future__ import annotations

import json
import logging
import traceback
from threading import Thread

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from orchestrator import Orchestrator

# ── App setup ───────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── API routes ──────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "model": "openai/gpt-oss-120b"})


@app.route("/api/generate", methods=["POST"])
def generate_plan():
    """
    Expects JSON body:
    {
      "topic": "Machine Learning",
      "skill_level": "beginner",
      "available_hours": 10,
      "duration_weeks": 4,
      "goals": "optional specific goals"
    }
    """
    data = request.get_json(force=True)

    # Validate required fields
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400

    user_request = {
        "topic": topic,
        "skill_level": data.get("skill_level", "beginner"),
        "available_hours": float(data.get("available_hours", 10)),
        "duration_weeks": int(data.get("duration_weeks", 4)),
        "goals": data.get("goals") or None,
    }

    logger.info("Generating plan for: %s", user_request)

    try:
        orchestrator = Orchestrator()
        result = orchestrator.run(user_request)

        return jsonify({
            "success": True,
            "plan": result.get("plan", {}),
            "time_report": result.get("time_report", {}),
            "review": result.get("review", {}),
            "approved": result.get("approved", False),
            "rounds": result.get("rounds", 0),
            "log": result.get("log", []),
        })

    except Exception as exc:
        logger.error("Generation failed: %s", traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ── Serve React frontend ───────────────────────────────────────────────
@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ── Run ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Study Planner API running at http://localhost:5000")
    print("📖 Frontend at http://localhost:5173 (dev) or http://localhost:5000 (prod)\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
