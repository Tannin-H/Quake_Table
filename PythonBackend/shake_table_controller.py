import math
import time

from config import Config
from pico_link import PicoLink
from logger import Logger

# Initialize the logger
logger = Logger()
log = logger.get_logger(__name__)


def _calculate_slew_speed(freq, a_max_steps, D_steps):
    """
    Calculates slew speed in steps/s using quadratic formula.

    Formula: v_s = (a_max/(2f)) - sqrt[(a_max/(2f))² - D*a_max]

    Args:
        freq: Motion frequency in Hz (complete cycles per second)
              Each cycle has 2 moves (forward + backward)

    Returns:
        tuple: (slew_speed_steps, error_message) where error_message is None if successful
    """
    # Convert motion frequency to move frequency
    # 2 Hz motion = 4 moves/second (2 forward + 2 backward)
    move_freq = freq * 2

    # Check if motion is physically possible
    min_accel_required = 16 * D_steps * move_freq ** 2
    if a_max_steps < min_accel_required:
        error_msg = (
            f"Motion not possible: requires minimum acceleration of "
            f"{min_accel_required:.2f} steps/s², but max is {a_max_steps} steps/s²"
        )
        return None, error_msg

    # Calculate slew speed using quadratic formula
    # Use move period (time for ONE move, not full cycle)
    move_period = 1 / move_freq
    term1 = a_max_steps * move_period / 2
    term2 = math.sqrt((a_max_steps * move_period / 2) ** 2 - D_steps * a_max_steps)
    slew_speed_steps = term1 - term2

    return slew_speed_steps, None

class ShakeTableController:
    def __init__(self, queue=None):
        """
        Initialize the Shake Table Controller.
        :param queue: Message queue for status updates
        """
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
            self.conn = PicoLink(self.message_queue)
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
            log.info("Connection closed.")
            return "Connection closed."
        return "No connection to close."

    def run_manual_routine(self, freq, displacement):
        """Runs a manual routine with the given frequency and displacement."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}

        try:

            # Convert displacement to steps
            steps = int(displacement * Config.STEPS_PER_MM)

            # Acceleration in mm/s² - convert to steps/s²
            a_max_steps = Config.MAX_ACCELERATION * Config.STEPS_PER_MM  # steps/s²

            # Calculate slew speed
            slew_speed_steps, error_msg = _calculate_slew_speed(
                freq, a_max_steps, steps
            )

            if error_msg:
                log.error(error_msg)
                return {"status": "error", "message": error_msg}

            # Format commands with integer values
            forwardCMD = f"{int(slew_speed_steps)} {int(a_max_steps)} {steps} 0"
            backwardCMD = f"{int(slew_speed_steps)} {int(a_max_steps)} {steps} 1"

            log.info(f"Forward command: {forwardCMD}")
            log.info(f"Backward command: {backwardCMD}")

            response = self.conn.send(f"MANUAL {forwardCMD} {backwardCMD}\n")
            log.info(f"Manual routine response: {response}")
            return {
                "status": "success",
                "message": f"Manual routine started. Response: {response}"
            }
        except Exception as e:
            error_msg = f"Failed to start manual routine: {e}"
            return {"status": "error", "message": error_msg}

    def send_movement_data(self, command_batch):
        """Sends a batch of movement commands to the microcontroller."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            batch_size_command = f"BATCH_SIZE {len(command_batch)}"
            log.info(f"Sending batch size: {batch_size_command}")
            self.conn.send(batch_size_command + '\n')

            for i, command in enumerate(command_batch):
                response = self.conn.send(command + '\n')
                if response is None:
                    error_msg = f"Failed to send command {i + 1}/{len(command_batch)}: {command}"
                    log.error(error_msg)
                    return {"status": "error", "message": error_msg}
                time.sleep(0.01)

            log.info(f"Successfully sent batch of {len(command_batch)} commands")
            return {"status": "success", "message": f"Batch of {len(command_batch)} commands sent."}
        except Exception as e:
            error_msg = f"Failed to send movement data: {e}"
            return {"status": "error", "message": error_msg}

    def stop_table(self):
        """Sends a stop command to the microcontroller."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            response = self.conn.send("STOP\n")
            log.info(f"Stop command sent. Response: {response}")
            return {"status": "success", "message": f"Stop command sent. Response: {response}"}
        except Exception as e:
            error_msg = f"Failed to stop table: {e}"
            return {"status": "error", "message": error_msg}

    def reset_table(self):
        """Sends a reset command to the microcontroller."""
        if self.conn is None:
            error_msg = "Connection not established. Ensure table is connected."
            return {"status": "error", "message": error_msg}
        try:
            response = self.conn.send("RESET\n")
            log.info(f"Reset command sent. Response: {response}")
            return {"status": "success", "message": f"Reset command sent. Response: {response}"}
        except Exception as e:
            error_msg = f"Failed to reset table: {e}"
            return {"status": "error", "message": error_msg}