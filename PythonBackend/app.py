import os
import numpy as np
from flask import Flask, jsonify, render_template, request
from main import *

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
        print("Starting Simulation")
        # Send data using the pre-opened connection
        command_batch = request.get_json().get('commands')
        response = send_movement_data(arduino_connection, command_batch)
        print(response)
        return response, 200
    except Exception as e:
        print("Error sending movement data " + str(e))
        return

@app.route('/start-manual', methods=['POST'])
def start_manual():
    try:
        print("Starting Manual Controlled Movement")

        # Get JSON data from request
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        # Extract parameters from the received JSON
        speed = data.get('speed', 0)  # Default to 0 if not provided
        displacement = data.get('displacement', 0)  # Default to 'unknown' if not provided

        print(speed, displacement)
        # Call your function with the received parameters
        response = run_manual_routine(arduino_connection, speed, displacement)

        print(response)
        return jsonify({"message": "Manual routine started", "response": response}), 200
    except Exception as e:
        print("Error running manual routine: " + str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/stop-movement', methods=['POST'])
def stop_movement():
    try:
        print("Sending stop movement command")
        response = stop_table(arduino_connection)
        print(response)
        return response, 200
    except Exception as e:
        print("Error stopping table " + str(e))
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
