'''
**********************************************************************
* Filename    : views
* Description : views for server
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Cavon    2016-09-13    New release
**********************************************************************
'''

from .driver import camera, stream
from .driver.stream import VideoCamera, gen
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.shortcuts import render
from picar import back_wheels, front_wheels
import picar
import queue

picar.setup()
db_file = "remote_control/driver/config"
fw = front_wheels.Front_Wheels(debug=False, db=db_file)
bw = back_wheels.Back_Wheels(debug=False, db=db_file)
cam = camera.Camera(debug=False, db=db_file)
cam.ready()
bw.ready()
fw.ready()

SPEED = 60
BW_STATUS = 'stop'
FW_ANGLE = 90
CAM_PAN = 90
CAM_TILT = 90
status_list = [[BW_STATUS, SPEED]]

def show_status():
     global SPEED, BW_STATUS, FW_ANGLE, CAM_PAN, CAM_TILT
     print('speed: %d, bw_status: %s, fw_angle: %d, cam_pan: %d, cam_tilt: %d' %
             (SPEED, BW_STATUS, FW_ANGLE, CAM_PAN, CAM_TILT))


def home(request):
     return render(request, "base.html")

def run(request):
     global SPEED, BW_STATUS, FW_ANGLE, CAM_PAN, CAM_TILT, q
     debug = ''
     if 'action' in request.GET:
          action = request.GET['action']
          if action == 'follow_lane_opencv':
              BW_STATUS = action
              bw.speed = 30
              cam.turn_down(20)
          # ============== Back wheels =============
          elif action == 'bwready':
               bw.ready()
               BW_STATUS = 'stop'
          elif action == 'forward':
               bw.speed = SPEED
               bw.forward()
               BW_STATUS = 'forward'
               debug = "speed =", SPEED
          elif action == 'backward':
               bw.speed = SPEED
               bw.backward()
               BW_STATUS = 'backward'
          elif action == 'stop':
               bw.stop()
               BW_STATUS = 'stop'
               cam.ready()

          # ============== Front wheels =============
          elif action == 'fwready':
               FW_ANGLE = fw.ready()
          elif action == 'fwleft':
               FW_ANGLE = fw.turn_left()
          elif action == 'fwright':
               FW_ANGLE = fw.turn_right()
          elif action == 'fwstraight':
               FW_ANGLE = fw.turn_straight()
          elif 'fwturn' in action:
               print("turn %s" % action)
               angle = int(action.split(':')[1])
               FW_ANGLE = angle
               fw.turn(angle)
          
          # ================ Camera =================
          elif action == 'camready':
               (CAM_PAN, CAM_TILT) = cam.ready()
          elif action == "camleft":
               CAM_PAN = cam.turn_left(40)
          elif action == 'camright':
               CAM_PAN = cam.turn_right(40)
          elif action == 'camup':
               CAM_TILT = cam.turn_up(20)
          elif action == 'camdown':
               CAM_TILT = cam.turn_down(20) 
     if 'speed' in request.GET:
          speed = int(request.GET['speed'])
          if speed < 0:
               speed = 0
          if speed > 100:
               speed = 100
          SPEED = speed
          if BW_STATUS != 'stop':
               bw.speed = speed
          debug = "speed =", speed
     #status.save()
     #print(status)
     #q.put(BW_STATUS)
     status_list[0] = [BW_STATUS, SPEED]
     show_status()
     host = stream.get_host().decode('utf-8').split(' ')[0]
     return render(request, "run.html", {'host': host})

def cali(request):
     if 'action' in request.GET:
          action = request.GET['action']
          # ========== Camera calibration =========
          if action == 'camcali':
               print('"%s" command received' % action)
               cam.calibration()
          elif action == 'camcaliup':
               print('"%s" command received' % action)
               cam.cali_up()
          elif action == 'camcalidown':
               print('"%s" command received' % action)
               cam.cali_down()
          elif action == 'camcalileft':
               print('"%s" command received' % action)
               cam.cali_left()
          elif action == 'camcaliright':
               print('"%s" command received' % action)
               cam.cali_right()
          elif action == 'camcaliok':
               print('"%s" command received' % action)
               cam.cali_ok()

          # ========= Front wheel cali ===========
          elif action == 'fwcali':
               print('"%s" command received' % action)
               fw.calibration()
          elif action == 'fwcalileft':
               print('"%s" command received' % action)
               fw.cali_left()
          elif action == 'fwcaliright':
               print('"%s" command received' % action)
               fw.cali_right()
          elif action == 'fwcaliok':
               print('"%s" command received' % action)
               fw.cali_ok()

          # ========= Back wheel cali ===========
          elif action == 'bwcali':
               print('"%s" command received' % action)
               bw.calibration()
          elif action == 'bwcalileft':
               print('"%s" command received' % action)
               bw.cali_left()
          elif action == 'bwcaliright':
               print('"%s" command received' % action)
               bw.cali_right()
          elif action == 'bwcaliok':
               print('"%s" command received' % action)
               bw.cali_ok()
          else:
               print('command error, error command "%s" received' % action)
     return render(request, "cali.html")

def connection_test(request):
     return HttpResponse('OK')

def monitor(request):
    global status_list
    return StreamingHttpResponse(gen(VideoCamera(fw, bw, status_list)),
        content_type='multipart/x-mixed-replace; boundary=frame')

