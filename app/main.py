from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.parser import parse_file
from app.ai_service import critique_resume
import traceback

app = FastAPI(title="AI Resume Critiquer API")

# Allow CORS so your local HTML file can talk to this local server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "running"}

@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...), 
    job_description: str = Form(None)
):
    try:
        print(f"📂 Receiving file: {file.filename}")
        contents = await file.read()
        
        print("⚙️ Parsing file...")
        parsed_data = await parse_file(contents, file.filename)
        
        print("🤖 Sending to Local AI...")
        critique = await critique_resume(parsed_data, job_description)
        print("✅ Analysis Complete!")
        
        return critique

    except Exception as e:
        error_msg = f"CRASH: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)