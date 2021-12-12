import cv2
import math
import numpy
from datetime import datetime

class LineFollowOpencv(object):
    def __init__(self, front_wheel, back_wheel, status, dry_run):
        self.front_wheel = front_wheel
        self.back_wheel = back_wheel
        self.status = status
        self.dry_run = dry_run

    def follow_line(self, image):
        lanes = self.detect_lane(image)
        angle = self.lanes_to_angle(image, lanes)
        # store image and angle for debugging
        #timestr = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S.%f')[:-3]
        #cv2.imwrite('/home/pi/Pictures/picar/data/%d-%s.jpg' % (status[0][1], str(angle)), image)
        if angle is not None and self.front_wheel is not None:
            self.front_wheel.turn(angle)

    def detect_lane(self, image):
        edges = self.detect_edges(image)
        lines = self.detect_line_segments(edges)
        # Keep images where lines are not detected for debug purpose
        if lines is None:
            cv2.imwrite('/home/pi/Pictures/no_lines.jpg', image)
        lanes = self.merge_to_lanes(image, lines)
        return lanes

    def detect_edges(self, image):
        # Convert the image color to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/hsv.jpg', hsv)
        
        # Lift blue
        blue_lower = numpy.array([80, 40, 40])
        blue_upper = numpy.array([170, 255, 255])
        blue = cv2.inRange(hsv, blue_lower, blue_upper)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/blue.jpg', blue)

        # Detect edges
        edges = cv2.Canny(blue, 100, 200)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/edges.jpg', edges)

        # Only focus bottom half of the screen
        # Create mask for upper half
        height, width = edges.shape
        mask = numpy.zeros_like(edges)

        polygon = numpy.array([[
            (0, height * 1 / 2), (width, height * 1 / 2), # top left corner
            (width, height), (0, height),  # bottom right corner
        ]], numpy.int32)

        cv2.fillPoly(mask, polygon, 255)
        filtered_edges = cv2.bitwise_and(edges, mask)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/filtered_edges.jpg', filtered_edges)
        return filtered_edges

    def detect_line_segments(self, edges):
        # detect line segments
        rho = 1  # distance precision in pixel, i.e. 1 pixel
        angle = numpy.pi / 180  # angular precision in radian, i.e. 1 degree
        min_threshold = 10  # minimal of votes
        line_segments = cv2.HoughLinesP(
            edges, rho, angle, min_threshold,
            numpy.array([]), minLineLength=10, maxLineGap=4)
        return line_segments

    def merge_to_lanes(self, image, lines):
        if lines is None:
            return None
        left = []  # lines for left lane
        right = []  # lines for right lane
        height, width, _ = image.shape

        # Only collect lines at the left 1/2 for the left lane, similar for right lane
        boundary = 1/2
        left_region_boundary = width * (1 - boundary)
        right_region_boundary = width * boundary

        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            # Skip vertical line since the slope is infinite
            if x1 == x2:
                continue
            parameters = numpy.polyfit((x1, x2), (y1, y2), 1)
            slope = parameters[0]
            y_int = parameters[1]

            if slope < 0:
                if x1 < left_region_boundary and x2 < left_region_boundary:
                    left.append((slope, y_int))
                    cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 5)
            else:
                if x1 > right_region_boundary and x2 > right_region_boundary:
                    right.append((slope, y_int))
                    cv2.line(image, (x1, y1), (x2, y2), (255, 0, 0), 5)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/line_segments.jpg', image)

        lanes = []
        if len(left) > 0:
            left_avg = numpy.average(left, axis=0)
            lanes.append(self.make_points(image, left_avg))

        if len(right) > 0:
            right_avg = numpy.average(right, axis=0)
            lanes.append(self.make_points(image, right_avg))

        # Draw lanes on image
        for lane in lanes:
            x1, y1, x2, y2 = lane
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 5)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/lane.jpg', image)
        return lanes

    def make_points(self, image, average): 
        height, width, _ = image.shape
        slope, intercept = average
        y1 = height  # bottom of the frame
        y2 = int(y1 * 1 / 2)  # make points from middle of the frame down

        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)
        return [x1, y1, x2, y2]

    def lanes_to_angle(self, image, lanes):
        if lanes is None or len(lanes) == 0:
            return None
        height, width, _ = image.shape
        mid = int(width / 2)

        # If there are two lanes, the direction line is in the middle
        if len(lanes) == 2:
            _, _, left_x2, _ = lanes[0]
            _, _, right_x2, _ = lanes[1]
            x_offset = (left_x2 + right_x2) / 2 - mid
            y_offset = int(height / 2)
        # If there is only one lane, follow the direction of the only lane
        elif len(lanes) == 1:
            x1, _, x2, _ = lanes[0]
            x_offset = x2 - x1
            y_offset = int(height / 2)
        else:
            # output image that has no lanes.
            print(len(lanes))
            cv2.imwrite('/home/pi/Pictures/picar/wrong_lanes.jpg', image)

        # Calculate angels from direction line
        angle_radian = math.atan(x_offset / y_offset)  # angle (in radian)
        angle_degree = int(angle_radian * 180.0 / math.pi)  # angle (in degrees)
        steering_angle = angle_degree + 90  # steering angle

        # Display direction line
        cv2.line(image, (int(width/2), height),
                (int(x_offset + mid), int(height/2)), (255, 255, 0), 5)
        if self.dry_run:
            cv2.imwrite('/home/pi/Pictures/direction.jpg', image)
        return steering_angle


def main():
    image = cv2.imread('/home/pi/Pictures/Webcam/bad-17.jpg')
    line_follow_opencv = LineFollowOpencv(None, None, None, dry_run=True)
    line_follow_opencv.follow_line(image)
    cv2.imshow('image',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

