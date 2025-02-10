// Global state
const state = {
    chart: null,
    animation: {
        frame: null,
        startTime: null,
        pauseTime: null,
        isPaused: false,
        pointsPerSecond: 20,
        windowDuration: 10,
        dampingPercentage: 50,
        timeStep: 0.01
    },
    sliders: {
        freq: 0,
        disp: 0,
        waveGenDisp: 0,
        gs: 0,
        ga: 0,
        simDuration: 5  // Default to 5 seconds
    },
    constants: {
        stepsPerMm: 400 / 5, // 400 steps = 5mm
        defaultAcceleration: 1000
    }
};

// Chart configuration
const chartConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Signal',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.3,
                pointRadius: 0
            },
            {
                label: 'Dot',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                pointRadius: 5,
                pointBackgroundColor: 'rgb(255, 99, 132)',
                showLine: false
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
            x: {
                type: 'linear',
                title: { display: true, text: 'Time (seconds)' },
                min: 0,
                max: 5 // Initial window duration
            },
            y: {
                title: { display: true, text: 'Amplitude' },
                suggestedMin: -1,
                suggestedMax: 1
            }
        },
        plugins: { legend: { display: false } }
    }
};

// API calls
const api = {
    async sendRequest(endpoint, method, data = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };
            if (data) options.body = JSON.stringify(data);

            const response = await fetch(endpoint, options);
            const result = await response.text();
            document.getElementById('response').innerText = `Response: ${result}`;
            return result;
        } catch (error) {
            document.getElementById('response').innerText = `Error: ${error.message}`;
            throw error;
        }
    },

    convertWaveformToCommands(yData) {
        const commands = [];
        let previousPosition = 0;
        const { stepsPerMm, defaultAcceleration } = state.constants;

        for (let i = 1; i < yData.length; i += 2) { // Skip every other point (downsampling)
            const positionDiff = yData[i] - previousPosition;
            const steps = Math.round(positionDiff * stepsPerMm);

            if (Math.abs(steps) < 79) continue; // Skip very small movements

            const direction = steps > 0 ? 1 : 0;
            const speed = Math.max(1000, Math.round(state.sliders.gs * 1000));

            commands.push(`MOVE ${speed} ${defaultAcceleration} ${Math.abs(steps)} ${direction}`);
            previousPosition = yData[i];
        }

        return commands;
    },

    async startMovement() {
        const numPoints = Math.round(state.sliders.simDuration * state.animation.pointsPerSecond);
        const lambda = -Math.log(1 - state.animation.dampingPercentage / 100) / Math.max(0.1, state.sliders.simDuration);

        const { yData } = chartFunctions.calculateWaveformData(numPoints, 0, lambda, state.sliders);
        const commands = this.convertWaveformToCommands(yData);

        const data = {
            commands: commands,
            parameters: {
                gs: state.sliders.gs,
                ga: state.sliders.ga,
                simulationDuration: state.sliders.simDuration
            }
        };

        return await api.sendRequest('/start-movement', 'POST', data);
    },

    stopMovement() {
        return api.sendRequest('/stop-movement', 'POST');
    },

    sendManual() {
        return api.sendRequest('/start-manual', 'POST', {
            speed: state.sliders.freq,
            displacement: state.sliders.disp
        });
    }
};

// Slider handling
class SliderHandler {
    static setupSlider(id, valueId, stateKey) {
        const slider = document.querySelector(`#${id}`);
        const valueElement = document.querySelector(`#${valueId}`);

        if (!slider || !valueElement) return;

        // Set initial value
        state.sliders[stateKey] = parseFloat(slider.value);
        valueElement.textContent = slider.value;

        slider.addEventListener('input', (event) => {
            const value = parseFloat(event.target.value);
            state.sliders[stateKey] = value;
            valueElement.textContent = value;

            const progress = (value / slider.max) * 100;
            slider.style.background = `linear-gradient(to right, #f50 ${progress}%, #ccc ${progress}%)`;

            // Update scale when wave displacement changes
            if (id === 'waveGenDispRange') {
                chartFunctions.updateScale();
            }
        });
    }
}

// Chart functions
const chartFunctions = {
    init() {
        const ctx = document.getElementById('myChart')?.getContext('2d');
        if (!ctx) {
            console.error('Could not find chart canvas element');
            return;
        }

        // Clear any existing chart
        if (state.chart) {
            state.chart.destroy();
        }

        state.chart = new Chart(ctx, chartConfig);
        console.log('Chart initialized:', state.chart);
    },

    updateScale() {
        if (!state.chart) return;

        // Calculate the maximum possible amplitude based on wave displacement
        const maxAmplitude = state.sliders.waveGenDisp * 1.2; // Add 20% margin

        // Update the chart scales
        state.chart.options.scales.y.suggestedMin = -maxAmplitude;
        state.chart.options.scales.y.suggestedMax = maxAmplitude;

        // If there's no animation running, update the chart
        if (!state.animation.frame) {
            state.chart.update('none');
        }
    },

    update(timestamp) {
        const { animation, sliders, chart } = state;
        if (!chart) {
            console.error('Chart not initialized');
            return;
        }

        if (!animation.startTime) {
            animation.startTime = timestamp;
        }

        if (animation.isPaused) {
            if (!animation.pauseTime) animation.pauseTime = timestamp;
            return;
        }

        if (animation.pauseTime) {
            animation.startTime += timestamp - animation.pauseTime;
            animation.pauseTime = null;
        }

        const elapsedSeconds = (timestamp - animation.startTime) / 1000;

        // Update time display
        const timeDisplay = document.getElementById('timeDisplay');
        if (timeDisplay) {
            timeDisplay.textContent = `Time: ${elapsedSeconds.toFixed(2)}s`;
        }

        // Check duration
        if (elapsedSeconds > sliders.simDuration) {
            chartFunctions.stop();
            return;
        }

        const numPoints = sliders.simDuration * animation.pointsPerSecond;
        const lambda = -Math.log(1 - animation.dampingPercentage / 100) / Math.max(0.1, sliders.simDuration);

        const { xData, yData } = chartFunctions.calculateWaveformData(
            numPoints,
            elapsedSeconds,
            lambda,
            sliders
        );

        // Update chart data
        chart.data.labels = xData;
        chart.data.datasets[0].data = yData;

        // Update dot position
        const dotIndex = Math.floor(elapsedSeconds * animation.pointsPerSecond);
        const dotData = new Array(numPoints).fill(null);
        dotData[dotIndex] = yData[dotIndex];
        chart.data.datasets[1].data = dotData;

        // Center the viewport on the dot only after it reaches the center
        const dotPosition = elapsedSeconds; // Current time is the dot's position
        const halfWindow = animation.windowDuration / 2; // Half the window duration

        let minX = chart.options.scales.x.min || 0; // Default to 0 if not set
        let maxX = chart.options.scales.x.max || animation.windowDuration; // Default to windowDuration if not set

        // Check if the dot has reached the center of the viewport
        if (dotPosition >= halfWindow && dotPosition <= sliders.simDuration - halfWindow) {
            // Start scrolling to keep the dot centered
            minX = dotPosition - halfWindow;
            maxX = dotPosition + halfWindow;
        } else if (dotPosition > sliders.simDuration - halfWindow) {
            // Stop scrolling at the end of the simulation
            minX = sliders.simDuration - animation.windowDuration;
            maxX = sliders.simDuration;
        }

        // Update the chart scales
        chart.options.scales.x.min = minX;
        chart.options.scales.x.max = maxX;

        chart.update('none');

        animation.frame = requestAnimationFrame(chartFunctions.update);
    },

    calculateWaveformData(numPoints, elapsedSeconds, lambda, sliders) {
        const xData = new Array(numPoints);
        const yData = new Array(numPoints);

        for (let i = 0; i < numPoints; i++) {
            const x = i / state.animation.pointsPerSecond;
            xData[i] = x;

            if (x < 0 || x > sliders.simDuration) {
                yData[i] = 0;
            } else {
                yData[i] = sliders.waveGenDisp *
                          Math.exp(-lambda * x) *
                          Math.cos(2 * Math.PI * sliders.gs * x);
            }
        }

        return { xData, yData };
    },

    start() {
        console.log('Starting animation...');
        const { animation } = state;
        if (animation.isPaused) {
            animation.isPaused = false;
        } else {
            animation.startTime = null;
            animation.isPaused = false;
        }
        animation.frame = requestAnimationFrame(chartFunctions.update);
    },

    stop() {
        if (state.animation.frame) {
            cancelAnimationFrame(state.animation.frame);
            state.animation.frame = null;
        }
    },

    pause() {
        state.animation.isPaused = true;
        state.animation.pauseTime = null;
    },

    reset() {
        chartFunctions.stop();
        state.animation.startTime = null;
        state.animation.pauseTime = null;
        state.animation.isPaused = false;
        document.getElementById('timeDisplay').textContent = 'Time: 0.00s';
        chartFunctions.init();
    }
};

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Initialize chart
    chartFunctions.init();
    console.log('DOM Content Loaded, chart initialized');

    // Setup all sliders
    const sliderConfigs = [
        ['freqRange', 'freqVal', 'freq'],
        ['dispRange', 'dispVal', 'disp'],
        ['waveGenDispRange', 'waveGenDispVal', 'waveGenDisp'],
        ['GsRange', 'GsVal', 'gs'],
        ['GaRange', 'GaVal', 'ga'],
        ['SimDurationRange', 'SimDurationVal', 'simDuration']
    ];

    sliderConfigs.forEach(([id, valueId, stateKey]) => {
        SliderHandler.setupSlider(id, valueId, stateKey);
    });

    // Setup button listeners
    const buttonConfigs = [
        ['sendDataButton', async () => {
            try {
                console.log('Sending data...');
                chartFunctions.start()
                await api.startMovement();
            } catch (error) {
                console.error('Error starting movement:', error);
            }
        }],
        ['stopSimulationButton', () => {
            api.stopMovement();
            chartFunctions.stop();
        }],
        ['sendManualButton', api.sendManual],
    ];

    buttonConfigs.forEach(([id, handler]) => {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', handler);
        } else {
            console.error(`Button with id ${id} not found`);
        }
    });
});