#!/usr/bin/env python3
"""Drive four sides of a square using the drive and rotate actions."""

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Twist
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):

    def __init__(self):
        super().__init__("square_driver")
        self.declare_parameter("side_length", 0.5)
        self.drive_client = ActionClient(self, DriveDistance, "drive_distance")
        self.rotate_client = ActionClient(self, Rotate, "rotate")
        self.cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)

    def send_drive(self, distance):
        self.drive_client.wait_for_server()
        goal = DriveDistance.Goal()
        goal.distance = distance
        goal_future = self.drive_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future)
        goal_handle = goal_future.result()
        if not goal_handle.accepted:
            return None

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return result_future.result()

    def send_rotate(self):
        self.rotate_client.wait_for_server()
        goal = Rotate.Goal()
        goal.angle = 1.57079632679
        goal_future = self.rotate_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future)
        goal_handle = goal_future.result()
        if not goal_handle.accepted:
            return None

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return result_future.result()

    def run_square(self):
        side_length = self.get_parameter("side_length").value
        for side in range(1, 5):
            drive_result = self.send_drive(side_length)
            if drive_result is None or drive_result.status != GoalStatus.STATUS_SUCCEEDED:
                self.stop()
                self.get_logger().error(f"Drive goal failed on side {side}")
                return

            rotate_result = self.send_rotate()
            if rotate_result is None or rotate_result.status != GoalStatus.STATUS_SUCCEEDED:
                self.stop()
                self.get_logger().error(f"Rotate goal failed after side {side}")
                return

        self.get_logger().info("Square completed")
        self.stop()

    def stop(self):
        self.cmd_vel.publish(Twist())


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        node.run_square()
    except (KeyboardInterrupt, ExternalShutdownException):
        node.stop()
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
