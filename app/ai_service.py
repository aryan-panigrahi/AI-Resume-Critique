import httpx
import json
import re

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
DEFAULT_MODEL = "meta-llama-3.1-8b-instruct"

BASE_SYSTEM_PROMPT = """
You are an elite, ruthlessly analytical, executive-level technical recruiter and principal ATS (Applicant Tracking System) engineer.
Your purpose is to critique technical resumes with surgical precision, applying the highest global standards of Fortune 100 engineering teams.

Your core operational directives:
1. Ruin mediocrity. Never provide generic, polite, or patronizing encouragement. Be severe, objective, and deeply analytical.
2. Rate resumes strictly using the full 1-100 score range. Do not bundle scores around safe averages (50-70). A poorly optimized or low-impact resume must be scored aggressively low (e.g., 20-45).
3. Evaluate resumes from a double perspective:
   - The ATS Parser: Assess document readability, layout compatibility, hierarchical syntax, and keyword-density index.
   - The Principal Recruiter: Assess deep business impact, technical ownership, system complexity, and wording maturity.
4. Enforce the Google X-Y-Z formula: "Accomplished [X] as measured by [Y], by doing [Z]" for all bullet points. Bullet points lacking quantitative metrics (percentages, dollars, hours saved, scale parameters) are considered major vulnerabilities.
5. Ensure candidate name extraction is flawless. Under no circumstances should you hallucinate, make up names, or use generic placeholders like "Candidate" or "Unknown" if a valid name can be extracted.

Output ONLY a JSON payload conforming exactly to the requested JSON schema. Do not output markdown fences or explanatory text outside of the JSON payload.
"""

def clean_json_text(text: str) -> str:
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        return text[start:end]
    return text

def extract_candidate_name_from_text(resume_text: str) -> str:
    if not resume_text:
        return ""
    lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
    for line in lines[:5]:
        # clean the line of common markdown/text symbols
        clean_line = line.strip('*_#-"\'•●o- ')
        if not clean_line:
            continue
        clean_line_lower = clean_line.lower()
        
        # Check line length (names are rarely > 35 chars or < 3 chars)
        if len(clean_line) < 3 or len(clean_line) > 35:
            continue
            
        # Must contain alphabetic characters
        if not any(c.isalpha() for c in clean_line):
            continue
            
        # Exclude lines that contain emails, phone numbers, website indicators, or resume header/section words
        keywords = [
            'resume', 'cv', 'curriculum', 'contact', 'email', 'phone', '@', 'http', 'www', '+', 
            'objective', 'summary', 'page', 'address', 'portfolio', 'github', 'linkedin', 
            'experience', 'education', 'skills', 'profile', 'about', 'work', 'history'
        ]
        if any(x in clean_line_lower for x in keywords):
            continue
        
        # If we passed all checks, this is a very strong candidate for a name!
        return clean_line
    return ""

def check_is_resume_heuristically(text: str) -> bool:
    if not text:
        return False
    txt_lower = text.lower()
    
    # 1. Look for standard resume headings/keywords
    resume_keywords = [
        "experience", "education", "skills", "projects", "employment", 
        "career", "university", "school", "technologies", "certificate", 
        "summary", "work history", "contact", "email", "phone", "profile"
    ]
    matches = sum(1 for kw in resume_keywords if kw in txt_lower)
    
    # 2. Look for programming/coding file markers
    code_markers = [
        "import ", "def ", "class ", "function ", "const ", "let ", 
        "public class", "public void", "void main", "using namespace",
        "<html>", "dockerfile", "pip install", "npm install", "api_key"
    ]
    code_matches = sum(1 for marker in code_markers if marker in txt_lower)
    
    # Heuristic rules:
    # If we have code markers and very few resume keywords, it's likely code
    if code_matches > 3 and matches < 2:
        return False
        
    # If it is extremely short (< 150 characters), it's not a resume
    if len(text.strip()) < 150:
        return False
        
    # If it contains zero resume keywords, it's highly unlikely to be a resume
    if matches == 0:
        # Check if it has an email or phone number which might be a minimal contact card/resume
        has_contact = bool(re.search(r'[\w\.-]+@[\w\.-]+', text)) or bool(re.search(r'\+?\d{10,12}', text))
        if not has_contact:
            return False
            
    return True

def extract_candidate_data(resume_text: str) -> dict:
    """
    Extract candidate sections (skills, experience, projects, education, certifications)
    from the raw resume text using heuristics.
    """
    sections = {
        "skills": "",
        "experience": "",
        "projects": "",
        "education": "",
        "certifications": "",
        "summary": "",
        "other": ""
    }
    
    if not resume_text:
        return sections
        
    current_section = "summary"
    lines = resume_text.split('\n')
    
    keywords_map = {
        "skills": ["skills", "technologies", "technical competencies", "core competencies", "key skills", "expertise", "languages & technologies", "technical skills", "tech stack"],
        "experience": ["experience", "employment history", "work history", "professional experience", "work experience", "employment", "career history"],
        "projects": ["projects", "personal projects", "academic projects", "key projects", "selected projects", "academic achievements"],
        "education": ["education", "academic profile", "academic history", "academic background", "credentials", "academic qualifications"],
        "certifications": ["certifications", "certificates", "accreditations", "licensures", "professional certifications"]
    }
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        lower_line = line_clean.lower().strip('*_#-"\':•● ')
        
        # Determine if it's a section header
        is_header = False
        if len(lower_line) < 35:
            for sec, kws in keywords_map.items():
                if lower_line in kws or any(lower_line == kw for kw in kws) or (len(lower_line) > 3 and any(kw in lower_line for kw in kws) and not any(x in lower_line for x in ["working", "using", "experience of", "skills in", "experience with", "using ", "projects with"])):
                    current_section = sec
                    is_header = True
                    break
                    
        if is_header:
            continue
            
        sections[current_section] += line + "\n"
        
    # Clean up trailing and leading whitespaces
    for key in sections:
        sections[key] = sections[key].strip()
        
    return sections

async def critique_resume(parsed_data, job_description=None):
    # Determine the model to use dynamically from LM Studio
    model_to_use = DEFAULT_MODEL
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LM_STUDIO_BASE_URL}/models")
            if response.status_code == 200:
                models_data = response.json()
                if "data" in models_data and len(models_data["data"]) > 0:
                    model_to_use = models_data["data"][0]["id"]
                    print(f"[INFO] Found loaded model in LM Studio: '{model_to_use}'")
                else:
                    print(f"[WARN] No active models found in LM Studio. Will attempt default model: '{model_to_use}'")
            else:
                print(f"[WARN] LM Studio returned status code {response.status_code}. Using default model: '{model_to_use}'")
    except Exception as list_err:
        print(f"[WARN] Failed to list LM Studio models: {list_err}. Proceeding with default model '{model_to_use}'.")

    print(f"[INFO] (Local AI via LM Studio) Analyzing with {model_to_use}...")

    if parsed_data.get("type") == "image_url":
        return {
            "candidate_name": "Unknown",
            "overall_score": 0,
            "summary": "Unable to analyze image-based resumes.",
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
            "raw_text": "",
            "is_resume": False
        }

    resume_text = parsed_data.get("content", "")

    # Extract candidate data from resume
    candidate_sections = extract_candidate_data(resume_text)
    total_parsed_len = len(candidate_sections["skills"]) + len(candidate_sections["experience"])
    if total_parsed_len < 100:
        resume_data_str = f"Raw Resume Text:\n{resume_text}"
    else:
        resume_data_str = f"""
[SUMMARY/OVERVIEW]
{candidate_sections['summary'] or 'None'}

[SKILLS & TECHNOLOGIES]
{candidate_sections['skills'] or 'None explicitly listed'}

[PROFESSIONAL EXPERIENCE]
{candidate_sections['experience'] or 'None explicitly listed'}

[PROJECTS]
{candidate_sections['projects'] or 'None explicitly listed'}

[EDUCATION]
{candidate_sections['education'] or 'None explicitly listed'}

[CERTIFICATIONS]
{candidate_sections['certifications'] or 'None explicitly listed'}
"""

    if job_description:
        system_prompt = """
You are an advanced ATS and hiring evaluator. Compare the candidate resume against the provided Job Description and reason carefully before scoring.
Your evaluation must run fresh and evaluate the candidate strictly on relevance to the JD requirements.
"""
        prompt = f"""
Job Description:
{job_description}

Candidate Resume Data:
{resume_data_str}

Instructions:

1. Analyze the JD requirements carefully.
2. Compare candidate skills and experience against the JD.
3. Reason about relevance, depth, and alignment.
4. Identify missing critical requirements.
5. Give higher weight to JD alignment than generic resume quality.
6. The AI should reason step-by-step internally in a detailed reasoning-based analysis explaining WHY the candidate matches or does not match the JD.
7. You must evaluate the following 8 dimensions in your detailed reasoning:
   - Skill match percentage
   - Relevant experience match
   - Missing required skills
   - Preferred skills match
   - Role/domain relevance
   - Seniority alignment
   - Project relevance
   - Education/certification relevance
8. Penalize resumes that contain unrelated experience or keyword stuffing.
9. Generate AT LEAST 5-8 improvement suggestions across multiple categories (Skills, Experience, Projects, Education, Certifications, Keywords, Formatting, ATS Optimization). Cover different resume sections.
10. Return ONLY a valid JSON payload conforming exactly to the requested JSON schema. No conversational prefixes, no markdown formatting fences (e.g., do not wrap in ```json), just the raw JSON object conforming to the structure below.

ANTI-HALLUCINATION DIRECTIVE (CRITICAL):
- NEVER invent metrics, percentages, dollar amounts, impact statements, or achievements that are NOT in the resume.
- If the resume lacks quantified outcomes, suggest adding them using template language: "Consider quantifying this with [specific metric type]."
- The "better" field MUST NOT contain fabricated statistics (e.g., do NOT write "improved by 30%" or "saved $2M").
- Instead use template placeholders: "Accomplished [specific outcome] as measured by [your metric], by doing [your method]."
- Only reference technologies, skills, and experiences ACTUALLY present in the resume text.
- If a skill or achievement is missing, say it is missing rather than inventing it.

[STRICT JSON SCHEMA COMPLIANCE]
{{
  "candidate_name": "The candidate's exact full name (e.g., 'Aryan Panigrahi'). Do NOT return placeholders unless completely anonymous.",
  "is_resume": true,
  "overall_score": 75,
  "skill_match_score": 80,
  "experience_match_score": 70,
  "missing_skills": ["List of missing required/preferred skills as simple strings"],
  "matched_skills": ["List of skills found in BOTH the JD and the resume"],
  "strengths": [
    "A direct alignment strength, e.g., 'Possesses robust TypeScript development credentials aligning with team requirements.'"
  ],
  "weaknesses": [
    "A direct technical or seniority gap, e.g., 'MISSING: Kubernetes container orchestration experience.'"
  ],
  "hiring_recommendation": "A concise (1-2 sentences) hiring recommendation (e.g. 'Strong match for senior roles', 'Borderline fit due to skill deficits')",
  "detailed_reasoning": "Step-by-step explanation addressing all 8 dimensions (Skill match, Relevant experience, Missing skills, Preferred skills, Role/domain relevance, Seniority alignment, Project relevance, Education/certification relevance) and explaining why the candidate matches or does not match.",
  "summary": "3-4 sentences in a professional recruiter tone summarizing the candidate's fit, strengths, and critical gaps. This must integrate the overall recommendation.",
  "improvements": [
    {{
      "category": "One of: Skills, Experience, Projects, Education, Certifications, Keywords, Formatting, ATS Optimization",
      "original": "VERBATIM weak bullet point extracted from the resume. Leave empty string if this is a general recommendation.",
      "better": "Improved rewrite or actionable suggestion.",
      "why": "Detailed explanation of why this improves the resume.",
      "source": "One of: resume_content, missing_content, jd_requirement"
    }}
  ]
}}
"""
    else:
        system_prompt = BASE_SYSTEM_PROMPT
        prompt = f"""
[ATS AUDIT BRIEF & RECRUITER CRITIQUE TASK]
Perform an exhaustive, high-fidelity corporate Applicant Tracking System (ATS) audit and professional senior recruiter critique on the candidate resume provided below.

[RESUME VALIDITY DETECTION (CRITICAL)]
Before conducting the critique, analyze whether the provided text actually represents a professional resume or CV.
- If the document is NOT a resume (e.g., it is programming source code, a generic cover letter, a shopping list, a textbook excerpt, financial accounts, or random prose):
  1. Set the "is_resume" boolean field to false.
  2. Set "overall_score" to 0.
  3. Write a clinical, severe summary in the "summary" field explaining that the uploaded document does not appear to be a professional resume.
  4. Leave other fields empty.
- If the document IS a professional resume, set "is_resume" to true and perform the critique normally.

[NAME EXTRACTION CORE OBJECTIVE - CRITICAL]
Identify and extract the candidate's actual full name.

[CANDIDATE RESUME INPUT]
{resume_data_str}

[REQUIRED ANALYSIS DIMENSIONS]
Audit and parse the resume text against the following severe professional criteria:
1. Technical alignment & keyword depth (40%)
2. Quantitative impact & Google X-Y-Z phrasing (40%)
3. Wording, grammar, action verbs, and formatting layout (20%)

Generate AT LEAST 5-8 improvement suggestions across multiple categories (Skills, Experience, Projects, Education, Certifications, Keywords, Formatting, ATS Optimization). Cover different resume sections.

ANTI-HALLUCINATION DIRECTIVE (CRITICAL):
- NEVER invent metrics, percentages, dollar amounts, impact statements, or achievements that are NOT in the resume.
- If the resume lacks quantified outcomes, suggest adding them using template language: "Consider quantifying this with [specific metric type]."
- The "better" field MUST NOT contain fabricated statistics (e.g., do NOT write "improved by 30%" or "saved $2M").
- Instead use template placeholders: "Accomplished [specific outcome] as measured by [your metric], by doing [your method]."
- Only reference technologies, skills, and experiences ACTUALLY present in the resume text.
- If a skill or achievement is missing, say it is missing rather than inventing it.

[STRICT JSON SCHEMA COMPLIANCE]
Return ONLY a valid JSON payload conforming exactly to this structure. No conversational prefixes, no markdown formatting fences (e.g., do not wrap in ```json), just the raw JSON object:
{{
  "candidate_name": "The candidate's exact full name (e.g., 'Aryan Panigrahi'). Do NOT return placeholders unless completely anonymous.",
  "is_resume": true,
  "overall_score": 78,
  "strengths": [
    "A highly professional engineering strength from the resume, e.g., 'Engineered high-throughput REST APIs leveraging FastAPI, demonstrating robust asynchronous design.'"
  ],
  "weaknesses": [
    "A direct, critical technical or structural gap, e.g., 'MISSING: Containerization (Docker) or Cloud infrastructure patterns.'"
  ],
  "summary": "3-4 sentences in a professional, severe, clinical recruiter tone evaluating the profile, strengths, and critical gaps. No emojis, no fluffy encouragement. If the document is not a resume, explain that clearly here.",
  "improvements": [
    {{
      "category": "One of: Skills, Experience, Projects, Education, Certifications, Keywords, Formatting, ATS Optimization",
      "original": "VERBATIM weak bullet point extracted from the resume. Leave empty string if this is a general recommendation.",
      "better": "Improved rewrite or actionable suggestion.",
      "why": "Detailed explanation of why this improves the resume.",
      "source": "One of: resume_content, missing_content, jd_requirement"
    }}
  ]
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        is_reasoning_model = any(tag in model_to_use.lower() for tag in ["deepseek-r1", "qwen3", "reasoning", "think"])
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            payload = {
                "model": model_to_use,
                "messages": messages,
                "max_tokens": 4096
            }
            if is_reasoning_model:
                payload["temperature"] = 0.6
            else:
                payload["temperature"] = 0.05
                
            response = await client.post(
                f"{LM_STUDIO_BASE_URL}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            res_json = response.json()
            raw = res_json["choices"][0]["message"]["content"]
        
        cleaned = clean_json_text(raw)
        data = json.loads(cleaned)

        is_resume = data.get("is_resume", True)
        if is_resume:
            heuristic_check = check_is_resume_heuristically(resume_text)
            if not heuristic_check:
                print("[WARN] Local heuristic determined this is not a resume. Overriding AI.")
                is_resume = False

        improvements = data.get("improvements", [])
        if is_resume and not improvements:
            improvements = [{
                "category": "ATS Optimization",
                "original": "",
                "better": "Add quantified impact to your project descriptions (users, scale, performance).",
                "why": "Recruiters prioritize measurable results over responsibilities.",
                "source": "missing_content"
            }]
        elif not is_resume:
            improvements = []

        score = int(data.get("overall_score", 50)) if is_resume else 0
        score = max(0, min(score, 100))

        ai_name = data.get("candidate_name", "")
        if is_resume and ai_name:
            ai_name = ai_name.strip().strip('*_#-"\'')
            if ai_name.lower() in ["candidate", "unknown", "name", "n/a", "unknown name", "candidate name", "user", "resume owner", "the candidate"]:
                ai_name = ""
        else:
            ai_name = "Document"
        
        if is_resume and not ai_name:
            ai_name = extract_candidate_name_from_text(resume_text)
            
        if is_resume and not ai_name:
            ai_name = "Candidate"

        skill_score = int(data.get("skill_match_score", score)) if is_resume else 0
        exp_score = int(data.get("experience_match_score", score)) if is_resume else 0
        missing_skills = data.get("missing_skills", []) if is_resume else []
        hiring_rec = data.get("hiring_recommendation", "") if is_resume else ""
        detailed_reasoning = data.get("detailed_reasoning", "") if is_resume else ""

        # Post-process missing skills to verify they are in weaknesses array in case they aren't
        weaknesses = data.get("weaknesses", []) if is_resume else []
        if is_resume and missing_skills:
            for skill in missing_skills:
                matching_weakness = any(skill.lower() in w.lower() for w in weaknesses)
                if not matching_weakness:
                    weaknesses.append(f"MISSING: {skill}")

        final = {
            "candidate_name": ai_name,
            "overall_score": score,
            "skill_match_score": skill_score,
            "experience_match_score": exp_score,
            "missing_skills": missing_skills,
            "matched_skills": data.get("matched_skills", []) if is_resume else [],
            "strengths": data.get("strengths", []) if is_resume else [],
            "weaknesses": weaknesses,
            "improvements": improvements,
            "hiring_recommendation": hiring_rec,
            "detailed_reasoning": detailed_reasoning,
            "summary": data.get("summary", "Professional summary unavailable."),
            "raw_text": resume_text,
            "is_resume": is_resume,
            "job_description": job_description or ""
        }

        print(f"[SUCCESS] Analysis complete | Score: {score}")
        return final

    except Exception as e:
        print(f"[WARN] Local AI API failed ({e}). Running high-fidelity local heuristic parser...")
        
        is_resume = check_is_resume_heuristically(resume_text)
        if not is_resume:
            return {
                "candidate_name": "Document",
                "overall_score": 0,
                "skill_match_score": 0,
                "experience_match_score": 0,
                "missing_skills": [],
                "matched_skills": [],
                "strengths": [],
                "weaknesses": [],
                "improvements": [],
                "hiring_recommendation": "Document is not a valid resume.",
                "detailed_reasoning": "Standard heuristic check failed. The uploaded file does not look like a resume.",
                "summary": "The uploaded document does not appear to be a professional resume or CV. It is missing key resume sections (Experience, Education, Skills) or resembles source code/plain text. Please upload a valid resume document.",
                "raw_text": resume_text,
                "is_resume": False,
                "job_description": job_description or ""
            }
            
        candidate_name = extract_candidate_name_from_text(resume_text)
        if not candidate_name:
            candidate_name = "Candidate"
            
        lines = [l.strip() for l in resume_text.split('\n') if l.strip()]

        skills_map = {
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript", 
            "react": "React", "node": "Node.js", "docker": "Docker", "aws": "AWS",
            "git": "Git", "sql": "SQL", "mongodb": "MongoDB", "postgres": "PostgreSQL",
            "fastapi": "FastAPI", "django": "Django", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
            "kubernetes": "Kubernetes", "kafka": "Apache Kafka", "redis": "Redis", "graphql": "GraphQL"
        }
        
        found_skills = []
        for key, val in skills_map.items():
            if re.search(r'\b' + re.escape(key) + r'\b', resume_text, re.IGNORECASE):
                found_skills.append(val)
                
        score = 65 + min(len(found_skills) * 3, 20)
        
        jd_skills_missing = []
        jd_skills_matched = []
        total_jd_keywords = 0
        if job_description:
            jd_text_lower = job_description.lower()
            for key, val in skills_map.items():
                in_jd = re.search(r'\b' + re.escape(key) + r'\b', jd_text_lower, re.IGNORECASE)
                in_res = re.search(r'\b' + re.escape(key) + r'\b', resume_text.lower(), re.IGNORECASE)
                if in_jd:
                    total_jd_keywords += 1
                    if in_res:
                        jd_skills_matched.append(val)
                    else:
                        jd_skills_missing.append(val)
            
            if total_jd_keywords > 0:
                match_ratio = len(jd_skills_matched) / total_jd_keywords
                score = int(45 + match_ratio * 45)
                
            if len(jd_skills_matched) == 0 and total_jd_keywords > 3:
                score = min(score, 35)
                
        score = min(max(score, 25), 96)

        strengths = []
        if jd_skills_matched:
            strengths.append(f"Strong alignment with target job description on: {', '.join(jd_skills_matched[:4])}.")
        elif len(found_skills) >= 4:
            strengths.append(f"Strong technical stack highlighting {', '.join(found_skills[:4])}.")
        else:
            strengths.append("Logical core skill section presenting software engineering capabilities.")
            
        if "Git" in found_skills or "Docker" in found_skills:
            strengths.append("Demonstrated modern containerization and version control practices.")
        if "FastAPI" in found_skills or "Django" in found_skills or "Node.js" in found_skills:
            strengths.append("Solid backend application architectural patterns.")
            
        if len(strengths) < 3:
            strengths.append("Logical section structural layout promoting rapid recruiter scanning.")

        weaknesses = []
        if job_description and jd_skills_missing:
            for missing_skill in jd_skills_missing[:4]:
                weaknesses.append(f"MISSING: {missing_skill} keyword alignment from target Job Description.")
        else:
            if "PyTorch" not in found_skills and "TensorFlow" not in found_skills:
                weaknesses.append("MISSING: Artificial Intelligence (AI) and Machine Learning (ML) toolkits.")
            if "Docker" not in found_skills and "AWS" not in found_skills:
                weaknesses.append("MISSING: Modern Cloud deployment architectures (AWS, Docker containers).")
            if len(found_skills) < 6:
                weaknesses.append("MISSING: Comprehensive technical domain keyword depth.")
        
        weaknesses.append("MISSING: Quantified project metrics and business impact statements.")

        improvements = []
        actual_bullets = []
        bullet_symbols = ['-', '*', '•', '●', '▪']
        for line in lines:
            line_clean = line.strip()
            starts_with_bullet = any(line_clean.startswith(sym) for sym in bullet_symbols)
            words = line_clean.split()
            if starts_with_bullet and len(words) >= 5 and len(line_clean) < 160:
                for sym in bullet_symbols:
                    if line_clean.startswith(sym):
                        line_clean = line_clean[len(sym):].strip()
                        break
                actual_bullets.append(line_clean)
            elif len(words) >= 7 and len(line_clean) > 30 and len(line_clean) < 140 and any(v in line_clean.lower() for v in ["worked", "managed", "helped", "assisted", "developed", "built", "implemented", "created", "designed"]):
                actual_bullets.append(line_clean)
                
            if len(actual_bullets) >= 4:
                break
                
        def rewrite_bullet(original_bullet):
            orig_lower = original_bullet.lower()
            if any(k in orig_lower for k in ["react", "vue", "angular", "frontend", "ui", "ux", "web", "css", "html", "javascript"]):
                better = "Designed and optimized responsive UI modules using React and state management, improving page load speed by [your measured percentage] and boosting user engagement metrics."
                why = "Replaces passive frontend task statements with a template for measurable speed and engagement metrics to demonstrate principal engineering ownership."
                category = "Projects"
            elif any(k in orig_lower for k in ["fastapi", "django", "node", "express", "backend", "api", "rest", "graphql"]):
                better = "Architected high-throughput REST APIs, implementing caching pipelines that reduced database query latency by [your measured latency improvement] under peak loads."
                why = "Specific backend framework citations coupled with measurable latency statistics convey deep engineering maturity."
                category = "Experience"
            elif any(k in orig_lower for k in ["db", "database", "postgres", "sql", "mongodb", "mysql"]):
                better = "Optimized database indexing and analytical queries, resulting in [measured percentage] performance improvement across core search dashboards."
                why = "Focuses on explicit performance optimization and query tuning rather than passive maintenance duties."
                category = "Experience"
            elif any(k in orig_lower for k in ["cloud", "aws", "docker", "kubernetes", "infra", "devops", "ci/cd", "jenkins"]):
                better = "Spearheaded migration of legacy services to containerized AWS instances, reducing infrastructure overhead by [your measured savings] while improving pipeline uptime."
                why = "Replacing passive migration statements with explicit container/cloud metrics demonstrates strong DevOps competence."
                category = "Experience"
            elif any(k in orig_lower for k in ["lead", "manage", "team", "agile", "scrum", "project"]):
                better = "Orchestrated cross-functional engineering team deliverables under agile frameworks, accelerating product release velocity by [your measured improvement]."
                why = "Highlights proactive engineering leadership and sprint management expertise instead of simple teamwork references."
                category = "Experience"
            else:
                better = "Spearheaded high-performance software features and database optimizations, yielding [your measured percentage] increase in system throughput."
                why = "Using active verbs and quantified results (throughput increase) asserts technical capability and business value."
                category = "Projects"
                
            return {
                "category": category,
                "original": original_bullet,
                "better": better,
                "why": why,
                "source": "resume_content"
            }

        if actual_bullets:
            for b in actual_bullets[:6]:
                improvements.append(rewrite_bullet(b))
        else:
            improvements.append({
                "category": "Experience",
                "original": "Responsible for backend development and database integration.",
                "better": "Architected backend services using FastAPI and PostgreSQL, implementing Redis caching to reduce database query latency by [your measured latency improvement].",
                "why": "Specific backend framework citations coupled with measurable latency statistics convey deep engineering maturity.",
                "source": "resume_content"
            })
            improvements.append({
                "category": "Projects",
                "original": "Helped with frontend UI design and state management.",
                "better": "Designed and engineered [number of] reusable React UI components leveraging Redux Toolkit, improving state transition speeds by [your measured percentage].",
                "why": "Replacing 'helped' with 'designed and engineered' asserts technical competence, backed by quantitative metrics.",
                "source": "resume_content"
            })
            improvements.append({
                "category": "Experience",
                "original": "Worked on migrating legacy code and fixing bug reports.",
                "better": "Orchestrated migration of legacy monolith to microservices architecture, resolving [your percentage] of high-severity bugs and enhancing system stability.",
                "why": "Highlights proactive engineering ownership and legacy migration expertise instead of passive bug patching.",
                "source": "resume_content"
            })

        jd_match_text = ""
        if job_description:
            matched_pct = int((len(jd_skills_matched) / total_jd_keywords * 100) if total_jd_keywords > 0 else 0)
            jd_match_text = f" The profile matches approximately {matched_pct}% of the target job description keywords."
            if jd_skills_missing:
                jd_match_text += f" Critical missing keywords include: {', '.join(jd_skills_missing[:3])}."
                
        summary = f"The resume presents a solid engineering candidate, {candidate_name}, with notable experience in {', '.join(found_skills[:3]) if found_skills else 'software development'}.{jd_match_text} However, the profile shows critical keyword gaps in modern cloud deployment and AI/ML competencies. Wording throughout project bullets relies heavily on passive responsibilities and lacks the quantified metrics required to stand out in competitive ATS pipelines."

        return {
            "candidate_name": candidate_name,
            "overall_score": score,
            "skill_match_score": int(score * 1.05) if job_description else score,
            "experience_match_score": int(score * 0.95) if job_description else score,
            "missing_skills": jd_skills_missing,
            "matched_skills": jd_skills_matched,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvements": improvements,
            "hiring_recommendation": "Borderline fit due to technical skill deficits." if jd_skills_missing else "Good alignment with core requirements.",
            "detailed_reasoning": f"Simulated offline analysis. Candidate highlights skills in: {', '.join(found_skills)}. JD match ratio is high.",
            "summary": summary,
            "raw_text": resume_text,
            "is_resume": is_resume,
            "job_description": job_description or ""
        }
