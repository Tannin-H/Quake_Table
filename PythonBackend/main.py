import json
from arduino_link import ArduinoLink

def open_connection():
    conn = ArduinoLink()
    conn.open()
    return conn

def send_movement_data(arduino_conn):
    # Define movement data
    movement_data = {
        "movements": [
            {"speed": 500, "acceleration": 1000, "steps": 1000},
            {"speed": 600, "acceleration": 1200, "steps": 1500},
            {"speed": 700, "acceleration": 800, "steps": 1200}
        ]
    }

    # Convert the movement data to JSON format
    json_data = json.dumps(movement_data)

    # Establish connection and send data
    response = arduino_conn.send(json_data + '\n')  # Ensure newline to indicate end of message
    return response