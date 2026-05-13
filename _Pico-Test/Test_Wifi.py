import network
import time
from config import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print(f"Connecting to {WIFI_SSID}...")

wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 15
start = time.time()

while not wlan.isconnected():
    elapsed = time.time() - start
    if elapsed > timeout:
        print("FAILED - connection timed out")
        raise SystemExit
    print(f"  waiting... {elapsed}s")
    time.sleep(1)

if wlan.isconnected():
    elapsed = time.time() - start
    status = wlan.ifconfig()
    mac = wlan.config('mac')
    mac_str = ':'.join(f'{b:02x}' for b in mac)
    rssi = wlan.status('rssi')
    
    print()
    print(f"SUCCESS - connected in {elapsed}s")
    print(f"  IP address : {status[0]}")
    print(f"  Subnet     : {status[1]}")
    print(f"  Gateway    : {status[2]}")
    print(f"  DNS        : {status[3]}")
    print(f"  MAC        : {mac_str}")
    print(f"  Signal     : {rssi} dBm")
    time.sleep(2)

    print("\nWiFi test complete! Disconnecting in 5 seconds...")
    time.sleep(2)
    print()
    for i in range(5, 0, -1):
        print(f"  Disconnecting in {i}...")
        time.sleep(1)

    wlan.disconnect()
    wlan.active(False)
    print()
    print("Disconnected.")
    print("Test complete!")