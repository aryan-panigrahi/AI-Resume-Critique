// --- THEME HANDLING ---
function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
}

window.onload = function () {
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
    }
    // Only load results if we are actually on the result page
    if (window.location.pathname.includes("result.html")) {
        loadCurrentResult();
        renderHistorySidebar();
    }
};

// --- HISTORY SYSTEM ---
function saveToHistory(data) {
    let history = JSON.parse(localStorage.getItem("scanHistory") || "[]");
    
    const newItem = {
        id: Date.now(),
        name: data.candidate_name || "Unknown",
        score: data.overall_score || 0,
        timestamp: new Date().toLocaleTimeString(),
        fullData: data 
    };

    // Add to top, keep max 10
    history.unshift(newItem);
    if (history.length > 10) history.pop(); 

    localStorage.setItem("scanHistory", JSON.stringify(history));
    localStorage.setItem("currentScan", JSON.stringify(data));
}

function loadFromHistory(id) {
    let history = JSON.parse(localStorage.getItem("scanHistory") || "[]");
    const item = history.find(x => x.id === id);
    if (item) {
        localStorage.setItem("currentScan", JSON.stringify(item.fullData));
        window.location.reload(); 
    }
}

function loadCurrentResult() {
    const dataStr = localStorage.getItem("currentScan");
    if (!dataStr) return; 
    renderResults(JSON.parse(dataStr));
}

function renderHistorySidebar() {
    const list = document.getElementById("historyList");
    if (!list) return;

    let history = JSON.parse(localStorage.getItem("scanHistory") || "[]");
    list.innerHTML = "";

    if (history.length === 0) {
        list.innerHTML = '<p style="color:#94a3b8; font-size: 0.9rem; padding:10px;">No history yet.</p>';
        return;
    }

    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        
        // Color code the mini-score in sidebar
        const scoreColor = item.score < 50 ? "#ef4444" : (item.score >= 80 ? "#22c55e" : "#f59e0b");
        
        div.innerHTML = `
            <div style="font-weight:bold;">${item.name}</div>
            <div style="font-size: 0.85rem; color: #64748b; display: flex; justify-content: space-between;">
                <span>${item.timestamp}</span>
                <span style="color: ${scoreColor}; font-weight:bold;">${item.score}/100</span>
            </div>
        `;
        div.onclick = () => loadFromHistory(item.id);
        list.appendChild(div);
    });
}

// --- DEBUG & PDF ---
function toggleDebug() {
    const modal = document.getElementById("debugModal");
    const content = document.getElementById("rawTextContent");
    
    if (modal.style.display === "block") {
        modal.style.display = "none";
    } else {
        const data = JSON.parse(localStorage.getItem("currentScan") || "{}");
        content.innerText = data.raw_text || "No raw text found. (Run a new scan to see data)";
        modal.style.display = "block";
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById("debugModal");
    if (event.target == modal) modal.style.display = "none";
}

function downloadPDF() {
    const element = document.querySelector(".content"); 
    const name = document.getElementById("candidateName").innerText || "Resume_Analysis";
    
    const opt = {
      margin: [0.5, 0.5],
      filename: `${name}_Critique.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    // Hide buttons during PDF generation
    const buttons = document.querySelectorAll("button, .btn-nav");
    buttons.forEach(b => b.style.display = 'none');
    
    html2pdf().set(opt).from(element).save().then(() => {
        buttons.forEach(b => b.style.display = '');
    });
}

// --- UPLOAD & ANALYZE ---
async function uploadAndAnalyze() {
    const fileInput = document.getElementById("resumeInput");
    const jobDescInput = document.getElementById("jobDesc");
    const file = fileInput.files[0];

    if (!file) return alert("Please select a file first!");

    const btn = document.querySelector(".btn");
    const stepsContainer = document.getElementById("thinkingSteps");
    
    // UI Loading State
    btn.disabled = true;
    btn.innerText = "Analyzing...";
    stepsContainer.style.display = "block";
    
    // Reset steps
    [1, 2, 3, 4].forEach(i => {
        const el = document.getElementById(`step${i}`);
        if(el) el.className = "step-item pending";
    });

    const updateStep = (step, status) => {
        const el = document.getElementById(`step${step}`);
        if(el) el.className = `step-item ${status}`;
    };

    // Fake progress animation
    updateStep(1, "active");
    const timers = [];
    timers.push(setTimeout(() => { updateStep(1, "done"); updateStep(2, "active"); }, 2500));
    timers.push(setTimeout(() => { updateStep(2, "done"); updateStep(3, "active"); }, 5000));
    timers.push(setTimeout(() => { updateStep(3, "done"); updateStep(4, "active"); }, 12000));

    const formData = new FormData();
    formData.append("file", file);
    const jdText = jobDescInput ? jobDescInput.value.trim() : "";
    if (jdText) formData.append("job_description", jdText);

    try {
        // Call Backend
        const response = await fetch("http://127.0.0.1:8000/analyze", { 
            method: "POST", 
            body: formData 
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server Error");
        }

        const data = await response.json();
        
        // Finish Animation
        timers.forEach(clearTimeout);
        [1, 2, 3, 4].forEach(i => updateStep(i, "done"));
        
        // Redirect
        setTimeout(() => {
            saveToHistory(data);
            window.location.href = "result.html";
        }, 1000);

    } catch (error) {
        console.error(error);
        alert("Analysis Failed:\n" + error.message);
        btn.disabled = false;
        btn.innerText = "Analyze with AI";
        stepsContainer.style.display = "none";
    }
}

// --- RENDER RESULTS (THE FIXED SECTION) ---
function renderResults(data) {
    const score = (typeof data.overall_score === 'number') ? data.overall_score : 50;
    const name = data.candidate_name || "Candidate";

    // 1. Basic Info
    const nameEl = document.getElementById("candidateName");
    if(nameEl) nameEl.innerText = name;
    
    const scoreValEl = document.getElementById("scoreVal");
    if(scoreValEl) scoreValEl.innerText = score;
    
    // Animate Score Bar with Color Logic
    setTimeout(() => {
        const fill = document.getElementById("scoreFill");
        if(fill) {
            fill.style.width = score + "%";
            if(score >= 80) fill.style.background = "#16a34a"; // Green
            else if(score >= 50) fill.style.background = "#ca8a04"; // Yellow
            else fill.style.background = "#dc2626"; // Red
        }
    }, 200);

    const summaryEl = document.getElementById("summaryText");
    if(summaryEl) summaryEl.innerText = data.summary || "No summary provided.";

    // 2. Badges Helper
    const renderBadges = (elementId, items, type) => {
        const list = document.getElementById(elementId);
        if(!list) return;
        
        list.innerHTML = "";
        list.className = "badge-container"; 

        if (!items || items.length === 0) {
            list.innerHTML = "<p style='color:#94a3b8; width:100%;'>No specific points found.</p>";
            return;
        }

        items.forEach(item => {
            const badge = document.createElement("div");
            // Remove the internal python flag if present
            const cleanText = item.replace("MISSING:", "").trim();
            
            if (type === 'weakness' || item.includes("MISSING:")) {
                badge.className = "skill-badge error"; // Styling for bad
                badge.innerHTML = `❌ ${cleanText}`;
            } else {
                badge.className = "skill-badge success"; // Styling for good
                badge.innerHTML = `✅ ${cleanText}`;
            }
            list.appendChild(badge);
        });
    };

    renderBadges("strengthsList", data.strengths, 'strength');
    renderBadges("weaknessesList", data.weaknesses, 'weakness');

    // 3. IMPROVEMENTS (FIXED KEYS + DUAL CARD STYLE)
    const impList = document.getElementById("improvementsList");
    if(impList) {
        impList.innerHTML = "";
        
        if (data.improvements && data.improvements.length > 0) {
            data.improvements.forEach(imp => {
                // FIXED KEYS: .original, .better, .why (Matching Python)
                const original = imp.original || ""; 
                const better = imp.better || imp; 
                const why = imp.why || "";

                // Detect Card Type
                const isGeneral = !original || 
                                  original.toLowerCase().includes("general") || 
                                  original.toLowerCase().includes("feedback");

                const card = document.createElement("div");

                if (isGeneral) {
                    // BLUE CARD (General Tip)
                    card.className = "general-card";
                    card.innerHTML = `
                        <div class="general-icon">💡</div>
                        <div class="general-content">
                            <h4>General Advice</h4>
                            <p>${better}</p>
                            ${why ? `<p style="font-size:0.85rem; margin-top:5px; opacity:0.7;"><em>Why: ${why}</em></p>` : ''}
                        </div>
                    `;
                } else {
                    // RED/GREEN CARD (Specific Rewrite)
                    card.className = "rewrite-card";
                    card.innerHTML = `
                        <div class="rewrite-original">
                            <strong>❌ Original:</strong> "${original}"
                        </div>
                        <div class="rewrite-better">
                            <strong>✅ Better:</strong> "${better}"
                        </div>
                        <div class="rewrite-why">
                            <span>💡 <em>${why || "To improve clarity and impact."}</em></span>
                        </div>
                    `;
                }
                impList.appendChild(card);
            });
        } else {
            impList.innerHTML = "<p style='color:#94a3b8;'>No specific suggestions generated.</p>";
        }
    }
}