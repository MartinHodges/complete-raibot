# raibot-firmware
This project provides firmware for a Raspberry Pi Pico W (not the Pico 2) based on a micropython kernel.

It is assumed that the Pico has:
* 4 inputs associated with bump detectors (front, back, left and right)
* 4 inputs associated with A and B phases from the left and right motor rotational sensors
* 2 PWM outputs to drive the left and right motors
* 2 outputs to drive the left and right motor directions

These pins are configured in the `constants.py` file.

# Setting up the firmware
Before using this firmware, a `credentials.py` file is required with the following contents:
```
SSID = '<your Wi-Fi SID>>'
PASSWORD = '<your Wi-Fi password>'
REMOTE_LOG_URL = '<the URL of your remote logger, eg: http://10.0.1.50:3002/log>'
```

# Thonny
I have used the Thonny IDE to upload the micropython code and to run it in a localised test mode.
