#!/usr/bin/env python
import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import CompressedImage, Image
from duckietown_msgs.msg import Segment, SegmentList, Pixel, Vector2D
from line_detector.LineDetector import *
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
import numpy as np

class LineDetectorNode(object):
    def __init__(self):
        self.node_name = "Line Detector"
        
        self.hei_image = self.setupParam("~hei_image", 240)
        self.wid_image = self.setupParam("~wid_image", 320)
        self.top_cutoff  = self.setupParam("~top_cutoff", 90)
        
        self.bridge = CvBridge()
        self.detector = LineDetector()
        
        self.sub_image = rospy.Subscriber("~image", CompressedImage, self.processImage)
        self.pub_lines = rospy.Publisher("~segment_list", SegmentList, queue_size=1)
        self.pub_image = rospy.Publisher("~image_with_lines", Image, queue_size=1)

    def setupParam(self, param_name, default_value):
        value = rospy.get_param(param_name, default_value)
        rospy.set_param(param_name, value) # Write to parameter server for transparancy
        rospy.loginfo("[%s] %s = %s " %(self.node_name,param_name,value))
        return value

    def processImage(self,image_msg):
        image_cv = cv2.imdecode(np.fromstring(image_msg.data, np.uint8), cv2.CV_LOAD_IMAGE_COLOR)
        #image_cv = self.bridge.imgmsg_to_cv2(image_msg, "bgr8")
        
        # Resize and crop image
        hei_original = image_cv.shape[0]
        wid_original = image_cv.shape[1]
        if self.hei_image!=hei_original or self.wid_image!=wid_original:
            image_cv = cv2.resize(image_cv, (self.wid_image, self.hei_image))
        image_cv = image_cv[self.top_cutoff:,:,:]

        # Set the image to be detected
        self.detector.setImage(image_cv)
	
        # Detect lines and normals
        lines_white, normals_white = self.detector.detectLines('white')
        lines_yellow, normals_yellow = self.detector.detectLines('yellow')
        lines_red, normals_red = self.detector.detectLines('red')

        # Draw lines and normals
        self.detector.drawLines(lines_white, (0,0,0))
        self.detector.drawLines(lines_yellow, (255,0,0))
        self.detector.drawLines(lines_red, (0,255,0))
        #self.detector.drawNormals(lines_white, normals_white)
        #self.detector.drawNormals(lines_yellow, normals_yellow)
        #self.detector.drawNormals(lines_red, normals_red)

        # Convert to position in original resolution, and add segments to segmentList
        segmentList = SegmentList()
        arr_cutoff = np.array((0, self.top_cutoff, 0, self.top_cutoff))
        arr_ratio = np.array((1.*wid_original/self.wid_image, 1.*hei_original/self.hei_image, 1.*wid_original/self.wid_image, 1.*hei_original/self.hei_image))
  
        if len(lines_white)>0:
            rospy.loginfo("[LineDetectorNode] number of white lines = %s" %(len(lines_white)))
            lines_white = ((lines_white + arr_cutoff) * arr_ratio).astype('int')
            segmentList.segments.extend(self.toSegmentMsg(lines_white, normals_white, Segment.WHITE, wid_original, hei_original))
        if len(lines_yellow)>0:
            rospy.loginfo("[LineDetectorNode] number of yellow lines = %s" %(len(lines_yellow)))
            lines_yellow = ((lines_yellow + arr_cutoff) * arr_ratio).astype('int')
            segmentList.segments.extend(self.toSegmentMsg(lines_yellow, normals_yellow, Segment.YELLOW, wid_original, hei_original))
        if len(lines_red)>0:
            rospy.loginfo("[LineDetectorNode] number of red lines = %s" %(len(lines_red)))
            lines_red = ((lines_red + arr_cutoff) * arr_ratio).astype('int')
            segmentList.segments.extend(self.toSegmentMsg(lines_red, normals_red, Segment.RED, wid_original, hei_original))
        
        # Publish segmentList
        self.pub_lines.publish(segmentList)
         
        # Publish the frame with lines
        image_msg = self.bridge.cv2_to_imgmsg(self.detector.getImage(), "bgr8")
        self.pub_image.publish(image_msg)

    def onShutdown(self):
            rospy.loginfo("[LineDetectorNode] Shutdown.")
            
    def toSegmentMsg(self,  lines, normals, color, wid, hei):
        
        segmentMsgList = []
        for u1,v1,u2,v2,norm_u,norm_v in np.hstack((lines,normals)):
            segment = Segment()
            segment.color = color
            segment.pixels[0].u = int(u1)
            segment.pixels[0].v = int(v1)
            segment.pixels[1].u = int(u2)
            segment.pixels[1].v = int(v2)
            segment.pixels_normalized[0].x = u1/wid
            segment.pixels_normalized[0].y = v1/hei
            segment.pixels_normalized[1].x = u2/wid
            segment.pixels_normalized[1].y = v2/hei
            segment.normal.x = norm_u
            segment.normal.y = norm_v
             
            segmentMsgList.append(segment)
        return segmentMsgList

if __name__ == '__main__': 
    rospy.init_node('line_detector',anonymous=False)
    line_detector_node = LineDetectorNode()
    rospy.on_shutdown(line_detector_node.onShutdown)
    rospy.spin()

