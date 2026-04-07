// ============================================================
//  Apex Arena — verify.html API helper
//  Wraps all fetch calls with the stored JWT token
// ============================================================

const API_BASE = 'http://127.0.0.1:8000';

/**
 * Authenticated fetch helper.
 * Reads JWT from sessionStorage, sends as Bearer token.
 * Throws on non-OK responses with the server's detail message.
 */
async function apiFetch(path, options = {}) {
    const token = sessionStorage.getItem('apex_token');
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers || {}),
    };

    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
    });

    if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
            const body = await res.json();
            detail = body.detail || body.message || detail;
        } catch (_) {}
        throw new Error(detail.toString().toUpperCase());
    }

    // For 204 No Content responses
    if (res.status === 204) return null;

    return res.json();
}
