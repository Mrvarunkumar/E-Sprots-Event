// ============================================================
//  APEX ARENA — Admin Command Center
//  Connects to FastAPI backend (Supabase-powered) via JWT
// ============================================================

const API_BASE = 'http://127.0.0.1:8000';

let adminToken = sessionStorage.getItem('adminToken') || null;

// ─── ON PAGE LOAD ─────────────────────────────────────────────
window.addEventListener('load', () => {
    if (adminToken) {
        showDashboard();
    }
});

// ─── LOGIN ────────────────────────────────────────────────────
async function login() {
    const user = document.getElementById('username').value.trim();
    const pass = document.getElementById('password').value;

    if (!user || !pass) {
        showLoginError('⚠ Please enter username and password.');
        return;
    }

    const loginBtn = document.getElementById('loginBtn');
    loginBtn.textContent = '⏳  AUTHENTICATING…';
    loginBtn.disabled = true;
    clearLoginError();

    try {
        const res = await fetch(`${API_BASE}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            adminToken = data.access_token;
            sessionStorage.setItem('adminToken', adminToken);
            showDashboard();
        } else {
            showLoginError('✕ ' + (data.detail || 'Invalid credentials.'));
        }
    } catch (err) {
        showLoginError('✕ Cannot connect to server. Make sure the backend is running on port 8000.');
    } finally {
        loginBtn.textContent = '⯈   AUTHENTICATE';
        loginBtn.disabled = false;
    }
}

function showLoginError(msg) {
    const el = document.getElementById('loginError');
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}

function clearLoginError() {
    const el = document.getElementById('loginError');
    if (el) { el.textContent = ''; el.style.display = 'none'; }
}

// ─── SHOW DASHBOARD ───────────────────────────────────────────
function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    loadStats();
    loadTeams();
}

// ─── LOAD STATS (from Supabase via /admin/stats) ──────────────
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/admin/stats`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });

        if (res.status === 401) { logout(); return; }

        const data = await res.json();
        document.getElementById('total').innerText    = data.total_registrations ?? '—';
        document.getElementById('paid').innerText     = data.paid_teams          ?? '—';
        document.getElementById('verified').innerText = data.verified_teams      ?? '—';
        document.getElementById('bgmi-stat').innerText = data.bgmi_count         ?? '—';
        document.getElementById('ff-stat').innerText   = data.freefire_count     ?? '—';
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ─── LOAD TEAMS TABLE (from Supabase via /admin/teams) ────────
async function loadTeams() {
    const tbody = document.getElementById('teamsBody');
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-dim);padding:24px;letter-spacing:3px;font-size:0.8rem;">LOADING…</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/admin/teams?limit=200`, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });

        if (res.status === 401) { logout(); return; }

        const teams = await res.json();

        if (!teams.length) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-dim);padding:32px;letter-spacing:3px;font-size:0.8rem;">NO REGISTRATIONS YET</td></tr>';
            return;
        }

        tbody.innerHTML = teams.map(t => {
            const statusBadge = {
                'verified': `<span class="badge badge-verified">VERIFIED</span>`,
                'paid':     `<span class="badge badge-paid">PAID</span>`,
                'pending':  `<span class="badge badge-unpaid">PENDING</span>`,
                'rejected': `<span class="badge" style="color:#ff4444;border-color:rgba(255,0,0,0.3);">REJECTED</span>`,
            }[t.payment_status] || `<span class="badge badge-unpaid">${t.payment_status.toUpperCase()}</span>`;

            const actionBtn = t.payment_status === 'verified'
                ? `<span style="color:var(--green);font-weight:700;">✓ YES</span>`
                : `<button class="badge badge-unpaid" style="cursor:pointer;background:rgba(255,60,0,0.1);border-color:var(--orange);" onclick="window.location.href='verify.html?teamId=${t.team_id}'">VERIFY</button>`;

            const date = t.created_at
                ? new Date(t.created_at).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })
                : '—';

            return `<tr>
                <td style="color:var(--orange);font-family:var(--font-display);font-size:0.75rem;">${t.team_id}</td>
                <td>${t.game}</td>
                <td>${t.captain_name}</td>
                <td>${t.captain_phone}</td>
                <td>${t.branch} — Sem ${t.semester}</td>
                <td>${statusBadge}</td>
                <td>${actionBtn}</td>
                <td style="color:var(--text-dim);font-size:0.82rem;">${date}</td>
            </tr>`;
        }).join('');

    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#ff4444;padding:24px;letter-spacing:2px;font-size:0.8rem;">FAILED TO LOAD DATA — CHECK SERVER</td></tr>';
        console.error('Teams load error:', err);
    }
}

// ─── VERIFICATION MODAL ───────────────────────────────────────
function openVerificationModal() {
    document.getElementById('phoneSearch').value = '';
    const result = document.getElementById('verifyResult');
    result.style.display = 'none';
    result.className = 'result-box';
    result.textContent = '';
    document.getElementById('verificationModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
    setTimeout(() => document.getElementById('phoneSearch').focus(), 100);
}

function closeVerificationModal(event) {
    // Close only if clicking the backdrop (not the card)
    if (event && event.target !== document.getElementById('verificationModal')) return;
    _hideModal();
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') _hideModal();
});

function _hideModal() {
    document.getElementById('verificationModal').style.display = 'none';
    document.body.style.overflow = '';
}

// ─── VERIFY PAYMENT (Supabase via /admin/verify-payment) ──────
async function verifyPayment() {
    const phone = document.getElementById('phoneSearch').value.trim();
    if (!phone) { alert('Please enter a phone number.'); return; }

    const resultDiv = document.getElementById('verifyResult');
    const verifyBtn = document.getElementById('verifyBtn');

    resultDiv.className = 'result-box';
    resultDiv.textContent = '⏳  Verifying in database…';
    resultDiv.style.display = 'block';
    verifyBtn.disabled = true;
    verifyBtn.textContent = '⏳  VERIFYING…';

    try {
        const res = await fetch(`${API_BASE}/admin/verify-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`
            },
            body: JSON.stringify({ phone })
        });

        if (res.status === 401) { logout(); return; }

        const data = await res.json();

        if (res.ok && data.success) {
            resultDiv.className = 'result-box success';
            resultDiv.textContent = '✓  ' + data.message;
            // Refresh stats and table after verification
            loadStats();
            loadTeams();
        } else {
            resultDiv.className = 'result-box error';
            resultDiv.textContent = '✕  ' + (data.detail || data.message || 'Verification failed.');
        }
    } catch (err) {
        resultDiv.className = 'result-box error';
        resultDiv.textContent = '✕  Network error. Is the backend running?';
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.textContent = '⯈   VERIFY IN DATABASE';
    }
}

let currentExportGame = '';

function openExportModal(game) {
    currentExportGame = game;
    document.getElementById('exportModalTitle').textContent = `Exporting data for ${game.toUpperCase()}`;
    document.getElementById('exportModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeExportModal() {
    document.getElementById('exportModal').style.display = 'none';
    document.body.style.overflow = '';
}

async function confirmExport(format) {
    if (!currentExportGame) return;
    
    // Map 'Free Fire' to 'freefire' for the URL, Hackathon/Quiz lowercase
    const gamePath = currentExportGame.toLowerCase().replace(' ', '');
    const url = `${API_BASE}/export/${format}/${gamePath}`;
    const filename = `${currentExportGame.replace(' ', '')}_Teams.${format === 'excel' ? 'xlsx' : 'pdf'}`;
    
    await _downloadExport(url, filename);
    closeExportModal();
}

async function _downloadExport(url, fallbackName) {
    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${adminToken}` }
        });

        if (res.status === 401) { logout(); return; }
        if (!res.ok) { alert('Export failed — server returned ' + res.status); return; }

        const blob = await res.blob();
        const disposition = res.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^";\n]+)"?/);
        const filename = match ? match[1] : fallbackName;

        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    } catch (err) {
        alert('Export failed: ' + err.message);
    }
}

// ─── LOGOUT ──────────────────────────────────────────────────
function logout() {
    adminToken = null;
    sessionStorage.removeItem('adminToken');
    _hideModal();
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    clearLoginError();
}