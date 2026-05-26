import rclpy
from rclpy.node import Node
from custom_interface.msg import Target
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import time


class Controller(Node):
    def __init__(self):
        super().__init__('controller')

        # 지정된 차량 정보를 받아올 subscription
        self.car_info_subscription_ = self.create_subscription(
            Target,
            'start_car',
            self.car_info_listener_callback,
            10)

        # 카메라, 라이다 정보를 처리하는 노드에 차량 정보를 전달하는 publisher
        self.car_info_publisher = self.create_publisher(
            String,
            'car_info',
            10
        )

        # line_follower 노드로부터 차량에 전달할 속도 정보를 받아오는 subscription
        self.twist_subscription = self.create_subscription(
            Twist,
            'twist_info',
            self.twist_listener_callback,
            10
        )

        # line_follower 노드로부터 차량 상태(직진, 회전) 정보를 받아오는 subscription
        self.drive_issue_subscription = self.create_subscription(
            String,
            'drive_issue',
            self.drive_issue_listener_callback,
            10
        )

        # 정지선 검출 정보를 받아오는 subscription
        self.stop_issue_subscription = self.create_subscription(
            String,
            'stop_issue',
            self.stop_issue_listener_callback,
            10
        )

        # 종료 지점 검출 정보를 받아오는 subscription
        self.end_issue_subscription = self.create_subscription(
            String,
            'end_issue',
            self.end_issue_listener_callback,
            10
        )

        # 초기화
        self.twist_publisher_ = None

        # 회전 여부
        self.turn = False
        # 정지 여부
        self.stop = False
        # 정지선 종류 구분
        self.count = 0

    def car_info_listener_callback(self, msg: Target):
        # 지정 차량
        car = msg.car
        self.get_logger().info('I heard: "%s"' % msg.car)

        time.sleep(5)

        # 차량에 속도 정보를 전달할 publisher
        self.twist_publisher_ = self.create_publisher(Twist, '/demo/' + car + '_cmd_demo', 10)

        # 차량 출발
        twist = Twist()
        for i in range(200):
            twist.linear.x = 3.0  # 초기 속도 낮게 설정
            self.twist_publisher_.publish(twist)
            time.sleep(0.01)

        # 카메라, 라이다 정보를 처리하는 노드들에 차량 정보 전달
        car_info_msg = String()
        car_info_msg.data = car
        self.car_info_publisher.publish(car_info_msg)

    def twist_listener_callback(self, twist: Twist):
        # 차선을 따라 주행하기 위한 속도 정보 전달
        if not self.stop:
            self.twist_publisher_.publish(twist)

    def drive_issue_listener_callback(self, msg: String):
        if msg.data == '직진':
            self.turn = False
        elif msg.data == '회전':
            self.turn = True

    def stop_issue_listener_callback(self, msg: String):
        # 언덕 정지선
        if msg.data == '정지' and not self.turn and not self.stop and self.count == 1:
            self.stop = True
            self.count += 1

            twist = Twist()
            twist.angular.y = 0.0

            # 차량이 밀리지 않도록
            for i in range(3500):
                twist.linear.x = 1.3
                self.twist_publisher_.publish(twist)
                time.sleep(0.001)

            self.stop = False

            # 차량 출발
            for i in range(2000):
                twist.linear.x = 6.0
                self.twist_publisher_.publish(twist)
                time.sleep(0.001)

        # 평지 정지선
        if msg.data == '정지' and not self.turn and not self.stop and self.count == 0:
            self.stop = True
            self.count += 1
            twist = Twist()

            # 3초간 정지
            for i in range(400):
                twist.linear.x = 0.0
                self.twist_publisher_.publish(twist)
                time.sleep(0.01)

            # 차량 출발
            for i in range(200):
                twist.linear.x = 6.0
                self.twist_publisher_.publish(twist)
                time.sleep(0.01)

            self.stop = False

    def end_issue_listener_callback(self, msg: String):
        if msg.data == '종료':
            self.stop = True
            self.get_logger().info('종료 지점 도달: 차량 정지')

            twist = Twist()
            for i in range(100):
                twist.linear.x = 0.0
                self.twist_publisher_.publish(twist)
                time.sleep(0.01)

            self.destroy_node()


def main(args=None):
    rclpy.init(args=args)

    controller = Controller()

    rclpy.spin(controller)

    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()