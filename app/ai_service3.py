import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()  # MUST be called

MODEL_NAME = "gemini-1.5-flash-8b"
def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


async def critique_resume(parsed_data, job_description=None):
    print(f"🚀 (Cloud AI) Analyzing with {MODEL_NAME}...")

    resume_text = parsed_data.get("content", "")

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "candidate_name": {"type": "STRING"},
            "overall_score": {"type": "NUMBER"},
            "summary": {"type": "STRING"},
            "strengths": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            },
            "weaknesses": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            },
            "improvements": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "original": {"type": "STRING"},
                        "better": {"type": "STRING"},
                        "why": {"type": "STRING"}
                    }
                }
            }
        }
    }

    try:
        client = get_client()

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Critique this resume:\n{resume_text}",
            config=types.GenerateContentConfig(
                system_instruction="You are a Senior Technical Recruiter...",
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )

        return json.loads(response.text)

    except Exception as e:
        print(f"❌ Cloud API Error: {e}")
        return {"error": str(e)}
