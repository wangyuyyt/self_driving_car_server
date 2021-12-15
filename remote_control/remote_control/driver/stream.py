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
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.shortcuts import render
from django.http import StreamingHttpResponse
import cv2 
import numpy as np
import os
import subprocess
import tempfile

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
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # Construct a black image if image from the camera is empty.
        if image is None:
            image = np.zeros((640, 480, 1), np.uint8)
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
