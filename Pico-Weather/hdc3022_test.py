import machine # type: ignore
import time

# I2C setup - same bus as BMP390
i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1))

# HDC3022 address
HDC3022_ADDR = 0x44

# Trigger measurement command (high repeatability)
def read_hdc3022():
    # Send measurement command
    i2c.writeto(HDC3022_ADDR, bytes([0x24, 0x00]))
    time.sleep_ms(50)
    
    # Read 6 bytes: temp MSB, temp LSB, temp CRC, hum MSB, hum LSB, hum CRC
    data = i2c.readfrom(HDC3022_ADDR, 6)
    
    # Convert temperature
    temp_raw = (data[0] << 8) | data[1]
    temp_c = -45 + 175 * (temp_raw / 65535)
    temp_f = temp_c * 9/5 + 32
    
    # Convert humidity
    hum_raw = (data[3] << 8) | data[4]
    humidity = 100 * (hum_raw / 65535)
    
    return temp_c, temp_f, humidity

# Main loop
while True:
    temp_c, temp_f, humidity = read_hdc3022()
    print(f"Temp: {temp_c:.2f} C / {temp_f:.2f} F")
    print(f"Humidity: {humidity:.2f} %")
    print("---")
    time.sleep(2)