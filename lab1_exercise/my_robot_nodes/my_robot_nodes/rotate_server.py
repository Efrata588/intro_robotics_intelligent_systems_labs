#!/usr/bin/env python3
"""Turn the robot by a requested angle using odometry yaw."""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate


def yaw_from_quaternion(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


def wrapped_difference(current, previous):
    return math.atan2(
        math.sin(current - previous),
        math.cos(current - previous),
    )


class RotateServer(Node):

    def __init__(self):
        super().__init__("rotate_server")
        self.declare_parameter("turn_speed", 0.5)
        self.yaw = None

        group = ReentrantCallbackGroup()
        self.cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(
            Odometry, "odom", self.on_odom, 10, callback_group=group
        )
        self.action_server = ActionServer(
            self,
            Rotate,
            "rotate",
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=lambda goal_handle: CancelResponse.ACCEPT,
            callback_group=group,
        )

    def on_odom(self, msg):
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def on_goal(self, goal):
        if goal.angle == 0.0 or self.yaw is None:
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def execute(self, goal_handle):
        target = float(goal_handle.request.angle)
        previous_yaw = self.yaw
        turned = 0.0
        feedback = Rotate.Feedback()
        result = Rotate.Result()

        self.get_logger().info(f"Rotating {target:.2f} rad")
        while rclpy.ok() and abs(turned) < abs(target):
            if goal_handle.is_cancel_requested:
                self.cmd_vel.publish(Twist())
                result.turned = turned
                goal_handle.canceled()
                return result

            current_yaw = self.yaw
            if current_yaw is None:
                self.cmd_vel.publish(Twist())
                time.sleep(0.05)
                continue

            turned += wrapped_difference(current_yaw, previous_yaw)
            previous_yaw = current_yaw

            command = Twist()
            command.angular.z = math.copysign(
                self.get_parameter("turn_speed").value,
                target,
            )
            self.cmd_vel.publish(command)
            feedback.turned = turned
            goal_handle.publish_feedback(feedback)
            time.sleep(0.05)

        self.cmd_vel.publish(Twist())
        result.turned = turned
        goal_handle.succeed()
        self.get_logger().info(f"Rotation complete at {turned:.2f} rad")
        return result


def main():
    rclpy.init()
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
