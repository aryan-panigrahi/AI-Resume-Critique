import ollama
import json
import re

MODEL_NAME = "qwen3:8b"

BASE_SYSTEM_PROMPT = """
You are a Senior Technical Recruiter and Resume Critique Expert.

Your job is to:
1. Evaluate resumes holistically (skills, projects, impact, wording).
2. Think like an ATS + a human recruiter.
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
    print(f"🤖 (Local AI) Analyzing with {MODEL_NAME}...")

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
TASK: Perform a deep resume critique.

RESUME TEXT:
{resume_text}

"""

    if job_description:
        prompt += f"""
JOB DESCRIPTION:
{job_description}

IMPORTANT:
- Treat the JD as the ATS reference.
- Missing core tools MUST be listed as weaknesses using:
  "MISSING: <skill>"
"""

    prompt += """
ANALYSIS REQUIREMENTS (MANDATORY):

1. Identify key TECHNICAL SKILLS.
2. Identify PROJECTS built by the candidate.
   - Evaluate project complexity.
   - Check for impact, scale, and ownership.
3. Critique WORDING:
   - Detect weak bullets ("worked on", "helped", "responsible for").
   - Rewrite them using strong action verbs and measurable impact.
4. Generate a PROFESSIONAL SUMMARY:
   - 3–4 lines
   - Recruiter tone
   - Mention strengths + gaps.
5. Generate AT LEAST 3 IMPROVEMENTS.
   - Each improvement must be either:
     a) A before/after bullet rewrite
     b) A concrete suggestion to improve projects or wording

SCORING RULES:
- Base score on:
  Skills relevance (40%)
  Project quality & depth (40%)
  Wording & clarity (20%)
- Score range: 0–100
- If major JD mismatch exists, cap score at 35.

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
            model=MODEL_NAME,
            messages=messages,
            format="json",
            options={
                "temperature": 0.2,
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
        score = max(0, min(score, 100))

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
            "overall_score": 0,
            "summary": "Failed to analyze resume.",
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
            "raw_text": str(e)
        }


