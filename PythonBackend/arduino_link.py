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


class ArduinoLink:
    arduinoQueue = queue.Queue()

    def __init__(self, arduinoPort="/dev/cu.usbmodem21201", baudRate=115200, ack="OK"):
        self.arduinoPort = arduinoPort
        self.baudRate = baudRate
        self.ack = ack
        self.configureArduino()

    def open(self, timeout=5):
        start = time.time()
        print(f"Waiting for '{self.ack}' from Arduino on port {self.arduinoPort} ...")
        while time.time() - start <= timeout:
            if not self.arduinoQueue.empty():
                if self.arduinoQueue.get() == self.ack:
                    print("Connection established")
                    return
        print(f"*** Unable to establish connection within {timeout} seconds")

    def listenToArduino(self):
        """Continuously reads data from the Arduino in a separate thread."""
        message = b''
        while True:
            try:
                # Read one byte at a time from the serial port
                incoming = self.serial.read()
                if incoming == b'\n':  # Indicates end of a message
                    self.arduinoQueue.put(message.decode('utf-8').strip().upper())
                    message = b''  # Reset message after handling
                elif incoming not in [b'', b'\r']:  # Append valid data to the message
                    message += incoming
            except serial.SerialException as e:
                print(f"[ERROR] Serial connection issue: {e}")
                # Attempt to reconnect the serial connection
                self.reconnect()
                break

    def configureArduino(self):
        """Configures the Arduino connection and starts the listening thread."""
        try:
            self.serial = serial.Serial(self.arduinoPort, self.baudRate, timeout=1)
            arduinoThread = threading.Thread(target=self.listenToArduino)
            arduinoThread.daemon = True
            arduinoThread.start()
        except serial.SerialException as e:
            print(f"[ERROR] Could not open serial port {self.arduinoPort}: {e}")

    def reconnect(self):
        """Handles reconnection logic if the Arduino disconnects."""
        print("[INFO] Attempting to reconnect to the Arduino...")
        while True:
            try:
                # Attempt to reconnect to the Arduino
                self.serial = serial.Serial(self.arduinoPort, self.baudRate, timeout=1)
                print("[INFO] Successfully reconnected to the Arduino.")
                arduinoThread = threading.Thread(target=self.listenToArduino)
                arduinoThread.daemon = True
                arduinoThread.start()
                break
            except serial.SerialException as e:
                print(f"[ERROR] Reconnection failed: {e}")
                time.sleep(5)  # Wait before retrying

    def send(self, msg):
        """Sends a message to the Arduino and waits for a response."""
        self.serial.write(msg.encode('utf-8'))
        self.serial.write(bytes('\n', encoding='utf-8'))
        while self.arduinoQueue.empty():
            pass
        return self.arduinoQueue.get()
