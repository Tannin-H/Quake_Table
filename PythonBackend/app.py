import os

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
        return jsonify({"status": "success", "response": response})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':  # True only for the second run in debug mode
        setup_connection()
    app.run(debug=True)
