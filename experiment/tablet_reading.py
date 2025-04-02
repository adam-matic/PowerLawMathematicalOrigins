## tablet_reading.py

import time
from time import perf_counter
try:
    from pywinusb import hid
except ImportError:
    print("Warning: pywinusb module not found. Tablet functionality will be limited.")
    hid = None

class Tablet:
    def __init__(self):
        self.reset_data()
        self.device = None
        
        if hid is None:
            print("pywinusb module not available. Tablet functionality will not work.")
            return
            
        print("Looking for Huion tablet...")
        self.find_and_connect_tablet()
        
        if self.device:
            print("Connected to tablet. Move the pen over the tablet to see events.")
        else:
            print("No tablet found. Will use mouse fallback.")

    def reset_data(self):
        """Reset all tracking data"""
        self.start_time = perf_counter()
        self.xs = []
        self.ys = []
        self.times = []
        self.x = 0
        self.y = 0
        self.pressures = []
        self.pressure = 0
        self.data = []

    def close(self):
        """Close the device connection if one exists"""
        if self.device: 
            try:
                self.device.close()
            except:
                pass

    def sample_handler(self, data):
        """Handler called when tablet data is received"""
        t = perf_counter() - self.start_time
        # For Huion tablets, data is typically structured as:
        # [report_id, status, x_low, x_high, y_low, y_high, pressure_low, pressure_high, .. button statuses]
        if len(data) >= 8:            
            self.x = (data[3] << 8) | data[2]
            self.y = (data[5] << 8) | data[4]
            pressure = (data[7] << 8) | data[6]
            self.xs.append(self.x)
            self.ys.append(self.y)
            self.pressures.append(pressure)
            self.times.append(t)
            self.data.append({"x":self.x, "y":self.y, "t":t})
        if (len(self.xs) != len(self.ys)):
            print("different length", len(self.x), len(self.y))

    def find_and_connect_tablet(self):
        """Find the Huion tablet and connect to it"""
        if hid is None:
            return None
            
        try:
            # Huion 610 Pro vendor ID (may need adjustment for your specific model)
            huion_vendor_id = 0x256c
            
            # Find all HID devices
            all_devices = hid.HidDeviceFilter().get_devices()
            
            # Try to find the Huion tablet by vendor ID
            tablet_devices = hid.HidDeviceFilter(vendor_id=huion_vendor_id).get_devices()
            
            if not tablet_devices:
                print("No Huion tablet found. Try running as administrator.")
                print("You may also need to check the correct vendor ID for your tablet model.")
                return None
            
            # Use the first tablet device found
            self.device = tablet_devices[0]
            print(f"Found tablet: {self.device.product_name}")
            
            try:
                self.device.open()
                # Set the handler for input reports
                self.device.set_raw_data_handler(self.sample_handler)
            except Exception as e:
                print(f"Error opening tablet: {e}")
                self.device = None
        except Exception as e:
            print(f"Unexpected error initializing tablet: {e}")
            self.device = None
