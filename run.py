import ctypes
from ctypes import wintypes
import psutil
import time
import keyboard

class ProcessReader:
    def __init__(self, process_name):
        self.process_name = process_name
        self.process_handle = None
        self.process_id = None
        
    def open_process(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == self.process_name.lower():
                self.process_id = proc.pid
                self.process_handle = ctypes.windll.kernel32.OpenProcess(
                    0x0010,
                    False,
                    self.process_id
                )
                return True
        return False
        
    def read_memory(self, address):
        if not self.process_handle:
            return None
            
        buffer = ctypes.c_uint32()
        bytes_read = ctypes.c_size_t()
        
        address_ptr = ctypes.c_void_p(address)
        
        success = ctypes.windll.kernel32.ReadProcessMemory(
            self.process_handle,
            address_ptr,
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read)
        )
        
        if success:
            raw_value = buffer.value
            if raw_value < 1000 and raw_value % 10 == 0:
                return raw_value // 10
            return raw_value
        return None
        
    def close(self):
        if self.process_handle:
            ctypes.windll.kernel32.CloseHandle(self.process_handle)
            self.process_handle = None

def get_valid_threshold():
    while True:
        try:
            threshold = int(input("Enter threshold (must be greater than 2): "))
            if threshold > 2:
                return threshold
            print("Please enter a number greater than 2.")
        except ValueError:
            print("Please enter a valid number.")

def verify_condition(reader, address, threshold, is_above):
    print(f"\nVerifying {'high' if is_above else 'low'} value for 3 seconds...")
    time.sleep(3)
    
    new_value = reader.read_memory(address)
    if new_value is not None:
        if is_above and new_value >= threshold:
            print(f"\nConfirmed. Current value: {new_value}")
        elif not is_above and new_value < threshold:
            print(f"\nConfirmed. Current value: {new_value}")
        else:
            print(f"\nValue changed during verification. Current value: {new_value}")
    print("\nContinuing monitoring...")
    return new_value >= threshold

def main():
    reader = ProcessReader("Species.exe")
    
    if reader.open_process():
        try:
            address_str = input("Enter memory address (in hex): ")
            address_str = address_str.replace("0x", "")
            address = int(address_str, 16)
            
            threshold = get_valid_threshold()
            
            print("\nMonitoring started...")
            print("Press 'q' to quit")
            print(f"Monitoring for values >= {threshold}...")
            
            last_value = None
            was_above_threshold = False
            verification_in_progress = False
            
            while not keyboard.is_pressed('q'):
                value = reader.read_memory(address)
                
                if value != last_value:
                    print(f"Current value: {value}", end='\r')
                    last_value = value
                
                if value is not None and not verification_in_progress:
                    if value >= threshold and not was_above_threshold:
                        verification_in_progress = True
                        was_above_threshold = verify_condition(reader, address, threshold, True)
                        verification_in_progress = False
                        
                    elif value < threshold and was_above_threshold:
                        verification_in_progress = True
                        was_above_threshold = verify_condition(reader, address, threshold, False)
                        verification_in_progress = False
                    
                time.sleep(0.1)
                
        finally:
            reader.close()
            print("\nMonitoring stopped.")
    else:
        print("Process not found")

if __name__ == "__main__":
    main()