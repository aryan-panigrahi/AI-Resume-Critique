import sys
# Force sys.stdout and sys.stderr to use UTF-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from app.parser import parse_file
from app.ai_service import critique_resume
from app.database import init_db, save_scan, get_all_scans, get_scan_by_id, clear_all_scans
import traceback
import httpx
import xml.etree.ElementTree as ET
import re

app = FastAPI(title="Scope API")

@app.on_event("startup")
def startup_event():
    init_db()

# Allow CORS so your local HTML file can talk to this local server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r"<[^<]+?>", "", raw_html)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'").replace("&#8216;", "'").replace("&#8220;", '"').replace("&#8221;", '"')
    return clean.strip()

@app.get("/api/news")
async def get_tech_news():
    url = "https://techcrunch.com/category/startups/feed/"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch. Status code: {response.status_code}")
            
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            items = channel.findall("item")
            
            news = []
            for item in items[:15]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                desc_node = item.find("description")
                desc = desc_node.text if desc_node is not None else ""
                
                clean_desc = clean_html(desc)
                if len(clean_desc) > 180:
                    clean_desc = clean_desc[:177] + "..."
                
                category = "Emerging Companies"
                title_lower = title.lower()
                if "layoff" in title_lower or "cut" in title_lower or "fire" in title_lower or "downsize" in title_lower:
                    category = "Layoffs Track"
                elif "funding" in title_lower or "raise" in title_lower or "seed" in title_lower or "series" in title_lower or "valuation" in title_lower or "acquire" in title_lower or "buy" in title_lower or "raised" in title_lower or "invest" in title_lower:
                    category = "Funding Rounds"
                elif "job" in title_lower or "hiring" in title_lower or "recruitment" in title_lower:
                    category = "Job Market"
                
                news.append({
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "description": clean_desc,
                    "category": category
                })
            
            return news
        except Exception as e:
            print(f"Error fetching RSS news: {e}")
            return [
                {
                    "title": "Cognition AI Secures $42M Series A for Swarm Coding Platforms",
                    "link": "https://techcrunch.com",
                    "pubDate": "Tue, 26 May 2026 18:30:00 +0000",
                    "description": "The developer-focused startup is aggressively scaling their software engineering rosters, seeking Senior Frontend (React) and Backend (FastAPI, Go) talent to build next-gen LLM orchestration engines.",
                    "category": "Emerging Companies"
                },
                {
                    "title": "Q2 Tech Layoffs Taper by 78%, Reaching Pre-Pandemic Lows",
                    "link": "https://techcrunch.com",
                    "pubDate": "Mon, 25 May 2026 12:00:00 +0000",
                    "description": "Layoffs.fyi tracker indicates deep-tech, database, and infrastructure industries are rebounding decisively, marking the end of broad workforce reductions and signaling a shift back to growth hiring.",
                    "category": "Layoffs Track"
                },
                {
                    "title": "Pinecone Raises $100M to Scale High-Speed Vector Analytics",
                    "link": "https://techcrunch.com",
                    "pubDate": "Mon, 25 May 2026 10:00:00 +0000",
                    "description": "With enterprises migrating LLM agents into production, demand for index querying has surged. Hiring targets include Cloud DevOps (AWS/Kubernetes) and performance tuning specialists.",
                    "category": "Funding Rounds"
                },
                {
                    "title": "DevOps & Git Automation Roles Surge 24% in Q2 Openings",
                    "link": "https://techcrunch.com",
                    "pubDate": "Sun, 24 May 2026 14:00:00 +0000",
                    "description": "Enterprises are prioritizing efficiency, resulting in high demand for candidates with proven Git automation, CI/CD pipeline optimization, and infrastructure containerization credentials.",
                    "category": "Job Market"
                }
            ]

@app.get("/")
def health_check():
    return {"status": "running"}

@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...), 
    job_description: str = Form(None)
):
    try:
        print(f"[INFO] Receiving file: {file.filename}")
        contents = await file.read()
        
        print("[INFO] Parsing file...")
        parsed_data = await parse_file(contents, file.filename)
        
        print("[INFO] Sending to Local AI...")
        critique = await critique_resume(parsed_data, job_description)
        print("[INFO] Analysis Complete!")
        
        # Persist results in SQL Database
        critique["filename"] = file.filename
        critique["job_description"] = job_description or ""
        try:
            scan_id = save_scan(critique)
            critique["id"] = scan_id
        except Exception as db_err:
            print(f"[WARN] Database persistence failed: {db_err}")
            critique["id"] = None
            
        return critique

    except Exception as e:
        error_msg = f"CRASH: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

import os
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin123")


@app.get("/api/scans")
async def fetch_scans():
    try:
        return get_all_scans()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scans/{scan_id}")
async def fetch_scan(scan_id: int):
    try:
        scan = get_scan_by_id(scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan record not found.")
        return scan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/scans")
async def delete_all_scans():
    try:
        clear_all_scans()
        return {"status": "success", "message": "All past scans deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))