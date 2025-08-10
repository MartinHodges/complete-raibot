import constants
import rp2
import time
import time
from machine import Pin, PWM

class Motor:

    @rp2.asm_pio()
    def edge_counter_right():
        label("start")
        pull(block)          # Wait for Python to send initial count
        mov(x, osr)          # Move received value to counter
        wrap_target()
        wait(0, gpio, 16)      # Wait for pin to go low
        wait(1, gpio, 16)      # Wait for pin to go high (rising edge)
        wait(0, gpio, 17)      # Wait for pin to go low
        wait(1, gpio, 17)      # Wait for pin to go high (rising edge)
        jmp(x_dec, "send")   # Decrement counter
        irq(rel(0))               # Trigger interrupt when counter reaches 0
        jmp("start")         # Go back to wait for next number
        label("send")
        mov(isr, x)          # Move counter to input shift register
        #push()               # Push counter value to RX FIFO
        wrap()

    @rp2.asm_pio()
    def edge_counter_left():
        label("start")
        pull(block)          # Wait for Python to send initial count
        mov(x, osr)          # Move received value to counter
        wrap_target()
        wait(0, gpio, 14)      # Wait for pin to go low
        wait(1, gpio, 14)      # Wait for pin to go high (rising edge)
        wait(0, gpio, 15)      # Wait for pin to go low
        wait(1, gpio, 15)      # Wait for pin to go high (rising edge)
        jmp(x_dec, "send")   # Decrement counter
        irq(rel(0))               # Trigger interrupt when counter reaches 0
        jmp("start")         # Go back to wait for next number
        label("send")
        mov(isr, x)          # Move counter to input shift register
        #push()               # Push counter value to RX FIFO
        wrap()

    def counter_zero(self, sm):
        self.clicks -= constants.DISTANCE_STEP
        if self.clicks <= constants.DISTANCE_STEP:
            self.clicks = 0
            self.stop_motor()
            self.logger.log(f"Motor {self.side} reached target clicks and stopped")
        else:
            self.sm.put(constants.DISTANCE_STEP)

    def __init__(self, side, pwm_pin_number, direction_pin_number, pulse_a_pin_number, pulse_b_pin_number, logger):
        self.side = side
        self.logger = logger
        
        pio_code = self.edge_counter_right if side == constants.RIGHT else self.edge_counter_left
        self.sm = rp2.StateMachine(side, pio_code, freq=2000000, in_base=Pin(pulse_a_pin_number))
        self.sm.irq(self.counter_zero)
        self.sm.active(1)
        self.side = side
        
        self.pwm = PWM(Pin(pwm_pin_number))
        self.pwm.freq(1000)
        
        self.direction = Pin(direction_pin_number, Pin.OUT)

        self.pulse_a = Pin(pulse_a_pin_number, Pin.IN, Pin.PULL_UP)
        self.pulse_b = Pin(pulse_b_pin_number, Pin.IN, Pin.PULL_UP)

        self.last_duty = 0
        self.last_direction = 0
        self.last_clicks_target = 0
        self.clicks = 0
        self.running = False
        self.last_start_time = None
        self.running_time = None
        self.emergency_stopped = False
        
        print(f"{self.sm} {side}")
    
    def get_clicks(self):
        return self.clicks
    
    def get_running_time(self):
        return self.running_time

    def was_emergency_stopped(self):
        return self.emergency_stopped

    def last_direction_value(self):
        return self.last_direction

    def last_duty_value(self):
        return self.last_duty

    def last_clicks_target_value(self):
        return self.last_clicks_target

    def is_running(self):
        return self.running

    def distance_travelled(self):
        return self.last_clicks_target - self.clicks

    def get_side(self):
        return self.side
    
    def stop_motor(self):
        self.pwm.duty_u16(0)
        self.running_time = time.ticks_diff(time.ticks_us(), self.last_start_time)
        self.last_start_time = None
        self.running = False
        self.emergency_stopped = False
        self.logger.log(f"Motor {self.side} stopped")
        
    def emergency_stop(self):
        self.pwm.duty_u16(0)
        self.running_time = time.ticks_diff(time.ticks_us(), self.last_start_time)
        self.last_start_time = None
        self.running = False
        self.emergency_stopped = True
        self.logger.log(f"Motor {self.side} emergency stopped")

    def adjust_duty(self, duty_delta):
        if self.running:
            new_duty = int((self.last_duty * .9) + duty_delta)
            self.pwm.duty_u16(new_duty if new_duty < 65535 else 65535)

    def start_motor(self, direction, duty, clicks):
        
        print(f"{direction} {duty} {clicks}")
        
        if duty <= 0 or clicks <= 0:
            self.logger.log(f"Motor {self.side} invalid start request: {self.last_duty} duty {self.last_clicks_target} clicks")
        elif self.running or duty <= 0 or clicks <= 0:
            self.logger.log(f"Motor {self.side} cannot be started as it is already running or asked to do nothing")
        else:
            self.logger.log(f"Starting Motor {self.side} at {duty} duty for {clicks} clicks...")

            new_duty = duty if duty <= 65535 else 65535

            self.last_clicks_target = clicks
            self.last_duty = duty
            self.running = True
            self.last_direction = 1 if direction else 0
            self.direction.value(self.last_direction)
            self.last_duty = new_duty
            self.running_time = None
            self.clicks = clicks
            self.emergency_stopped = False
            self.sm.put(constants.DISTANCE_STEP)
            self.last_start_time = time.ticks_us()
            self.pwm.duty_u16(new_duty)
