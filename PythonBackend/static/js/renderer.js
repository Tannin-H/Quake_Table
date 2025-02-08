let chart;
let animationFrame;
let startTime = null;
let pauseTime = null;
let isPaused = false;
let pointsPerSecond;
let windowDuration = 5; // Show 5 seconds of data at a time

// Function to send movement data on button click
async function sendMovementData() {
    try {
        const response = await fetch('/start-movement', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            }
        });
        const result = await response.text();
        document.getElementById('response').innerText = `Response: ${result}`;
    } catch (error) {
        document.getElementById('response').innerText = `Error: ${error.message}`;
    }
}

// Function to stop the table and reset to home position
async function stopMovement() {
    try {
        const response = await fetch('/stop-movement', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            }
        });
        const result = await response.text();
        document.getElementById('response').innerText = `Response: ${result}`;
    } catch (error) {
        document.getElementById('response').innerText = `Error: ${error.message}`;
    }
}

// Attach event listener to the send data button
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('sendDataButton');
    if (button) { // Check if button exists
        button.addEventListener('click', sendMovementData);
    } else {
        console.error("Button not found!");
    }
});

// Attach event listener to the stop movement button
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('stopSimulationButton');
    if (button) { // Check if button exists
        button.addEventListener('click', stopMovement);
    } else {
        console.error("Button not found!");
    }
});

const freqSlider = document.querySelector("#freqRange")
const freqSliderValue = document.querySelector("#freqVal")

freqSlider.addEventListener("input", (event) => {
  const tempSliderValue = event.target.value;
  freqSliderValue.textContent = tempSliderValue;

  const progress = (tempSliderValue / freqSlider.max) * 100;

  freqSlider.style.background = `linear-gradient(to right, #f50 ${progress}%, #ccc ${progress}%)`;
});

const dispSlider = document.querySelector("#dispRange")
const dispSliderValue = document.querySelector("#dispVal")

dispSlider.addEventListener("input", (event) => {
  const tempSliderValue = event.target.value;
  dispSliderValue.textContent = tempSliderValue;

  const progress = (tempSliderValue / dispSlider.max) * 100;

  dispSlider.style.background = `linear-gradient(to right, #f50 ${progress}%, #ccc ${progress}%)`;
});

async function initChart() {
    const response = await fetch('/data');
    const data = await response.json();
    pointsPerSecond = data.pointsPerSecond;

    const ctx = document.getElementById('myChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.x,
            datasets: [{
                label: 'Signal',
                data: data.y,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.3,
                pointRadius: 0
            }]
        },
        options: {
            animation: false,
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    }
                },
                y: {
                    min: -1.5,
                    max: 1.5,
                    title: {
                        display: true,
                        text: 'Amplitude'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function updateGraph(timestamp) {
    if (!startTime) startTime = timestamp;
    if (isPaused) {
        if (!pauseTime) pauseTime = timestamp;
        return;
    }

    if (pauseTime) {
        startTime += timestamp - pauseTime;
        pauseTime = null;
    }

    const elapsedSeconds = (timestamp - startTime) / 1000;
    document.getElementById('timeDisplay').textContent = `Time: ${elapsedSeconds.toFixed(2)}s`;

    // Calculate new data points
    const numPoints = windowDuration * pointsPerSecond;
    const xData = new Array(numPoints);
    const yData = new Array(numPoints);

    for (let i = 0; i < numPoints; i++) {
        const x = elapsedSeconds + (i - numPoints) / pointsPerSecond;
        xData[i] = x;
        yData[i] = Math.sin(2 * Math.PI * 0.5 * x); // 0.5 Hz sine wave
    }

    // Update chart data
    chart.data.labels = xData;
    chart.data.datasets[0].data = yData;
    chart.options.scales.x.min = elapsedSeconds - windowDuration;
    chart.options.scales.x.max = elapsedSeconds;
    chart.update();

    animationFrame = requestAnimationFrame(updateGraph);
}

function startAnimation() {
    if (isPaused) {
        isPaused = false;
        animationFrame = requestAnimationFrame(updateGraph);
    } else {
        startTime = null;
        isPaused = false;
        animationFrame = requestAnimationFrame(updateGraph);
    }
}

function pauseAnimation() {
    isPaused = true;
    pauseTime = null;
}

function resetAnimation() {
    cancelAnimationFrame(animationFrame);
    startTime = null;
    pauseTime = null;
    isPaused = false;
    document.getElementById('timeDisplay').textContent = 'Time: 0.00s';
    initChart();
}

// Initialize the chart when the page loads
document.addEventListener('DOMContentLoaded', initChart);