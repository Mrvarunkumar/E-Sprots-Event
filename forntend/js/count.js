// ============================================================
//  Apex Arena — Event Count JS
//  Fetches real-time registration counts from /api/counts
// ============================================================

const API_BASE = 'http://127.0.0.1:8000';

async function updateCounts() {
    try {
        const res = await fetch(`${API_BASE}/api/counts`);

        if (!res.ok) {
            console.error('Failed to fetch counts:', res.status);
            return;
        }

        const data = await res.json();

        const ffEl   = document.getElementById('freefire-count');
        const bgmiEl = document.getElementById('bgmi-count');
        const hackathonEl = document.getElementById('hackathon-count');
        const quizEl = document.getElementById('quiz-count');

        if (ffEl)   ffEl.innerText   = data.freefire_count ?? 0;
        if (bgmiEl) bgmiEl.innerText = data.bgmi_count     ?? 0;
        if (hackathonEl) hackathonEl.innerText = data.hackathon_count ?? 0;
        if (quizEl) quizEl.innerText = data.quiz_count ?? 0;

    } catch (err) {
        console.error('Could not load registration counts:', err);
    }
}

// Run on load
updateCounts();