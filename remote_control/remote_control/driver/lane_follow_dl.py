#!/usr/bin/env python

import cv2 
import numpy as np
import os
import tflite_runtime.interpreter as tflite
from datetime import datetime

class LaneFollowDeepLearning(object):
    def __init__(self, front_wheel, back_wheel, status, dry_run):
        self.front_wheel = front_wheel
        self.back_wheel = back_wheel
        self.status = status
        self.dry_run = dry_run
        self.model_name = 'lane_navigation_check_nvidia.h5.tflite'
        self.tflite_interpreter = tflite.Interpreter(
                model_path=os.path.join(
                    '/home/pi/robotics/self_driving_car_server/remote_control/remote_control/driver/',
                    self.model_name))

    def follow_lane(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (200,66))
        X = np.asarray([image])


        input_details = self.tflite_interpreter.get_input_details()
        output_details = self.tflite_interpreter.get_output_details()
        self.tflite_interpreter.allocate_tensors()

        self.tflite_interpreter.set_tensor(input_details[0]['index'], np.array(X, dtype=np.float32))
        self.tflite_interpreter.invoke()

        angle = self.tflite_interpreter.get_tensor(output_details[0]['index'])
        if angle is not None and self.front_wheel is not None:
            self.front_wheel.turn(angle)
        return angle

    
def main():
    lane_follow = LaneFollowDeepLearning(None, None, None, dry_run=True)

    timestr = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S.%f')[:-3]
    print(timestr)

    for f in os.listdir('/home/pi/Pictures/picar/trainingdata/')[0:100]:
        image = cv2.imread(os.path.join('/home/pi/Pictures/picar/trainingdata/', f))
        angle = lane_follow.follow_lane(image)
        print('%s  .. :%.3f' % (f, angle))

    timestr = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S.%f')[:-3]
    print(timestr)

if __name__ == "__main__":
    main()
