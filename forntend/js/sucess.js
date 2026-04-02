// Get Team ID from URL
const urlParams = new URLSearchParams(window.location.search);
const teamId = urlParams.get('teamId');

if(teamId){
    document.getElementById("teamId").innerText = teamId;
}

// Download PDF
function downloadPDF() {
    window.location.href = "http://127.0.0.1:8000/download-pdf?teamId=" + teamId;
}

// Back to Home
function goHome() {
    window.location.href = "index.html";
}

// Auto download PDF after 3 seconds
setTimeout(() => {
    if(teamId){
        downloadPDF();
    }
}, 3000);