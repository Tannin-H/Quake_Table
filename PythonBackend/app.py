# app.py
import os
import queue
import time

import numpy as np
from flask_cors import CORS
from flask import Flask, jsonify, render_template, request, Response
from main import PicoConnectionManager

app = Flask(__name__)
pico_manager = PicoConnectionManager()
message_queue = queue.Queue()
CORS(app)

def trigger_alert(message):
    """Add an error message to the SSE queue."""
    message_queue.put(('error', message))

def setup_connection():
    """Open the connection to the microcontroller."""
    try:
        print(pico_manager.open_connection())
        # Send "connected" status
        message_queue.put(('status', 'connected'))
    except Exception as e:
        error_msg = f"Failed to open connection: {str(e)}"
        print(error_msg)
        # Send "disconnected" status
        message_queue.put(('status', 'disconnected'))
        message_queue.put(('error', error_msg))

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stream')
def stream():
    def event_stream():
        while True:
            try:
                message_type, message = message_queue.get(timeout=1)
                yield f"event: {message_type}\ndata: {message}\n\n"
            except queue.Empty:
                pass

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )


@app.route('/start-movement', methods=['POST'])
def start_movement():
    try:
        print("Starting Simulation")
        command_batch = request.get_json().get('commands')
        response = pico_manager.send_movement_data(command_batch)
        print(response)
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error sending movement data: {str(e)}"
        print(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/start-manual', methods=['POST'])
def start_manual():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        speed = data.get('speed', 0)
        displacement = data.get('displacement', 0)
        response = pico_manager.run_manual_routine(speed, displacement)
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error running manual routine: {str(e)}"
        print(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop-movement', methods=['POST'])
def stop_movement():
    try:
        print("Sending stop movement command")
        response = pico_manager.stop_table()
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error stopping table: {str(e)}"
        print(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reset-position', methods=['POST'])
def reset_position():
    try:
        print("Centering Table")
        response = pico_manager.reset_table()
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error resetting table: {str(e)}"
        print(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        setup_connection()
    app.run(debug=True)