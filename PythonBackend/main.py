import time

from pico_link import PicoLink

def open_connection():
    conn = PicoLink()
    conn.open()
    return conn

def start_manual_routine(controller_conn):
    controller_conn.send("MANUAL 800 0 200 0 800 0 200 1" + '\n')
    return "Manual routine started."

def send_movement_data(controller_conn):
     # Each command follows the format:
    # MOVE <speed> <acceleration> <steps> <direction (0|1)>
    batch_commands = [
        "MOVE 7000 1000 2000 0",
        "MOVE 8000 1000 2000 1",
        "MOVE 7000 1000 2000 0",
        "MOVE 8000 1000 2000 1"
    ]

    # Inform the controller of the batch size.
    batch_size_command = "BATCH_SIZE {}".format(len(batch_commands))
    controller_conn.send(batch_size_command + '\n')

    # Send each movement command in the batch.
    for command in batch_commands:
        controller_conn.send(command + '\n')
        time.sleep(0.01)

    # Optionally, you could collect and process responses here.
    return "Batch of {} commands sent.".format(len(batch_commands))


def stop_table(controller_conn):
    response = controller_conn.send("STOP\n")
    return response