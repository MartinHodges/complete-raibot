import rp2
import time
import network
import socket
import _thread
import ujson
import time
from machine import Pin, PWM
from remote_logger import HttpLogger
import constants
from motor import Motor
import credentials

BUMP_CONFIG = [2, 3, 4, 5]

left_motor = None
right_motor = None
motors = [None, None]

bumps = [None, None, None, None]

cal_adjustment = 0

debug = False

calibrate = False

def init_pins():
    global bumps
    bumps = [
        Pin(BUMP_CONFIG[constants.LEFT], Pin.IN, Pin.PULL_UP),
        Pin(BUMP_CONFIG[constants.RIGHT], Pin.IN, Pin.PULL_UP),
        Pin(BUMP_CONFIG[constants.FRONT], Pin.IN, Pin.PULL_UP),
        Pin(BUMP_CONFIG[constants.BACK], Pin.IN, Pin.PULL_UP)
        ]

def calc_calibration():
    global cal_adjustment

    if left_motor.get_running_time() is None or right_motor.get_running_time() is None:
        return

    if left_motor.was_emergency_stopped() or right_motor.was_emergency_stopped():
        return

    if right_motor.get_running_time() == 0 or left_motor.get_running_time() == 0:
        return

    adjustment = right_motor.get_running_time() / left_motor.get_running_time()
    cal_adjustment = adjustment * (cal_adjustment if cal_adjustment > 0.5 else 1)
    my_logger.log(f"Adjustment factor: {cal_adjustment}")
 
# --- Custom URL Query String Parser for MicroPython ---
def parse_qs_micropython(query_string):
    """
    A simple URL query string parser for MicroPython.
    Does not handle URL decoding (e.g., %20) or duplicate keys gracefully like urllib.parse.
    Expects 'key=value&key2=value2' format.
    Returns a dictionary where values are lists (to mimic urllib.parse's behavior, but usually 1 item).
    """
    params = {}
    if not query_string:
        return params
    
    pairs = query_string.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1) # Split only on the first '='
            # Simple unquoting (for spaces). For full URL decoding, it's more complex.
            value = value.replace('+', ' ')
            params[key] = [value] # Store as list to mimic parse_qs behavior
        # else: handle cases like 'key_only' if needed
    return params

# --- HTTP Server Thread Function ---
def http_server_thread():
    global actual_target_pulses, debug
    addr = socket.getaddrinfo('0.0.0.0', constants.WEB_PORT)[0][-1]
    s = socket.socket()
    # Allow the port to be reused
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    my_logger.log(f'listening on {addr}')

    while True:
        try:
            conn, addr = s.accept()
            # print('client connected from', addr)
            request = conn.recv(1024)
            # print(request)

            data = request.decode()
            request_lines = data.split('\r\n')
            request_line = request_lines[0]
            my_logger.log(f"Request: {request_lines}")


            if "POST /debug" in request_line:
                debug = not debug
            elif "POST /motor" in request_line:
                headers, body = data.split("\r\n\r\n", 1)
                if debug:
                    my_logger.log(f"Headers received:\n{headers}")

                # Extract Content-Length
                content_length = 0
                for line in headers.split("\r\n"):
                    if line.lower().startswith("content-length"):
                        content_length = int(line.split(":")[1].strip())
                        break

                # If not all body bytes are received yet
                while len(body) < content_length:
                    body += conn.recv(1024).decode() 

                if debug:
                    my_logger.log(f"Raw body:\n {body}")

                left_motor.stop_motor()
                right_motor.stop_motor()

                # Parse JSON
                new_state = ujson.loads(body)
                motor1_count = int(new_state['right']['count'])
                motor1_duty = int(float(new_state['right']['duty']) * cal_adjustment)
                motor1_dir = (new_state['right']['direction'] == "forward")

                # For motor2
                motor2_count = int(new_state['left']['count'])
                motor2_duty = int(new_state['left']['duty'])             
                motor2_dir = (new_state['left']['direction'] == "forward")

                no_travel = False
                bump_stop = False

                if motor1_duty == 0 or motor1_count == 0:
                    right_motor.stop_motor()
                    no_travel = True

                if motor2_duty == 0 or motor2_count == 0:
                    left_motor.stop_motor()
                    no_travel = True

                if motor1_dir == motor2_dir:
                    if motor1_dir == constants.FORWARD and bumps[constants.FRONT].value() == 1:
                        bump_stop = True
                    if motor1_dir == constants.REVERSE and bumps[constants.BACK].value() == 1:
                        bump_stop = True
                
                if bump_stop:
                    right_motor.emergency_stop()
                    left_motor.emergency_stop()
                elif no_travel:
                    right_motor.stop_motor()
                    left_motor.stop_motor()
                else:
                    right_motor.start_motor(motor1_dir, motor1_duty, motor1_count)
                    left_motor.start_motor(motor2_dir, motor2_duty, motor2_count)

                if debug:
                    my_logger.log(f"Parsed JSON:\n {data}")

                while left_motor.is_running() or right_motor.is_running():
                    time.sleep(0.1)
                calc_calibration()

            html_content = f"""
{{
    "right": {{
        "running": "{right_motor.is_running()}",
        "direction": "{'forward' if right_motor.last_direction  else 'reverse'}",
        "duty": "{right_motor.last_duty_value()}",
        "travelled": "{right_motor.distance_travelled()}"
    }},
    "left": {{
        "running": "{left_motor.is_running()}",
        "direction": "{'forward' if left_motor.last_direction else 'reverse'}",
       "duty": "{left_motor.last_duty_value()}",
       "travelled": "{left_motor.distance_travelled()}"
    }},
    "adjustment": "{cal_adjustment}",
    "force_stopped": "{right_motor.was_emergency_stopped() or left_motor.was_emergency_stopped()}",
    "bumps": {{
        "front": "{bumps[constants.FRONT].value()}",
        "left":  "{bumps[constants.LEFT].value()}",
        "right": "{bumps[constants.RIGHT].value()}",
        "back":  "{bumps[constants.BACK].value()}"
    }}
}}
                """
            response = 'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n' + html_content
            conn.send(response)
            conn.close()

        except OSError as e:
            conn.close()
            # print('connection closed', e) # Suppress frequent "connection closed" messages

# --- Wi-Fi Connecton Function ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])
    return wlan

# --- Main Program ---
print("Initializing...")

# Connect to Wi-Fi
print("Connecting to WiFi...")
wlan = connect_wifi(credentials.SSID, credentials.PASSWORD)

init_pins()

print("Press Ctrl+C to stop")

try:
    # Start HTTP server in a separate thread
    _thread.start_new_thread(http_server_thread, ())

    # Create an instance of the logger and replace stdout
    my_logger = HttpLogger(credentials.REMOTE_LOG_URL, wlan, constants.LOG_BUFFER_SIZE)

    left_motor = Motor(constants.LEFT, constants.LEFT_MOTOR_PWM, constants.LEFT_MOTOR_DIR, constants.LEFT_MOTOR_PULSE_A, constants.LEFT_MOTOR_PULSE_B, my_logger)
    right_motor = Motor(constants.RIGHT, constants.RIGHT_MOTOR_PWM, constants.RIGHT_MOTOR_DIR, constants.RIGHT_MOTOR_PULSE_A, constants.RIGHT_MOTOR_PULSE_B, my_logger)

    motors = [left_motor, right_motor]

    my_logger.log("System ready for dual motors. Both are currently stopped.")

    left_motor.start_motor(constants.FORWARD, constants.DEFAULT_SPEED_DUTY, constants.DEFAULT_TARGET_CLICKS)
    right_motor.start_motor(constants.FORWARD, constants.DEFAULT_SPEED_DUTY, constants.DEFAULT_TARGET_CLICKS)

    while left_motor.is_running() or right_motor.is_running():
        time.sleep(0.1)
    calc_calibration()
    
    # The main loop simply keeps the script running.
    # All active motor control and HTTP serving happens in threads and PIO.
    while True:
        if bumps[constants.FRONT].value() == 1 and (left_motor.is_running() or right_motor.is_running()):
            if left_motor.last_direction_value() == constants.FORWARD and right_motor.last_direction_value() == constants.FORWARD:
                my_logger.log("Stopping going forwards to avoid object")
                left_motor.emergency_stop()
                right_motor.emergency_stop()
        
        if bumps[constants.BACK].value() == 1 and (left_motor.is_running() or right_motor.is_running()):
            if left_motor.last_direction_value() == constants.REVERSE and left_motor.last_direction_value() == constants.REVERSE:
                my_logger.log("Stopping going reverse to avoid object")
                left_motor.emergency_stop()
                right_motor.emergency_stop()
        
        time.sleep(0.1)
        my_logger.flush()

except KeyboardInterrupt:
    motors[constants.LEFT].emergency_stop()
    motors[constants.RIGHT].emergency_stop()
    my_logger.log("\nStopped")
        

