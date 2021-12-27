#!/usr/bin/env python
'''
Publishes current lat/lon as NMEA msg for Fledermaus Vessel Manager

'''

# System imports
from math import *

# ROS/Gazebo imports
import rospy
import tf
from frl_vehicle_msgs.msg import UwGliderStatus

# For UDP connection
import socket

# For NMEA msg format
import pynmea2
# This script is writing GPGGA standard format
# $GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
# 1    = UTC of Position
# 2    = Latitude
# 3    = N or S
# 4    = Longitude
# 5    = E or W
# 6    = GPS quality indicator (0=invalid; 1=GPS fix; 2=Diff. GPS fix)
# 7    = Number of satellites in use [not those in view]
# 8    = Horizontal dilution of position
# 9    = Antenna altitude above/below mean sea level (geoid)
# 10   = Meters  (Antenna height unit)
# 11   = Geoidal separation (Diff. between WGS-84 earth ellipsoid and
#        mean sea level.  -=geoid is below WGS-84 ellipsoid)
# 12   = Meters  (Units of geoidal separation)
# 13   = Age in seconds since last update from diff. reference station
# 14   = Diff. reference station ID#
# 15   = Checksum

UDP_IP = "127.0.0.1"
UDP_PORT = 30362  # default port of the Vessel Manager

def ddToddm(deg):
     d = int(deg)
     dm = abs(deg - d) * 60
     return "%i%f" % (d, dm)

def sTohhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i%02i%02i" % (hours, minutes, seconds)


class Node():
    def __init__(self):
        # Keep track of time and depth
        self.t0 = rospy.get_time()
        while self.t0 < 0.01:
            rospy.logwarn("Waiting for ROS tme to be received")
            rospy.sleep(0.5)
            self.t0 = rospy.get_time()
            self.t0_init = self.t0
        self.d0 = None

        # Init messages
        self.sim_msg = UwGliderStatus()

        # Initiate socket for UDP connection
        self.sock = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM) # UDP

    def publish_NMEA(self):
        # Timing
        now = rospy.get_time()
        dt = now - self.t0
        if dt < 1.0e-3:
            # rospy.logwarn("Timestep is too small (%f) - skipping this update"
            #               %dt)
            return
        sim_time = now

        # Read UwGliderStatus msg
        self.sim_msg = rospy.wait_for_message("status", UwGliderStatus)
        latitude = self.sim_msg.latitude
        longitude = self.sim_msg.longitude
        depth = self.sim_msg.depth

        msg = pynmea2.GGA('PV', 'GGA', \
            (str(sTohhmmss(sim_time)), \
            str(ddToddm(latitude)), 'N', \
            str("0" + ddToddm(-longitude)), 'W', \
            '1', '04', '', \
            str(depth), 'M', \
            '', 'M', '', '0000'))

        MESSAGE = str(msg)
        self.sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))

        return

if __name__ == '__main__':

    # Start node
    rospy.init_node('nmea_publisher')

    # Update rate
    update_rate = rospy.get_param('~update_rate', 5.0)

    # Initiate node object
    node=Node()

    # Spin
    r = rospy.Rate(update_rate)
    try:
        while not rospy.is_shutdown():
            node.publish_NMEA()
            r.sleep()
    except rospy.ROSInterruptException:
        pass
