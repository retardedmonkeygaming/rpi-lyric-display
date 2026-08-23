// Add these updated functions into your editor.html script block

async function runSentimentAnalysis() {
    const statusEl = document.getElementById('sentiment-status');
    const emojiEl = document.getElementById('mood-emoji');
    
    statusEl.innerText = "Analyzing...";
    
    try {
        const res = await fetch(`/api/songs/${songId}/analyze-sentiment`);
        const data = await res.json();
        
        if (data.status === 'success') {
            // This now shows the real mood: HYPE, SAD, etc.
            statusEl.innerText = `Mood: ${data.suggested_mood} (Confident)`;
            statusEl.style.color = "#00ff66";
            emojiEl.innerText = "✅"; 
        }
    } catch (e) {
        statusEl.innerText = "Error analyzing.";
    }
}

async function applyEmojiToAllLines() {
    if(!confirm("Apply hardware icons to all matching lines?")) return;
    
    try {
        const res = await fetch(`/api/songs/${songId}/auto-emoji-lines`, { method: 'POST' });
        if (res.ok) {
            alert("Hardware icons injected! Refreshing page...");
            location.reload(); // Refresh to show the \x01 characters in the inputs
        }
    } catch (e) {
        alert("Failed to update.");
    }
}