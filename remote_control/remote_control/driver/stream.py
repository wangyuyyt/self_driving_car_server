#!/usr/bin/env python
'''
**********************************************************************
* Filename    : stream.py
* Description : A streamer module base on mjpg_streamer
* Author      : xxx
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : xxx    xxxx-xx-xx    New release
*               xxx    xxxx-xx-xx    xxxxxxxx
**********************************************************************
'''
from datetime import datetime
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.shortcuts import render
from django.http import StreamingHttpResponse
from . import lane_follow_dl
from PIL import Image
import cv2 
import io
import numpy as np
import os
import picamera
import subprocess
import tempfile
import time

def run_command(cmd):
        with tempfile.TemporaryFile() as f:
                subprocess.call(cmd, shell=True, stdout=f, stderr=f)
                f.seek(0)
                output = f.read()
        return output

def get_host():
        return run_command('hostname -I')

class VideoCamera(object):
    def __init__(self, fw, bw, status_list):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')

        self.fw = fw
        self.bw = bw
        self.status_list = status_list
        self.lane_follow = lane_follow_dl.LaneFollowDeepLearning(
                                 fw, bw, status_list, dry_run=False)
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # Construct a black image if image from the camera is empty.
        if image is None:
            image = np.zeros((640, 480, 1), np.uint8)

        angle = self.status_list[0][2]
        speed = self.status_list[0][3]
        # Auto steering
        if self.status_list is not None and self.status_list[0][0] == 'follow_lane':
            angle = self.lane_follow.follow_lane(image)

        # Save image and angle as training data
        if (self.status_list is not None and len(self.status_list) == 1 
                and self.status_list[0][0] != 'stop'  # backwheel status
                and self.status_list[0][1] ==  1  # save data
            ):
            timestr = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S.%f')[:-3]
            print ('savedata-%s-%d-%d' % (timestr, speed, angle))
            cv2.imwrite('/home/pi/Pictures/picar/trainingdata-tmp/%s-%d-%d.jpg' % (timestr, speed, angle), image)

        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

class CameraStream(object):
    def __init__(self):
        self.stream = io.BytesIO()
        self.current_frame = b''

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # Start of new frame; send the old one's length
            # then the data
            size = self.stream.tell()
            if size > 0:
                self.stream.seek(0)
                self.current_frame = self.stream.read(size)
                self.stream.seek(0)
        self.stream.write(buf)

    def get_frame(self):
        return self.current_frame

    def start(self):
        with picamera.PiCamera(resolution=(640, 480), framerate=30) as camera:
            time.sleep(2)
            camera.start_recording(self, format='mjpeg')
            while True:
                camera.wait_recording(1)
            camera.stop_recording()

