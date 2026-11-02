#!/usr/bin/env python3
"""Drive forward and turn away from obstacles reported by the robot."""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import SetBool

from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed


class TurnAway(Node):

    def __init__(self):
        super().__init__("turn_away")
        self.declare_parameter("forward_speed", 0.2)
        self.declare_parameter("turn_speed", 0.5)
        self.declare_parameter("max_turn_speed", 1.5)

        self.enabled = False
        self.last_distance = 0.0
        self.cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)
        self.status = self.create_publisher(RobotStatus, "robot_status", 10)
        self.create_subscription(ObstacleInfo, "obstacle", self.on_obstacle, 10)
        self.create_service(SetBool, "turn_away_enable", self.on_enable)
        self.create_service(SetTurnSpeed, "set_turn_speed", self.on_set_turn_speed)

    def on_obstacle(self, msg):
        self.last_distance = msg.distance
        forward_speed = self.get_parameter("forward_speed").value
        turn_speed = self.get_parameter("turn_speed").value

        status = RobotStatus()
        status.obstacle_distance = msg.distance
        if not self.enabled:
            status.state = "stopped"
            self.status.publish(status)
            return

        twist = Twist()
        if msg.too_close:
            twist.angular.z = -turn_speed if msg.angle > 0.0 else turn_speed
            status.state = "turning"
        else:
            twist.linear.x = forward_speed
            status.state = "forward"
        self.cmd_vel.publish(twist)
        self.status.publish(status)

    def on_enable(self, request, response):
        self.enabled = request.data
        response.success = True
        response.message = "enabled" if self.enabled else "stopped"
        if not self.enabled:
            self.cmd_vel.publish(Twist())
        self.publish_status("forward" if self.enabled else "stopped")
        return response

    def on_set_turn_speed(self, request, response):
        maximum = self.get_parameter("max_turn_speed").value
        if not 0.0 < request.turn_speed <= maximum:
            response.success = False
            response.message = f"turn speed must be above 0 and at most {maximum} rad/s"
            return response

        self.set_parameters([
            Parameter("turn_speed", value=float(request.turn_speed))
        ])
        response.success = True
        response.message = f"turn speed set to {request.turn_speed:.2f} rad/s"
        return response

    def publish_status(self, state):
        status = RobotStatus()
        status.state = state
        status.obstacle_distance = self.last_distance
        self.status.publish(status)


def main():
    rclpy.init()
    node = TurnAway()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
