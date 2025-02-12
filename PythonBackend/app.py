# app.py
import os
from queue import Queue, Empty
import logging
from flask_cors import CORS
from flask import Flask, jsonify, render_template, request, Response
from main import PicoConnectionManager

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
message_queue = Queue()
pico_manager = PicoConnectionManager(queue=message_queue)
CORS(
    app,
    resources={r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }},
    supports_credentials=True
)

def trigger_alert(message):
    """Add an error message to the SSE queue."""
    message_queue.put(('error', message))

def trigger_limit_alert():
    """Add a limit triggered alert to the SSE queue."""
    message_queue.put(('limit_triggered', 'Limit switch triggered'))


def setup_connection():
    """Open the connection to the microcontroller."""
    try:
        result = pico_manager.open_connection()
        logging.info(f"Connection result: {result}")

        if "established" in result.lower():
            message_queue.put(('status', 'connected'))
            logging.info("Status updated to: connected")
        else:
            message_queue.put(('status', 'disconnected'))
            message_queue.put(('error', result))
            logging.warning(f"Connection failed: {result}")
    except Exception as e:
        error_msg = f"Failed to open connection: {str(e)}"
        logging.error(error_msg)
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
                # Now use Empty instead of Queue.Empty
                message = message_queue.get(timeout=0.5)
                if message:
                    message_type, message_data = message
                    yield f"event: {message_type}\ndata: {message_data}\n\n"
            except Empty:  # Use Empty instead of Queue.Empty
                # Send heartbeat to keep connection alive
                if pico_manager.conn and pico_manager.conn.is_connected():
                    yield "event: heartbeat\ndata: connected\n\n"
                else:
                    yield "event: heartbeat\ndata: disconnected\n\n"

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