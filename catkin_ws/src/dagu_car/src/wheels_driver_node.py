#!/usr/bin/env python
import rospy
from duckietown_msgs.msg import WheelsCmdStamped
from dagu_car.dagu_wheels_driver import DaguWheelsDriver

class WheelsDriverNode(object):
    def __init__(self):
        self.node_name = rospy.get_name()
	rospy.loginfo( "HELLO ARIIIII")
        rospy.loginfo("[%s] Initializing " %(self.node_name))

        # Setup publishers
        self.driver = DaguWheelsDriver()

        # Setup subscribers
        self.sub_topic = rospy.Subscriber("~wheels_cmd", WheelsCmdStamped, self.cbWheelsCmd, queue_size=1)

    def setupParam(self,param_name,default_value):
        value = rospy.get_param(param_name,default_value)
        rospy.set_param(param_name,value) #Write to parameter server for transparancy
        rospy.loginfo("[%s] %s = %s " %(self.node_name,param_name,value))
        return value

    def cbWheelsCmd(self,msg):
        self.driver.setWheelsSpeed(left=-msg.vel_right,right=-msg.vel_left)

    def on_shutdown(self):
        self.driver.setWheelsSpeed(left=0.0,right=0.0)
        rospy.loginfo("[%s] Shutting down."%(rospy.get_name()))

if __name__ == '__main__':
    # Initialize the node with rospy
    rospy.init_node('wheels_driver_node', anonymous=False)
    # Create the DaguCar object
    node = WheelsDriverNode()
    # Setup proper shutdown behavior 
    rospy.on_shutdown(node.on_shutdown)
    # Keep it spinning to keep the node alive
    rospy.spin()
