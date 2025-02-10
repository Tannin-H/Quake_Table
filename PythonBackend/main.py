import time

from pico_link import PicoLink


def open_connection():
    conn = PicoLink()
    conn.open()
    return conn

def run_manual_routine(controller_conn, freq, displacement):
    steps = int(displacement) * 80
    speed = int(freq) * 500
    forwardCMD = f"{speed} 1000 {steps} 0"
    backwardCMD = f"{speed} 1000 {steps} 1"
    controller_conn.send(f"MANUAL {forwardCMD} {backwardCMD}\n")
    return "Manual routine started."

def send_movement_data(controller_conn, command_batch):
    # Each command follows the format:
    # MOVE <speed> <acceleration> <steps> <direction (0|1)>
    batch_commands = command_batch
    # Inform the controller of the batch size.
    batch_size_command = "BATCH_SIZE {}".format(len(batch_commands))
    # print(batch_size_command)
    # print(batch_commands)
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