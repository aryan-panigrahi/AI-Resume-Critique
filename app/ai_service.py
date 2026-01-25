import ollama
import json
import re

MODEL_NAME = "llama3.1"

BASE_SYSTEM_PROMPT = """
You are a Binary Logic Assessor.
Your ONLY job is to verify if a candidate meets the MANDATORY REQUIREMENTS.
Output ONLY valid JSON.
"""

def clean_json_text(text):
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        return text[start:end]
    return text

async def critique_resume(parsed_data, job_description=None):
    print(f"🤖 (Local AI) Analyzing with {MODEL_NAME}...")

    if parsed_data['type'] == 'image_url':
        return {
            "candidate_name": "Unknown",
            "overall_score": 0,
            "summary": "Llama 3.1 cannot read images.",
            "strengths": [], "weaknesses": [], "improvements": [],
            "raw_text": ""
        }

    # --- THE LOGIC BRANCH ---
    if job_description:
        print("🎯 LOGIC MODE: verifying technical match...")
        prompt_content = f"""
        TASK: Check for Critical Skills Mismatch.
        
        RESUME:
        {parsed_data['content']}

        JOB DESCRIPTION (JD):
        {job_description}

        INSTRUCTIONS:
        1. Compare the Hard Skills in JD vs Resume.
        2. "is_match": False if missing core tools (ISVA, TDI, LDAP, etc.).
        3. "weaknesses": MUST list the missing tools. Format them exactly like this: "MISSING: [Tool Name]".
           Example: ["MISSING: IBM Security Verify Access", "MISSING: Tivoli Directory Integrator"]
        
        JSON SCHEMA:
        {{
            "candidate_name": "Name",
            "is_match": boolean, 
            "overall_score": 0, 
            "summary": "Briefly explain the gap.",
            "strengths": ["List matching skills"],
            "weaknesses": ["MISSING: Tool1", "MISSING: Tool2"],
            "improvements": []
        }}
        """
    else:
        # Normal Mode
        prompt_content = f"""
        TASK: Analyze this resume.
        RESUME: {parsed_data['content']}
        JSON SCHEMA:
        {{
            "candidate_name": "Name",
            "is_match": true,
            "overall_score": 50,
            "summary": "Summary",
            "strengths": [], "weaknesses": [], "improvements": []
        }}
        """

    messages = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt_content}
    ]

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            format="json",
            options={"temperature": 0.0}
        )

        raw_content = response['message']['content']
        cleaned_content = clean_json_text(raw_content)
        data = json.loads(cleaned_content)

        # --- PYTHON OVERRIDE ---
        score = data.get("overall_score", 0)
        is_match = data.get("is_match", True)

        if job_description and is_match is False:
            print(f"⚠️ MISMATCH DETECTED. Crushing score from {score} to 12.")
            score = 12  # HARD CAP
        
        final_data = {
            "candidate_name": data.get("candidate_name", "Candidate"),
            "overall_score": score,
            "summary": data.get("summary", "Analysis complete."),
            "strengths": data.get("strengths", []),
            "weaknesses": data.get("weaknesses", []),
            "improvements": data.get("improvements", []),
            "raw_text": parsed_data['content'] # Send Raw Text
        }

        print(f"✅ Analysis complete! Final Score: {score}")
        return final_data

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "candidate_name": "Error",
            "overall_score": 0,
            "summary": "Error parsing AI response.",
            "strengths": [], "weaknesses": [], "improvements": [],
            "raw_text": str(e)
        }