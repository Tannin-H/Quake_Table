# main.py
import time
from pico_link import PicoLink
from logger import Logger

# Initialize the logger
logger = Logger()
log = logger.get_logger()

class PicoConnectionManager:
    def __init__(self, port="/dev/ttyACM0", baud_rate=115200, ack="OK", queue=None):
        self.port = port
        self.baud_rate = baud_rate
        self.ack = ack
        self.conn = None
        self.message_queue = queue
        self.last_status = None

    def update_status(self, status, error_msg=None):
        """Update status and send through message queue if changed"""
        if status != self.last_status:
            self.last_status = status
            if self.message_queue:
                self.message_queue.put(('status', status))
                if error_msg:
                    self.message_queue.put(('error', error_msg))
            log.info(f"Status updated to: {status}")

    def open_connection(self):
        """Opens the connection to the microcontroller."""
        try:
            self.conn = PicoLink(self.port, self.baud_rate, self.ack, self.message_queue)
            self.conn.open()

            if self.conn.is_connected():
                self.update_status('connected')
                return "Connection established."
            else:
                self.update_status('disconnected', "Failed to establish connection")
                self.conn = None
                return "Failed to establish connection."
        except Exception as e:
            error_msg = f"Failed to open connection: {e}"
            self.update_status('disconnected', error_msg)
            self.conn = None
            return error_msg

    def close_connection(self):
        """Closes the connection to the microcontroller."""
        if self.conn:
            self.conn.close()
            self.conn = None
            return "Connection closed."
        return "No connection to close."

    def run_manual_routine(self, freq, displacement):
        """Runs a manual routine with the given frequency and displacement."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            steps = int(displacement) * 80
            speed = int(freq) * 500
            forwardCMD = f"{speed} 1000 {steps} 0"
            backwardCMD = f"{speed} 1000 {steps} 1"
            response = self.conn.send(f"MANUAL {forwardCMD} {backwardCMD}\n")
            return {"status": "success", "message": f"Manual routine started. Response: {response}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to start manual routine: {e}"}

    def send_movement_data(self, command_batch):
        """Sends a batch of movement commands to the microcontroller."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            batch_size_command = f"BATCH_SIZE {len(command_batch)}"
            self.conn.send(batch_size_command + '\n')

            for command in command_batch:
                response = self.conn.send(command + '\n')
                if response is None:
                    return {"status": "error", "message": f"Failed to send command: {command}"}
                time.sleep(0.01)

            return {"status": "success", "message": f"Batch of {len(command_batch)} commands sent."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to send movement data: {e}"}

    def stop_table(self):
        """Sends a stop command to the microcontroller."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            response = self.conn.send("STOP\n")
            return {"status": "success", "message": f"Stop command sent. Response: {response}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop table: {e}"}

    def reset_table(self):
        """Sends a reset command to the microcontroller."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            response = self.conn.send("RESET\n")
            return {"status": "success", "message": f"Reset Command command sent. Response: {response}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop table: {e}"}