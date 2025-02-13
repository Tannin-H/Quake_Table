# pico_link.py
import threading
import queue
import serial
import time
import serial.tools.list_ports
from logger import Logger

# Initialize the logger
logger = Logger()
log = logger.get_logger()

class PicoLink:
    def __init__(self, controllerPort="/dev/ttyACM0", baudRate=115200, ack="OK", message_queue=None):
        self.serial = None
        self.connected = False
        self.picoPort = controllerPort
        self.baudRate = baudRate
        self.ack = ack
        self.controllerQueue = queue.Queue()
        self.message_queue = message_queue
        self.configureController()

    def open(self, timeout=60):
        """Opens the connection to the microcontroller."""
        start = time.time()
        log.info(f"Waiting for '{self.ack}' from Pico on port {self.picoPort} ...")
        while time.time() - start <= timeout:
            if not self.controllerQueue.empty():
                if self.controllerQueue.get() == self.ack:
                    log.info("Connection established")
                    self.send("CONF")
                    self.connected = True
                    return
        log.error(f"*** Unable to establish connection within {timeout} seconds")

    def close(self):
        """Closes the serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False
            log.info("Serial connection closed.")

    def is_connected(self):
        """Returns the connection status."""
        return self.connected

    def update_connection_status(self, is_connected, error_msg=None):
        """Update connection status and notify through message queue"""
        self.connected = is_connected
        if self.message_queue:
            status = 'connected' if is_connected else 'disconnected'
            log.info(f"Connection status updated to: {status}")
            self.message_queue.put(('status', status))
            if error_msg:
                self.message_queue.put(('error', error_msg))

    def listenToController(self):
        message = b''
        while True:
            try:
                if not self.serial or not self.serial.is_open:
                    self.update_connection_status(False, "Serial connection lost")
                    break

                incoming = self.serial.read()
                if not incoming:  # Timeout occurred
                    continue

                if incoming == b'\n':
                    decoded_message = message.decode('utf-8').strip().upper()
                    log.info(f"Decoded message: '{decoded_message}'")

                    if decoded_message == "LIMIT TRIGGERED":
                        log.info("Limit trigger detected, sending to queue")
                        if self.message_queue:
                            self.message_queue.put(('limit_triggered', 'Limit switch triggered'))
                            log.info("Limit message sent to queue")
                    self.controllerQueue.put(decoded_message)
                    message = b''
                elif incoming not in [b'', b'\r']:
                    message += incoming

            except serial.SerialException as e:
                error_msg = f"Serial connection issue: {e}"
                log.error(error_msg)  # Log the error
                self.update_connection_status(False, error_msg)
                self.reconnect()
                break

    def configureController(self):
        """Configures the microcontroller connection and starts the listening thread."""
        try:
            self.serial = serial.Serial(self.picoPort, self.baudRate, timeout=1)
            controllerThread = threading.Thread(target=self.listenToController)
            controllerThread.daemon = True
            controllerThread.start()
        except serial.SerialException as e:
            log.error(f"Could not open serial port {self.picoPort}: {e}")

    def reconnect(self, max_retries=5):
        """Handles reconnection logic if the microcontroller disconnects."""
        retries = 0
        while retries < max_retries:
            try:
                log.info("Attempting to reconnect to the microcontroller...")
                self.serial = serial.Serial(self.picoPort, self.baudRate, timeout=1)
                log.info("Successfully reconnected to the microcontroller. Listening for commands from the controller.")  # Log successful reconnection
                self.send("CONF")
                controllerThread = threading.Thread(target=self.listenToController)
                controllerThread.daemon = True
                controllerThread.start()
                self.connected = True
                return
            except serial.SerialException as e:
                log.error(f"Reconnection failed: {e}")
                retries += 1
                time.sleep(5)  # Wait before retrying
        log.error(f"*** Reconnection failed after {max_retries} attempts.")

    def send(self, msg, timeout=5):
        """Sends a message to the microcontroller and waits for a response."""
        try:
            self.serial.write(msg.encode('utf-8'))
            self.serial.write(bytes('\n', encoding='utf-8'))
            start_time = time.time()
            while self.controllerQueue.empty():
                if time.time() - start_time > timeout:
                    log.error(f"Timeout waiting for response to message: {msg}")
                    return None
                time.sleep(0.01)
            return self.controllerQueue.get()
        except serial.SerialException as e:
            log.error(f"Failed to send message: {e}")
            self.connected = False
            return None