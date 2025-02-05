import json
from pico_link import PicoLink

def open_connection():
    conn = PicoLink()
    conn.open()
    return conn

def send_movement_data(controller_conn):
    # Define movement data
    movement_data = "MOVE 500 500 2000"

    # Establish connection and send data
    response = controller_conn.send(movement_data + '\n')  # Ensure newline to indicate end of message
    return response

def init_table(controller_conn):
    response = controller_conn.send("RESET\n")
    return response