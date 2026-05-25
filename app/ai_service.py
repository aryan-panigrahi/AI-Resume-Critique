import ollama
import json
import re

MODEL_NAME = "llama3.1"

BASE_SYSTEM_PROMPT = """
You are a strict ATS-style Technical Recruiter and Resume Critique Expert.

Your behavior rules:
- Evaluate resumes ruthlessly, not politely.
- Avoid average or safe scoring.
- Use the FULL 1–100 scoring range.
- Weak resumes MUST receive very low scores.
- Exceptional resumes MUST receive very high scores.

You must:
1. Evaluate resumes holistically (skills, projects, impact, wording).
2. Think like an ATS + a senior recruiter.
3. Always provide actionable feedback.
4. Always suggest improved bullet point rewrites.
5. Always produce a professional summary.

Output ONLY valid JSON matching the provided schema.
Do NOT include explanations outside JSON.
"""

def clean_json_text(text: str) -> str:
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        return text[start:end]
    return text

async def critique_resume(parsed_data, job_description=None):
    # Determine the model to use dynamically
    model_to_use = MODEL_NAME
    try:
        models_list = ollama.list()
        available_models = [m.model for m in models_list.models] if hasattr(models_list, 'models') else []
        if MODEL_NAME not in available_models and not any(m.startswith(MODEL_NAME + ":") for m in available_models):
            if available_models:
                model_to_use = available_models[0]
                print(f"⚠️ '{MODEL_NAME}' not found. Falling back to available model: '{model_to_use}'")
            else:
                print(f"⚠️ No models found in Ollama. Will attempt to use '{MODEL_NAME}' which may fail.")
    except Exception as list_err:
        print(f"⚠️ Failed to list Ollama models: {list_err}. Proceeding with default model '{MODEL_NAME}'.")

    print(f"🤖 (Local AI) Analyzing with {model_to_use}...")

    if parsed_data.get("type") == "image_url":
        return {
            "candidate_name": "Unknown",
            "overall_score": 0,
            "summary": "Unable to analyze image-based resumes.",
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
            "raw_text": ""
        }

    resume_text = parsed_data.get("content", "")

    # ---------------- PROMPT ----------------
    prompt = f"""
TASK: Perform a deep, ATS-style resume critique.

RESUME TEXT:
{resume_text}
"""

    if job_description:
        prompt += f"""
JOB DESCRIPTION:
{job_description}

IMPORTANT:
- Treat the JD as the ATS reference baseline.
- Missing CORE tools MUST be listed as weaknesses using:
  "MISSING: <skill>"
"""

    prompt += """
ANALYSIS REQUIREMENTS (MANDATORY):

1. Identify key TECHNICAL SKILLS.
2. Identify PROJECTS built by the candidate.
   - Evaluate complexity, scale, ownership, and impact.
3. Critique WORDING:
   - Detect weak bullets ("worked on", "helped", "responsible for").
   - Rewrite using strong action verbs and measurable outcomes.
4. Generate a PROFESSIONAL SUMMARY:
   - 3–4 lines
   - Recruiter tone
   - Clearly state strengths and gaps.
5. Generate AT LEAST 3 IMPROVEMENTS.
   - Each improvement must be either:
     a) A before/after bullet rewrite
     b) A concrete project or wording improvement suggestion

SCORING RULES (STRICT):

- Score range: 1–100 (use full range).
- Base the score on:
  • Skills relevance → 40%
  • Project quality & depth → 40%
  • Wording & clarity → 20%

SCORING BANDS:
- 90–100 → Exceptional, near-ideal candidate
- 70–89 → Strong candidate with minor gaps
- 40–69 → Partial fit with notable weaknesses
- 10–39 → Weak fit, limited relevance
- 1–9 → Extremely weak or irrelevant resume

MISMATCH RULE (HARD CONSTRAINT):
- If a MAJOR job-description mismatch exists,
  cap the FINAL score at 35 regardless of sub-quality.

DISTRIBUTION RULE:
- Do NOT cluster scores around 50–70.
- Penalize weak resumes aggressively.
- Reward exceptional resumes decisively.

JSON SCHEMA (STRICT):
{
  "candidate_name": "Name or Unknown",
  "overall_score": number,
  "summary": "Professional summary",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvements": [
    {
      "original": "Original bullet or empty",
      "better": "Improved bullet or suggestion",
      "why": "Reason"
    }
  ]
}
"""

    messages = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    try:
        response = ollama.chat(
            model=model_to_use,
            messages=messages,
            format="json",
            options={
                "temperature": 0.15,
                "num_ctx": 8192
            }
        )

        raw = response["message"]["content"]
        cleaned = clean_json_text(raw)
        data = json.loads(cleaned)

        # ---------------- PYTHON SAFETY NET ----------------
        improvements = data.get("improvements", [])
        if not improvements:
            improvements = [{
                "original": "",
                "better": "Add quantified impact to your project descriptions (users, scale, performance).",
                "why": "Recruiters prioritize measurable results over responsibilities."
            }]

        score = int(data.get("overall_score", 50))
        score = max(1, min(score, 100))  # enforce 1–100

        final = {
            "candidate_name": data.get("candidate_name", "Candidate"),
            "overall_score": score,
            "summary": data.get("summary", "Professional summary unavailable."),
            "strengths": data.get("strengths", []),
            "weaknesses": data.get("weaknesses", []),
            "improvements": improvements,
            "raw_text": resume_text
        }

        print(f"✅ Analysis complete | Score: {score}")
        return final

    except Exception as e:
        print(f"❌ AI Service Error: {e}")
        return {
            "candidate_name": "Error",
            "overall_score": 1,
            "summary": "Failed to analyze resume.",
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
            "raw_text": str(e)
        }
