import asyncio
import sqlite3
import datetime
import sys
import logging

# Attempt to import the specific libraries
try:
    from pq_bms_bluetooth import PowerQueenBMS
    print("Successfully imported pq_bms_bluetooth")
except ImportError:
    print("Error: pq_bms_bluetooth library not found. Please install it using: pip install pq-bms-bluetooth")
    sys.exit(1)

try:
    # Assuming the main client class for renogy-bt is RenogyBTClient
    # The actual import might vary based on the library's structure.
    # Check the renogy-bt's GitHub repo (cyrils/renogy-bt) for precise import.
    # Based on search results, 'renogybt' seems to be the module name.
    from renogybt import RenogyBTClient
    print("Successfully imported renogybt")
except ImportError:
    print("Error: renogybt library not found. Please install it using: pip install renogybt")
    sys.exit(1)

# --- Configuration ---
# IMPORTANT: Replace these with the actual MAC addresses of your devices.
# You can typically find these using tools like 'bluetoothctl' on Linux or
# by checking the official apps for your devices.
POWERQUEEN_MAC_ADDRESS = "XX:XX:XX:XX:XX:XX"  # e.g., "00:1A:7D:DA:71:03"
RENOGY_MAC_ADDRESS = "YY:YY:YY:YY:YY:YY"      # e.g., "A1:B2:C3:D4:E5:F6"
RENOGY_DEVICE_ID = 255                        # Default broadcast ID, or specific device ID if known (e.g., 1 for Rover)

DB_NAME = "bms_data.db"
POLLING_INTERVAL_SECONDS = 300 # 5 minutes

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# --- Database Functions ---
def create_tables(db_name):
    """
    Connects to the SQLite database and creates necessary tables if they don't exist.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Table for PowerQueen BMS data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS powerqueen_data (
                timestamp TEXT PRIMARY KEY,
                mac_address TEXT,
                voltage REAL,
                current REAL,
                soc REAL,
                temp1 REAL,
                temp2 REAL,
                cycle_count INTEGER,
                full_charge_capacity REAL,
                remaining_capacity REAL,
                design_capacity REAL,
                charge_discharge_status TEXT,
                num_cells INTEGER,
                errors TEXT
            )
        ''')

        # Table for Renogy BT data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS renogy_data (
                timestamp TEXT PRIMARY KEY,
                mac_address TEXT,
                device_id INTEGER,
                battery_voltage REAL,
                battery_current REAL,
                battery_soc REAL,
                battery_temp REAL,
                controller_temp REAL,
                pv_voltage REAL,
                pv_current REAL,
                pv_power REAL,
                daily_pv_gen REAL,
                total_pv_gen REAL,
                load_status TEXT,
                load_current REAL,
                load_power REAL
            )
        ''')
        conn.commit()
        logging.info(f"SQLite tables checked/created in {db_name}")
    except sqlite3.Error as e:
        logging.error(f"Error creating database tables: {e}")
    finally:
        if conn:
            conn.close()

def insert_powerqueen_data(data):
    """
    Inserts PowerQueen BMS data into the database.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO powerqueen_data (
                timestamp, mac_address, voltage, current, soc, temp1, temp2,
                cycle_count, full_charge_capacity, remaining_capacity, design_capacity,
                charge_discharge_status, num_cells, errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['timestamp'], data['mac_address'], data['voltage'], data['current'], data['soc'],
            data['temp1'], data['temp2'], data['cycle_count'], data['full_charge_capacity'],
            data['remaining_capacity'], data['design_capacity'], data['charge_discharge_status'],
            data['num_cells'], data['errors']
        ))
        conn.commit()
        logging.info("PowerQueen data inserted successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error inserting PowerQueen data: {e}")
    finally:
        if conn:
            conn.close()

def insert_renogy_data(data):
    """
    Inserts Renogy BT data into the database.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO renogy_data (
                timestamp, mac_address, device_id, battery_voltage, battery_current,
                battery_soc, battery_temp, controller_temp, pv_voltage, pv_current,
                pv_power, daily_pv_gen, total_pv_gen, load_status, load_current, load_power
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['timestamp'], data['mac_address'], data['device_id'], data['battery_voltage'],
            data['battery_current'], data['battery_soc'], data['battery_temp'],
            data['controller_temp'], data['pv_voltage'], data['pv_current'], data['pv_power'],
            data['daily_pv_gen'], data['total_pv_gen'], data['load_status'],
            data['load_current'], data['load_power']
        ))
        conn.commit()
        logging.info("Renogy data inserted successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error inserting Renogy data: {e}")
    finally:
        if conn:
            conn.close()

# --- Polling Functions ---
async def poll_powerqueen_device(mac_address: str):
    """
    Connects to the PowerQueen BMS, polls data, and stores it.
    """
    logging.info(f"Polling PowerQueen BMS at {mac_address}...")
    pq_bms = PowerQueenBMS(mac_address)
    try:
        await pq_bms.connect()
        data = await pq_bms.read_all_data()

        if data:
            timestamp = datetime.datetime.now().isoformat()
            # Prepare data for insertion, handling potential missing keys
            pq_data_to_store = {
                'timestamp': timestamp,
                'mac_address': mac_address,
                'voltage': data.get('total_voltage', 0.0),
                'current': data.get('current', 0.0),
                'soc': data.get('state_of_charge', 0.0),
                'temp1': data.get('temperature_1', 0.0),
                'temp2': data.get('temperature_2', 0.0),
                'cycle_count': data.get('cycle_count', 0),
                'full_charge_capacity': data.get('full_charge_capacity', 0.0),
                'remaining_capacity': data.get('remaining_capacity', 0.0),
                'design_capacity': data.get('design_capacity', 0.0),
                'charge_discharge_status': data.get('charge_discharge_status', 'Unknown'),
                'num_cells': data.get('number_of_cells', 0),
                'errors': str(data.get('errors', 'No errors'))
            }
            insert_powerqueen_data(pq_data_to_store)
            logging.info(f"PowerQueen data collected for {mac_address}: {pq_data_to_store['soc']}% SOC")
        else:
            logging.warning(f"No data received from PowerQueen BMS at {mac_address}")

    except Exception as e:
        logging.error(f"Failed to poll PowerQueen BMS at {mac_address}: {e}")
    finally:
        await pq_bms.disconnect()


async def poll_renogy_device(mac_address: str, device_id: int):
    """
    Connects to the Renogy BT device, polls data, and stores it.
    """
    logging.info(f"Polling Renogy BT device at {mac_address} (Device ID: {device_id})...")
    renogy_client = RenogyBTClient(mac_address, device_id)
    try:
        await renogy_client.connect()
        # The renogybt library provides a get_status() method for common data.
        # You might need to explore more methods for comprehensive data like PV generation history.
        status_data = await renogy_client.get_status()
        all_params = await renogy_client.get_all_parameters() # This often includes more detailed info

        if status_data and all_params:
            timestamp = datetime.datetime.now().isoformat()

            # Merge data for easier processing
            merged_data = {**status_data, **all_params}

            # Prepare data for insertion, handling potential missing keys
            renogy_data_to_store = {
                'timestamp': timestamp,
                'mac_address': mac_address,
                'device_id': device_id,
                'battery_voltage': merged_data.get('battery_voltage', 0.0),
                'battery_current': merged_data.get('battery_charge_current', 0.0), # or battery_current depending on the library's exact key
                'battery_soc': merged_data.get('battery_soc', 0.0),
                'battery_temp': merged_data.get('battery_temp', 0.0),
                'controller_temp': merged_data.get('controller_temperature', 0.0),
                'pv_voltage': merged_data.get('pv_voltage', 0.0),
                'pv_current': merged_data.get('pv_current', 0.0),
                'pv_power': merged_data.get('pv_power_watts', 0.0),
                'daily_pv_gen': merged_data.get('daily_power_generation', 0.0),
                'total_pv_gen': merged_data.get('total_power_generation', 0.0),
                'load_status': merged_data.get('load_status', 'Unknown'),
                'load_current': merged_data.get('load_current', 0.0),
                'load_power': merged_data.get('load_power_watts', 0.0)
            }
            insert_renogy_data(renogy_data_to_store)
            logging.info(f"Renogy data collected for {mac_address}: Battery SOC {renogy_data_to_store['battery_soc']}%")
        else:
            logging.warning(f"No data received from Renogy BT device at {mac_address}")

    except Exception as e:
        logging.error(f"Failed to poll Renogy BT device at {mac_address}: {e}")
    finally:
        await renogy_client.disconnect()


async def main():
    """
    Main function to run the polling loop.
    """
    logging.info("Starting BMS Data Logger.")
    create_tables(DB_NAME)

    while True:
        logging.info("--- Starting new polling cycle ---")
        # Poll PowerQueen device
        if POWERQUEEN_MAC_ADDRESS != "XX:XX:XX:XX:XX:XX":
            await poll_powerqueen_device(POWERQUEEN_MAC_ADDRESS)
        else:
            logging.warning("PowerQueen MAC address not configured. Skipping PowerQueen polling.")

        # Poll Renogy device
        if RENOGY_MAC_ADDRESS != "YY:YY:YY:YY:YY:YY":
            await poll_renogy_device(RENOGY_MAC_ADDRESS, RENOGY_DEVICE_ID)
        else:
            logging.warning("Renogy MAC address not configured. Skipping Renogy polling.")

        logging.info(f"Next polling cycle in {POLLING_INTERVAL_SECONDS} seconds...")
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    # Ensure this script is run in an asyncio event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("BMS Data Logger stopped by user.")
    except Exception as e:
        logging.critical(f"An unhandled error occurred: {e}")

