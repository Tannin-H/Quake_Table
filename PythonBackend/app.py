# app.py
import os
from queue import Queue, Empty
from flask_cors import CORS
from flask import Flask, jsonify, render_template, request, Response
from main import PicoConnectionManager
from logger import Logger  # Import the Logger class

# Initialize the logger
logger = Logger()
log = logger.get_logger()

app = Flask(__name__)
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
    log.error(message)

def trigger_limit_alert():
    """Add a limit triggered alert to the SSE queue."""
    message_queue.put(('limit_triggered', 'Limit switch triggered'))
    log.warning("Limit switch triggered")

def setup_connection():
    """Open the connection to the microcontroller."""
    try:
        result = pico_manager.open_connection()
        log.info(f"Connection result: {result}")

        if "established" in result.lower():
            message_queue.put(('status', 'connected'))
            log.info("Status updated to: connected")
        else:
            message_queue.put(('status', 'disconnected'))
            message_queue.put(('error', result))
            log.warning(f"Connection failed: {result}")
    except Exception as e:
        error_msg = f"Failed to open connection: {str(e)}"
        log.error(error_msg)  # Log the error
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
                message = message_queue.get(timeout=0.5)
                if message:
                    message_type, message_data = message
                    yield f"event: {message_type}\ndata: {message_data}\n\n"
            except Empty:
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
        log.info("Starting Simulation")
        command_batch = request.get_json().get('commands')
        response = pico_manager.send_movement_data(command_batch)
        log.info(f"Response: {response}")
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error sending movement data: {str(e)}"
        log.error(error_msg)
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
        log.info(f"Manual routine response: {response}")
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error running manual routine: {str(e)}"
        log.error(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop-movement', methods=['POST'])
def stop_movement():
    try:
        log.info("Sending stop movement command")
        response = pico_manager.stop_table()
        log.info(f"Stop command response: {response}")
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error stopping table: {str(e)}"
        log.error(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reset-position', methods=['POST'])
def reset_position():
    try:
        log.info("Centering Table")
        response = pico_manager.reset_table()
        log.info(f"Reset command response: {response}")
        if response["status"] == "error":
            trigger_alert(response["message"])
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        error_msg = f"Error resetting table: {str(e)}"
        log.error(error_msg)
        trigger_alert(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        setup_connection()
    app.run(debug=True)