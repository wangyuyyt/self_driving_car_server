#!/usr/bin/env python

import cv2 
import picar
from picar.SunFounder_PCA9685 import Servo
from PIL import Image
import io
import RPi.GPIO as GPIO
import time
import picamera

def turn_servo(channel):
    servo = Servo.Servo(channel, bus_number=1)
    for i in range(0, 180, 10):
        servo.write(i)
        time.sleep(1)
    for i in range(180, 0, -10):
        servo.write(i)
        time.sleep(1)


def set_servo(channel):
    servo = Servo.Servo(channel, bus_number=1)
    servo.setup()
    servo.write(0)
    time.sleep(1)
    servo.write(90)
    time.sleep(1)
    servo.write(180)
    time.sleep(1)
    servo.write(90)
    servo.write(0)
    
if __name__ == '__main__':
    picar.setup()
    set_servo(15)

