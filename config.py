import os


class Config:
    """Application configuration"""
    # Flask settings
    DEBUG = True

    # Server settings
    FLASK_HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5051))

    # CORS settings
    CORS_ORIGINS = '*'
    CORS_METHODS = ["GET", "POST", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization"]

    # Logging settings
    LOG_LEVEL = 'DEBUG'

    # SSE settings
    SSE_HEARTBEAT_TIMEOUT = 0.5

    # Hardware Connection settings
    COM_PORT = os.environ.get('COM_PORT', '/dev/tty.usbmodem21301')
    BAUD_RATE = os.environ.get('BAUD_RATE', 205200)
    ACK = os.environ.get('ACK', 'OK')
    CONNECTION_TIMEOUT = os.environ.get('CONNECTION_TIMEOUT', 60)
    MAX_RECONNECT_ATTEMPTS = int(os.environ.get('MAX_RECONNECT_ATTEMPTS', 5))

    # Physical Table Settings
    STEPS_PER_MM = os.environ.get('STEPS_PER_MM', 80)
    MAX_ACCELERATION = os.environ.get('MAX_ACCELERATIONS', 8000) # in mm/s^2 This needs to be tuned to ensure the motor doesn't stall