import os
import numpy as np
from flask import Flask, jsonify, render_template
from main import send_movement_data, open_connection

app = Flask(__name__)

# Global connection object
arduino_connection = None

def setup_connection():
    global arduino_connection
    arduino_connection = open_connection()

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/start-movement', methods=['POST'])
def start_movement():
    try:
        print("Starting movement")
        # Send data using the pre-opened connection
        response = send_movement_data(arduino_connection)
        print(response)
        return
    except Exception as e:
        print("Error")
        return

@app.route('/data')
def get_data():
    # Generate initial data points (5 seconds worth at 10 points per second)
    points_per_second = 10
    total_points = 5 * points_per_second
    x = np.linspace(0, 5, total_points)
    y = np.sin(2 * np.pi * 0.5 * x)  # 0.5 Hz sine wave

    return jsonify({
        'x': x.tolist(),
        'y': y.tolist(),
        'pointsPerSecond': points_per_second
    })

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':  # True only for the second run in debug mode
        setup_connection()
    app.run(debug=True)
