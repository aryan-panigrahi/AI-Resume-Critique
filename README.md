# 🚀 Local AI Resume Critiquer (Privacy-Focused)

A powerful, full-stack application that uses **Local LLMs (Llama 3.1)** and **OCR (Tesseract)** to analyze resumes against job descriptions. It runs entirely on your machine—**no data ever leaves your computer.**

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![AI Model](https://img.shields.io/badge/AI-Llama_3.1-purple)
![Privacy](https://img.shields.io/badge/Privacy-100%25_Local-green)

## ✨ Key Features

* **🧠 Deep AI Analysis:** Uses **Llama 3.1** via Ollama to "think" like a ruthless technical recruiter.
* **👁️ Optical Character Recognition (OCR):** Supports **PDF, DOCX, JPG, and PNG**. It can read screenshots of resumes.
* **🔒 100% Privacy:** Runs on `localhost`. Your personal data never touches the cloud.
* **🎯 "Ruthless Mode":** Detects critical skill gaps. If you miss mandatory hard skills (e.g., "Kubernetes"), it crushes the score to <15/100.
* **📊 Visual Dashboard:**
    * **Skill Badges:** Green (Matched) vs. Red (Missing) pills for instant feedback.
    * **History Sidebar:** Saves previous scans for easy comparison.
* **📄 PDF Export:** Download a professional critique report with one click.
* **🔍 Visual Debugger:** View the raw text exactly as the AI saw it (great for debugging OCR errors).

## 🛠️ Tech Stack

* **Backend:** Python (FastAPI), Uvicorn
* **AI Engine:** Ollama (Llama 3.1)
* **OCR Engine:** Tesseract (pytesseract)
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Libraries:** `pdf2image`, `python-docx`, `html2pdf.js`

## 🚀 Quick Start

### Prerequisites
1.  **Python 3.9+** installed.
2.  **Ollama** installed and running with at least one local LLM downloaded (e.g., `llama3.1` or `qwen3:8b`).
3.  **Tesseract OCR** installed for image/OCR support (Windows/Linux/Mac).

### Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/ai-resume-critiquer.git
    cd ai-resume-critiquer
    ```

2.  **Setup Virtual Environment & Dependencies:**
    * **Windows (Automated):** Simply double-click `run_app.bat`! It will automatically create a local virtual environment (`.venv`), install the necessary requirements (including `python-multipart`), check your Ollama status, and boot the server.
    * **Manual Setup:**
        ```bash
        # Create virtual environment
        python -m venv .venv
        
        # Activate environment
        # Windows:
        .venv\Scripts\activate
        # macOS/Linux:
        source .venv/bin/activate

        # Install dependencies
        pip install -r requirements.txt python-multipart
        ```

3.  **Run the App:**
    * **Windows:** Double-click `run_app.bat`.
    * **Manual:**
        ```bash
        .venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
        ```

4.  **Open Browser:**
    Go to `http://127.0.0.1:8000`

> [!NOTE]
> **Dynamic LLM Fallback:** The backend is configured to search for `llama3.1` in your local Ollama registry on startup. If not found, it automatically falls back to your first available local model (such as `qwen3:8b`) to prevent server crashes.

## 🤝 Contributing

1.  Fork the repository.
2.  Create a Feature Branch (`git checkout -b feature/NewFeature`).
3.  Commit your changes (`git commit -m 'Add some NewFeature'`).
4.  Push to the Branch (`git push origin feature/NewFeature`).
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

