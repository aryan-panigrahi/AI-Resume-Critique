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
2.  **Ollama** installed and running (`ollama run llama3.1`).
3.  **Tesseract OCR** installed (Windows/Linux/Mac).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/ai-resume-critiquer.git](https://github.com/YOUR_USERNAME/ai-resume-critiquer.git)
    cd ai-resume-critiquer
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install fastapi uvicorn python-multipart python-docx ollama pytesseract pdf2image aiofiles
    ```

3.  **Run the App:**
    * **Windows:** Double-click `run_app.bat`.
    * **Manual:**
        ```bash
        uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
        ```

4.  **Open Browser:**
    Go to `http://127.0.0.1:8000`

## 🤝 Contributing

1.  Fork the repository.
2.  Create a Feature Branch (`git checkout -b feature/NewFeature`).
3.  Commit your changes (`git commit -m 'Add some NewFeature'`).
4.  Push to the Branch (`git push origin feature/NewFeature`).
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

