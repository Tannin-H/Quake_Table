// Function to send movement data on button click
async function sendMovementData() {
    try {
        const response = await fetch('/start-movement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();
        document.getElementById('response').innerText =
            result.status === "success" ? `Response: ${result.response}` : `Error: ${result.message}`;
    } catch (error) {
        document.getElementById('response').innerText = `Error: ${error.message}`;
    }
}

// Attach event listener to the button
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('sendDataButton');
    if (button) { // Check if button exists
        button.addEventListener('click', sendMovementData);
    } else {
        console.error("Button not found!");
    }
});
