# --- remote_logger.py (Corrected Snippet) ---
import sys
import urequests
import ujson
import time
import network # Assuming this import is needed in this module

class HttpLogger:
    def __init__(self, url, wlan_connection, max_buffer_size):
        self.url = url
        self.buffer = []
        self.max_buffer_size = max_buffer_size
        self.bytes_buffered = 0
        self.wlan = wlan_connection

    def log(self, s):
        print(s)
        
        if s.strip():
            self.buffer.append(s + '\n')
            self.bytes_buffered += len(s)
        
        if self.bytes_buffered >= self.max_buffer_size:
            self.flush()

    def flush(self):
        if not self.buffer:
            return

        if not self.wlan or not self.wlan.isconnected():
            print("Cannot flush: Wi-Fi not connected.\n")
            return

        log_data = "".join(self.buffer)
        
        try:
            headers = {'Content-Type': 'text/plain'}
            response = urequests.post(self.url, data=log_data, headers=headers)
            
            if response.status_code == 200:
                print("<<\n")
            else:
                print(f"Failed to send logs. Status: {response.status_code}\n")
            
            response.close()

        except Exception as e:
            print(f"HTTP request failed: {e}\n")

        finally:
            self.buffer.clear()
            self.bytes_buffered = 0