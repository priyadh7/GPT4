from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def get_recommendations(profile, feedback=""):
    prompt = f"""
You are a personalized learning recommendation system.
Student profile: {json.dumps(profile)}
Feedback: {feedback or "No feedback yet"}

Recommend exactly 5 learning resources suited to the student.
Return JSON only in this format:
{{
  "recommendations": [
    {{
      "title": "Artificial Intelligence Fundamentals",
      "reason": "Matches the student's interests",
      "score": 95
    }}
  ]
}}
Scores should be reasonable estimates, not measured probabilities.
"""
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False,
              "format": "json"},
        timeout=180
    )
    response.raise_for_status()
    data = response.json()["response"]
    parsed = json.loads(data)
    if isinstance(parsed, list):
        items = parsed
    else:
        items = parsed.get("recommendations", [])
    if not items:
        raise ValueError("The model returned no recommendations.")
    return items[:5]

@app.route("/", methods=["GET", "POST"])
def home():
    profile = {
        "name": "Agnes",
        "age": "20",
        "field": "Computer Science",
        "interests": "AI",
        "skill": "Beginner",
        "learning_type": "Practical",
        "goal": "Learn AI"
    }
    recommendations = []
    feedback = ""
    error = ""
    updated = False

    if request.method == "POST":
        for key in profile:
            profile[key] = request.form.get(key, profile[key]).strip()
        feedback = request.form.get("feedback", "").strip()
        updated = request.form.get("action") == "update"
        try:
            recommendations = get_recommendations(profile, feedback)
        except requests.RequestException:
            error = "Cannot connect to Ollama. Check that Ollama is running."
        except (ValueError, json.JSONDecodeError) as exc:
            error = f"Could not process recommendations: {exc}"

    return render_template(
        "index.html", profile=profile,
        recommendations=recommendations, feedback=feedback,
        error=error, updated=updated
    )

if __name__ == "__main__":
    app.run(debug=True)
