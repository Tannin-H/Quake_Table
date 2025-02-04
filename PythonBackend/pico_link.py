import threading
import queue
import serial
import time
import serial.tools.list_ports


def showPorts():
    ports = serial.tools.list_ports.comports()
    choices = []
    print('PORT\tDEVICE\t\t\tMANUFACTURER')
    for index, value in enumerate(sorted(ports)):
        if value.hwid != 'n/a':
            choices.append(index)
            print(index, '\t', value.name, '\t', value.manufacturer)


class PicoLink:
    controllerQueue = queue.Queue()

    def __init__(self, controllerPort="/dev/cu.usbmodem21201", baudRate=115200, ack="OK"):
        self.picoPort = controllerPort
        self.baudRate = baudRate
        self.ack = ack
        self.configureController()

    def open(self, timeout=10):
        start = time.time()
        print(f"Waiting for '{self.ack}' from Pico on port {self.picoPort} ...")
        while time.time() - start <= timeout:
            if not self.controllerQueue.empty():
                if self.controllerQueue.get() == self.ack:
                    print("Connection established")
                    self.send("CONF")
                    return
        print(f"*** Unable to establish connection within {timeout} seconds")

    def listenToController(self):
        """Continuously reads data from the microcontroller in a separate thread."""
        message = b''
        while True:
            try:
                # Read one byte at a time from the serial port
                incoming = self.serial.read()
                if incoming == b'\n':  # Indicates end of a message
                    self.controllerQueue.put(message.decode('utf-8').strip().upper())
                    message = b''  # Reset message after handling
                elif incoming not in [b'', b'\r']:  # Append valid data to the message
                    message += incoming
            except serial.SerialException as e:
                print(f"[ERROR] Serial connection issue: {e}")
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
            print(f"[ERROR] Could not open serial port {self.picoPort}: {e}")

    def reconnect(self):
        """Handles reconnection logic if the microcontroller disconnects."""
        print("[INFO] Attempting to reconnect to the microcontroller...")
        while True:
            try:
                # Attempt to reconnect to the microcontroller
                self.serial = serial.Serial(self.picoPort, self.baudRate, timeout=1)
                print("[INFO] Successfully reconnected to the microcontroller. Listening for commands from the controller.")
                controllerThread = threading.Thread(target=self.listenToController)
                controllerThread.daemon = True
                controllerThread.start()
                break
            except serial.SerialException as e:
                print(f"[ERROR] Reconnection failed: {e}")
                time.sleep(5)  # Wait before retrying

    def send(self, msg):
        """Sends a message to the microcontroller and waits for a response."""
        self.serial.write(msg.encode('utf-8'))
        self.serial.write(bytes('\n', encoding='utf-8'))
        while self.controllerQueue.empty():
            pass
        return self.controllerQueue.get()
