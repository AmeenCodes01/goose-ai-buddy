import subprocess
import platform
import time
import logging

logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 10  # Updated to 10 seconds as requested
WIFI_KEYWORDS = ['train', 'bus', 'station']
last_triggered_ssid = None  # State variable to track the last SSID that triggered an event
print(last_triggered_ssid, " last triggers")
def get_wifi_scan_command():
    """Returns the appropriate Wi-Fi scan command for the current OS."""
    os_type = platform.system().lower()
    if os_type == "windows":
        return ["netsh", "wlan", "show", "networks"]
    elif os_type == "darwin":  # macOS
        return ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"]
    elif os_type == "linux":
        return ["nmcli", "dev", "wifi", "list"]
    return None

def find_station_ssid():
    """
    Scans for Wi-Fi networks and returns the SSID if a keyword is found.
    """
    command = get_wifi_scan_command()
    if not command:
        logger.warning(f"Unsupported OS for Wi-Fi scanning: {platform.system()}")
        return None

    logger.info("Scanning for Wi-Fi networks...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        lines = result.stdout.splitlines()
        for line in lines:
            if line.strip().lower().startswith("ssid"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    ssid = parts[1].strip()
                    for keyword in WIFI_KEYWORDS:
                        if keyword in ssid.lower():
                            logger.info(f"Keyword '{keyword}' found in SSID: {ssid}")
                            return ssid  # Return the found SSID
    except FileNotFoundError:
        logger.error(f"Command '{' '.join(command)}' not found. Wi-Fi scanning tool may not be installed.")
    except Exception as e:
        logger.error(f"An error occurred during Wi-Fi scan: {e}")
    
    return None # Return None if no matching SSID is found

def wifi_scanner_agent_loop(event_callback):
    """
    Main loop for the Wi-Fi scanner agent. Manages state to avoid re-triggering for the same network.
    
    Args:
        event_callback (function): The function to call when a new station SSID is detected.
    """
    global last_triggered_ssid
    logger.info("Wi-Fi Scanner Agent thread started.")
    while True:
        found_ssid = find_station_ssid()

        if found_ssid:
            # A station SSID was found. Check if it's a new one.
            if found_ssid != last_triggered_ssid:
                logger.info(f"New station detected: {found_ssid}. Triggering event.")
                if callable(event_callback):
                    event_callback(found_ssid)
                last_triggered_ssid = found_ssid
            else:
                logger.info(f"Still connected to {found_ssid}. No new event triggered.")
        else:
            # No station SSID was found, so we are no longer at the station.
            # Reset the state to allow for future triggers.
            if last_triggered_ssid is not None:
                logger.info("No longer connected to a station Wi-Fi. Resetting state.")
                last_triggered_ssid = None
        
        time.sleep(SCAN_INTERVAL_SECONDS)