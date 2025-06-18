# Raspberry Pi BMS Data Logger & Dashboard

This project provides a solution for monitoring PowerQueen and Renogy LiFePO4 battery management systems (BMS) via Bluetooth. It consists of a Python script to poll data from your devices and store it in a SQLite database, and a modern web dashboard to visualize this data with movable, persistent widgets.

## Table of Contents
* Features
* Requirements
* Project Structure
* Setup & Installation
  * 1. Clone the Repository
  * 2. System Bluetooth Setup (Raspberry Pi / Linux)
  * 3. Python Environment Setup
  * 4. Configure the Data Logger Script
  * 5. Run the Data Logger
  * 6. Set up the Web Dashboard
* Database Structure
* Viewing the Database
* Future Enhancements
* Disclaimer
* Contributing
* License

## Features
* Multi-BMS Support: Polls data from both PowerQueen and Renogy Bluetooth-enabled BMS devices.
* Data Logging: Stores all collected data in a local SQLite database (bms_data.db) for historical analysis.
* Configurable Polling Interval: Easily set how often data is collected (default: every 5 minutes).
* Modern Web Dashboard:
  * Visualizes key metrics (PowerQueen SOC, Remaining Capacity; Renogy PV Power).
  * Interactive line graphs with selectable time intervals (24 hours, 7 days, 30 days, 6 months).
  * Current status widgets for both PowerQueen and Renogy devices.
  * Movable and Resizable Widgets: Customize your dashboard layout using drag-and-drop.
  * Persistent Layout: Your custom dashboard arrangement is saved locally using browser cookies.
* Simulated Data (for demonstration): The dashboard initially uses simulated data, making it easy to set up and visualize before connecting to real devices via a backend.

## Requirements
### Hardware
* Raspberry Pi (or any Linux machine with Bluetooth capabilities)
* Bluetooth-enabled PowerQueen LiFePO4 battery
* Renogy device (e.g., charge controller, battery) with a BT-1 or BT-2 Bluetooth module
* Reliable power supply for your Raspberry Pi

### Software
* Operating System: Raspberry Pi OS (formerly Raspbian) or any Debian-based Linux distribution.
* Python: Python 3.7 or higher.
* Bluetooth Utilities: bluez (pre-installed on most Linux systems, but requires development headers).
* Python Libraries:
  * bleak (asynchronous BLE client)
  * pq-bms-bluetooth (for PowerQueen devices)
  * renogybt (for Renogy devices)
* Web Browser: A modern web browser (e.g., Chrome, Firefox, Edge) to view the dashboard.

## Project Structure
```
├── bms_data_logger.py      # Python script for polling and logging data
├── dashboard.html          # Web dashboard UI
├── bms_data.db             # SQLite database (will be created automatically)
└── README.md               # This file
```
## Setup & Installation
Follow these steps to get your BMS data logger and dashboard running on your Raspberry Pi.

### 1. Clone the Repository
First, clone this GitHub repository to your Raspberry Pi:
```
git clone https://github.com/your-username/your-repo-name.git  # Replace with your actual repo URL
cd your-repo-name
```
### 2. System Bluetooth Setup (Raspberry Pi / Linux)
Ensure your Raspberry Pi's Bluetooth is correctly configured and your user has the necessary permissions.
```
sudo apt update
sudo apt install bluetooth bluez libbluetooth-dev python3-dev
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo usermod -a -G bluetooth $USER # Add your current user to the bluetooth group
sudo reboot # Reboot for group changes to take effect
```

Important: After rebooting, log in again. Bluetooth devices usually only allow one active connection. Make sure no other apps (like official PowerQueen or Renogy mobile apps) are connected to your BMS devices when running the script.

### 3. Python Environment Setup
It's highly recommended to use a Python virtual environment to manage dependencies.
```
python3 -m venv venv
source venv/bin/activate # On Linux/macOS
# For Windows, use: .\venv\Scripts\activate
pip install --upgrade pip
pip install bleak pq-bms-bluetooth renogybt
```

### 4. Configure the Data Logger Script
Open bms_data_logger.py in your favorite text editor (e.g., nano bms_data_logger.py) and modify the configuration section:
```
# --- Configuration ---
# IMPORTANT: Replace these with the actual MAC addresses of your devices.
# You can typically find these using tools like 'bluetoothctl' on Linux or
# by checking the official apps for your devices.

POWERQUEEN_MAC_ADDRESS = "XX:XX:XX:XX:XX:XX"  # e.g., "00:1A:7D:DA:71:03"
RENOGY_MAC_ADDRESS = "YY:YY:YY:YY:YY:YY"      # e.g., "A1:B2:C3:D4:E5:F6"
RENOGY_DEVICE_ID = 255                        # Default broadcast ID, or specific device ID if known (e.g., 1 for Rover)

DB_NAME = "bms_data.db"
POLLING_INTERVAL_SECONDS = 300 # 5 minutes
```
* POWERQUEEN_MAC_ADDRESS: Replace "XX:XX:XX:XX:XX:XX" with the Bluetooth MAC address of your PowerQueen BMS.
* RENOGY_MAC_ADDRESS: Replace "YY:YY:YY:YY:YY:YY" with the Bluetooth MAC address of your Renogy BT module.
* RENOGY_DEVICE_ID: For Renogy, 255 often works as a broadcast ID. If you have multiple Renogy devices connected via a BT-2 Communication Hub, you might need to find their individual device IDs (refer to renogybt library documentation or issues for guidance).
* POLLING_INTERVAL_SECONDS: Adjust the polling frequency as needed.

To find MAC addresses on Linux:
1. Run bluetoothctl.
2. Type ```agent on``` and then ```scan on`.
3. Look for devices that appear in the list (you might need to enable pairing/discovery on your BMS if it has that option). Note down the MAC address (e.g., 00:1A:7D:DA:71:03).
4. Type ```scan off``` and then ```quit```.

### 5. Run the Data Logger
After configuring the script, you can run it:
```
source venv/bin/activate
python3 bms_data_logger.py
```

The script will start polling and logging data to bms_data.db. You should see log messages in your terminal.

To run in the background (recommended for continuous logging):
For a simple background process (will stop if the terminal closes):
```
source venv/bin/activate && nohup python3 bms_data_logger.py &
```

To stop it, you'll need to find its process ID (```ps aux | grep bms_data_logger.py```) and then kill <PID>.

For a more robust solution, especially for a Raspberry Pi that runs 24/7, consider setting it up as a systemd service. This ensures it starts on boot and restarts if it crashes. (Detailed systemd setup is beyond this README, but many online guides are available for Python scripts.)

### 6. Set up the Web Dashboard
The dashboard.html file provides the front-end UI. For it to display real data from your bms_data.db database, you'll need a simple web server (backend API) to serve the data.

Option A: Simple Local Server (for testing/development - uses simulated data)
You can open dashboard.html directly in your browser. It will use its internal simulated data for demonstration purposes, showing you the dashboard functionality, movable widgets, and persistent layout.
From your project directory
```
open dashboard.html # On macOS
xdg-open dashboard.html # On Linux
start dashboard.html # On Windows
```

Option B: Backend API (Recommended for real data)
To connect dashboard.html to your bms_data.db, you'll need to implement a small web server (e.g., using Python's Flask or FastAPI) that:
1. Reads data from bms_data.db.
2. Exposes API endpoints (e.g., /api/powerqueen/soc?interval=24_hours, /api/current_status) that the dashboard.html can fetch data from.
3. Serves dashboard.html itself.

Here's a conceptual example of how a Flask app might look (this is not included in the repository and needs to be built separately):
```
# app.py (Example Flask backend - NOT part of this repo)
from flask import Flask, jsonify, send_file, request
import sqlite3
import datetime
import os

app = Flask(__name__)
DATABASE = 'bms_data.db' # Path to your SQLite DB

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_file('dashboard.html')

@app.route('/api/powerqueen/soc')
def get_powerqueen_soc():
    interval = request.args.get('interval', '24_hours')
    # Implement logic to query SQLite based on interval
    # and return data in the format expected by dashboard.html
    conn = get_db_connection()
    # Example: fetch last X hours/days of data
    cursor = conn.cursor()
    # This query needs to be adapted for your specific data needs (e.g. aggregation for longer intervals)
    cursor.execute("SELECT timestamp, soc FROM powerqueen_data ORDER BY timestamp DESC LIMIT 100")
    data = [{'timestamp': row['timestamp'], 'value': row['soc']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

# Add similar endpoints for powerqueen_remaining_capacity, renogy_pv_power, and current status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```
You would then run this Flask app (e.g., python app.py), and access the dashboard via http://<Your_Pi_IP_Address>:5000.

## Database Structure
The bms_data.db SQLite database will contain two tables:

### powerqueen_data
| Column Name | Type | Description |
|---|---|---|
| timestamp | TEXT | ISO format datetime of data collection |
| mac_address | TEXT | Bluetooth MAC address of the device |
| voltage | REAL | Total battery voltage |
| current | REAL | Battery charge/discharge current |
| soc | REAL | State of Charge (%) |
| temp1 | REAL | Temperature sensor 1 (°C) |
| temp2 | REAL | Temperature sensor 2 (°C) |
| cycle_count | INTEGER | Number of charge/discharge cycles |
| full_charge_capacity | REAL | Full charge capacity (Ah) |
| remaining_capacity | REAL | Remaining capacity (Ah) |
| design_capacity | REAL | Design capacity (Ah) |
| charge_discharge_status | TEXT | Current status (e.g., "charging", "discharging") |
| num_cells | INTEGER | Number of cells |
| errors | TEXT | Any reported errors |

### renogy_data
| Column Name | Type | Description |
|---|---|---|
| timestamp | TEXT | ISO format datetime of data collection |
| mac_address | TEXT | Bluetooth MAC address of the device |
| device_id | INTEGER | Renogy device ID |
| battery_voltage | REAL | Battery voltage |
| battery_current | REAL | Battery current (charge/discharge) |
| battery_soc | REAL | Battery State of Charge (%) |
| battery_temp | REAL | Battery temperature (°C) |
| controller_temp | REAL | Charge controller temperature (°C) |
| pv_voltage | REAL | Solar panel (PV) voltage |
| pv_current | REAL | Solar panel (PV) current |
| pv_power | REAL | Solar panel (PV) power (Watts) |
| daily_pv_gen | REAL | Daily PV generation (Wh) |
| total_pv_gen | REAL | Total PV generation (Wh) |
| load_status | TEXT | Load status (e.g., "on", "off") |
| load_current | REAL | Load current |
| load_power | REAL | Load power (Watts) |

## Viewing the Database
You can view the contents of your bms_data.db file using a SQLite browser tool, such as:
* DB Browser for SQLite: A free and open-source visual tool available for Windows, macOS, and Linux.
* SQLite CLI: From your Raspberry Pi terminal, you can access it directly:
    sqlite3 bms_data.db
    .tables
    SELECT * FROM powerqueen_data LIMIT 5;
    SELECT * FROM renogy_data LIMIT 5;
    .quit

## Future Enhancements
* Backend API: Implement a full Python Flask/FastAPI backend to serve data from the SQLite database to the dashboard dynamically.
* Real-time Status Updates: Make the "Current Status" widgets update in real-time by fetching data from the backend more frequently.
* More Data Points: Add more metrics from both BMS types to the database and dashboard.
* Alerts & Notifications: Implement custom alerts based on battery parameters (e.g., low SOC, high temperature).
* Authentication: Secure the dashboard with user authentication if exposed outside a local network.
* Configuration File: Externalize more configuration options (like polling intervals, device names) from the Python script into a separate config file.
* Dockerization: Containerize the Python script and a simple web server using Docker for easier deployment and management.

## Disclaimer
This project uses unofficial Python libraries for communication with PowerQueen and Renogy devices. While efforts are made to ensure accuracy and safety, use this software at your own risk. The developer(s) are not responsible for any damage or issues arising from its use.

## Contributing
Contributions are welcome! If you find a bug or have an idea for an improvement, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License - see the LICENSE file for details (you would typically include a LICENSE file in your repo).
