import threading
import queue
import serial
import time
import serial.tools.list_ports
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def showPorts():
    """Lists available serial ports."""
    ports = serial.tools.list_ports.comports()
    choices = []
    logging.info('PORT\tDEVICE\t\t\tMANUFACTURER')
    for index, value in enumerate(sorted(ports)):
        if value.hwid != 'n/a':
            choices.append(index)
            logging.info(f"{index}\t{value.name}\t{value.manufacturer}")

class PicoLink:
    def __init__(self, controllerPort="/dev/cu.usbmodem21201", baudRate=115200, ack="OK"):
        self.serial = None
        self.connected = False
        self.picoPort = controllerPort
        self.baudRate = baudRate
        self.ack = ack
        self.controllerQueue = queue.Queue()
        self.configureController()

    def open(self, timeout=2):
        """Opens the connection to the microcontroller."""
        start = time.time()
        logging.info(f"Waiting for '{self.ack}' from Pico on port {self.picoPort} ...")
        while time.time() - start <= timeout:
            if not self.controllerQueue.empty():
                if self.controllerQueue.get() == self.ack:
                    logging.info("Connection established")
                    self.send("CONF")
                    self.connected = True
                    return
        logging.error(f"*** Unable to establish connection within {timeout} seconds")

    def close(self):
        """Closes the serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False
            logging.info("Serial connection closed.")

    def is_connected(self):
        """Returns the connection status."""
        return self.connected

    def listenToController(self):
        """Continuously reads data from the microcontroller in a separate thread."""
        message = b''
        while True:
            try:
                # Read one byte at a time from the serial port
                incoming = self.serial.read()
                if incoming == b'\n':  # Indicates end of a message
                    decoded_message = message.decode('utf-8').strip().upper()
                    logging.info(f"Received from Pico: {decoded_message}")
                    self.controllerQueue.put(decoded_message)
                    message = b''  # Reset message after handling
                elif incoming not in [b'', b'\r']:  # Append valid data to the message
                    message += incoming
            except serial.SerialException as e:
                logging.error(f"Serial connection issue: {e}")
                self.connected = False
                # Attempt to reconnect the serial connection
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
            logging.error(f"Could not open serial port {self.picoPort}: {e}")

    def reconnect(self, max_retries=5):
        """Handles reconnection logic if the microcontroller disconnects."""
        retries = 0
        while retries < max_retries:
            try:
                logging.info("Attempting to reconnect to the microcontroller...")
                self.serial = serial.Serial(self.picoPort, self.baudRate, timeout=1)
                logging.info("Successfully reconnected to the microcontroller. Listening for commands from the controller.")
                self.send("CONF")
                controllerThread = threading.Thread(target=self.listenToController)
                controllerThread.daemon = True
                controllerThread.start()
                self.connected = True
                return
            except serial.SerialException as e:
                logging.error(f"Reconnection failed: {e}")
                retries += 1
                time.sleep(5)  # Wait before retrying
        logging.error(f"*** Reconnection failed after {max_retries} attempts.")

    def send(self, msg, timeout=5):
        """Sends a message to the microcontroller and waits for a response."""
        try:
            self.serial.write(msg.encode('utf-8'))
            self.serial.write(bytes('\n', encoding='utf-8'))
            start_time = time.time()
            while self.controllerQueue.empty():
                if time.time() - start_time > timeout:
                    logging.error(f"Timeout waiting for response to message: {msg}")
                    return None
                time.sleep(0.01)
            return self.controllerQueue.get()
        except serial.SerialException as e:
            logging.error(f"Failed to send message: {e}")
            self.connected = False
            return None