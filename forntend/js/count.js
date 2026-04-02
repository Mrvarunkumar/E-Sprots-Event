// Get registrations from localStorage
function updateCounts() {
    let freefireTeams = JSON.parse(localStorage.getItem("freefireTeams")) || [];
    let bgmiTeams = JSON.parse(localStorage.getItem("bgmiTeams")) || [];

    document.getElementById("freefire-count").innerText = freefireTeams.length;
    document.getElementById("bgmi-count").innerText = bgmiTeams.length;
}

// Run when page loads
updateCounts();