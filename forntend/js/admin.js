// Admin Login
function login() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;

    if(user === "admin" && pass === "admin123") {
        document.getElementById("loginPage").style.display = "none";
        document.getElementById("dashboard").style.display = "block";
        loadStats();
    } else {
        alert("Invalid Login");
    }
}

// Load Dashboard Stats (from FastAPI later)
function loadStats() {
    // Replace with API call
    document.getElementById("total").innerText = 120;
    document.getElementById("paid").innerText = 95;
    document.getElementById("verified").innerText = 80;
}

// Open Verification Page
function openVerification() {
    document.getElementById("dashboard").style.display = "none";
    document.getElementById("verificationPage").style.display = "block";
}

// Verify Payment
function verifyPayment() {
    const phone = document.getElementById("phoneSearch").value;
    alert("Payment Verified for " + phone);

    // Call FastAPI here later
}

// Export Excel
function exportBGMI() {
    window.location.href = "http://127.0.0.1:8000/export/bgmi";
}

function exportFF() {
    window.location.href = "http://127.0.0.1:8000/export/freefire";
}

// View Registrations
function viewRegistrations() {
    window.location.href = "registrations.html";
}

// Back Button
function goBack() {
    document.getElementById("verificationPage").style.display = "none";
    document.getElementById("dashboard").style.display = "block";
}