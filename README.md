# Quake Table Control System

A Flask-based web application for controlling a shake table via serial communication with a Raspberry Pi Pico microcontroller.

## Overview

This system provides a web interface to control a shake table for earthquake simulation. It communicates with a Raspberry Pi Pico running firmware available at [Quake_Drive](https://github.com/Tannin-H/Quake_Drive).

## Requirements

- Python 3.12
- Raspberry Pi Pico with Quake_Drive firmware
- Serial connection to the Pico

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd quake-table-control-system
```

2. Install dependencies:
```bash
pip install flask flask-cors pyserial
```

3. Configure the COM port in `config.py` or set the `COM_PORT` environment variable to match your Pico's serial port.

## Usage

1. Connect the Raspberry Pi Pico to your computer via USB

2. Run the application:
```bash
python app.py
```
When the application and pico connection has been established the table with go through a calibration sequence triggering both limit switches then returning centre

3. Open your browser and navigate to `http://127.0.0.1:5051`

4. Use the web interface to control the shake table:
   - **Manual Controls**: Set frequency and displacement for sinusoidal motion
   - **Stop Simulation**: Emergency stop for the table
   - **Reset Position**: Return table to center position

## Known Limitations

- **Manual controls only**: Currently only manual control mode has been tested for accuracy
- **Cosine generation**: The cosine waveform generation feature is not yet functional
- **Motor stall risk**: Manual controls can send commands that exceed table capabilities, causing the motor to stall. Use the stop command or remove power going to the driver if this occurs.

## Configuration

Key settings in `config.py`:
- `COM_PORT`: Serial port for Pico connection (default: `/dev/tty.usbmodem21301`)
- `BAUD_RATE`: Serial communication baud rate (default: 205200)
- `STEPS_PER_MM`: Stepper motor steps per millimeter (default: 80)
- `MAX_ACCELERATION`: Maximum table acceleration in mm/s² (default: 8000)

## Project Structure

```
├── app.py                      # Flask application entry point
├── config.py                   # Configuration settings
├── logger.py                   # Logging utility
├── pico_link.py               # Serial communication with Pico
├── shake_table_controller.py  # Shake table control logic
└── templates/
    └── index.html             # Web interface
```

## License

MIT License

Copyright (c) 2025
