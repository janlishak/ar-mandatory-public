import time
import numpy as np
from robot2 import ThymioController
import threading

SEEKER = 0
AVOIDER = 1

class behaviouralModule:
    def __init__(self,
                 thymio,
                 max_speed=80,
                 thresholds={"robot": 1200, "black-line": 150, "safe-zone": 800, "front": 2000},
                 debug=False,
                 robot_type=AVOIDER):
        self.max_speed = max_speed
        self.thymio = thymio
        self.thresholds = thresholds
        self.debug = debug
        self.robot_type = robot_type
        self.last_collision_time = 0
        self.collision_timeout = 2
        thymio.set_motors([0, 0])

    def set_motor_speed(self, left_motor, right_motor):
        self.thymio.set_motors([left_motor, right_motor])

    def update(self):
        front_sensors = np.array(self.thymio.horizontal_sensors[:5])
        # back_sensors = np.array(self.thymio.horizontal_sensors[5:])
        ground_sensors = np.array(self.thymio.ground_sensors)
        #print(front_sensors)

        # Something blocking the way
        if (front_sensors > self.thresholds["front"]).any():
            self.set_motor_speed(0, 0)
            if self.debug: print("Blocked")
            self.last_collision_time = time.time()
            time.sleep(0.5)
            controller.is_safe = False
            return

        # Line in front
        if (ground_sensors < self.thresholds["black-line"]).all():
            self.set_motor_speed(self.max_speed//2, -self.max_speed//2)
            if self.debug: print("Black line in front -> Turning 180.")
            self.last_collision_time = time.time()
            time.sleep(1)
            controller.is_safe = False
            return

        # Black line to the left
        if ground_sensors[0] < self.thresholds["black-line"]:
            # Turn slightly to the right
            if self.debug: print("Black line at left -> Turning right.")
            self.set_motor_speed(self.max_speed//2, -self.max_speed//2)
            self.last_collision_time = time.time()
            controller.is_safe = False
            return

        # Black line to the right
        if ground_sensors[1] < self.thresholds["black-line"]:
            if self.debug: print("Black line at right -> Turning left.")
            self.set_motor_speed(-self.max_speed//2, self.max_speed//2)
            self.last_collision_time = time.time()
            controller.is_safe = False
            return
        
        if (ground_sensors > self.thresholds["safe-zone"]).all():
            print("We are safe!")
            controller.is_safe = True

        controller.is_safe = True
        current_time = time.time()
        time_since_collision = current_time - self.last_collision_time

        if self.robot_type == AVOIDER:
            if time_since_collision > self.collision_timeout:
                # No collision in the last 2 seconds, go full speed
                self.set_motor_speed(self.max_speed, self.max_speed)
            else:
                # Recent collision, reduce speed to half
                self.set_motor_speed(self.max_speed//2, self.max_speed//2)


if __name__ == "__main__":
    controller = ThymioController()
    print("LED set to green")
    controller.set_led([0, 32, 0])  # Set the LED to GREEN
    time.sleep(3)
    controller.set_led([0, 0, 255])  # Set the LED to BLUE
    b = behaviouralModule(controller, debug=True, max_speed=300, robot_type=AVOIDER)
    def behavior_loop():
        while True:
            b.update()
            time.sleep(0.2)
    thread = threading.Thread(target=behavior_loop, daemon=True)
    thread.start()

    # Wait and shutdown
    time.sleep(120)
    controller.set_led([32, 32, 0])  # Set the LED to yellow
    time.sleep(1)
    controller.stop()
    print("Controller stopped")