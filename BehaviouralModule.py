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
                 image_settings={"height": 240, "width": 320, "min_area": 1500, "blr": 3},
                 debug=False,
                 robot_type=AVOIDER):
        self.max_speed = max_speed
        self.thymio = thymio
        self.image_settings = image_settings
        self.thresholds = thresholds
        self.debug = debug
        self.robot_type = robot_type
        self.last_collision_time = 0
        self.last_random = 0
        self.random_timeout = 4
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
            self.set_motor_speed(self.max_speed, -self.max_speed)
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
            if self.robot_type == AVOIDER:
                print(ground_sensors)
                print("We are safe!")
                controller.is_safe = True
                controller.set_led([0,255,0])
                time.sleep(1)
                self.set_motor_speed(0, 0)
                time.sleep(2)
                #controller.running = False
                self.set_motor_speed(self.max_speed, self.max_speed)
                controller.set_led([0,0,255])
            else:
                controller.set_led([225,165,0])

        controller.is_safe = True
        current_time = time.time()
        time_since_collision = current_time - self.last_collision_time
        time_since_last_random = current_time - self.last_random
        #self.set_motor_speed(self.max_speed, self.max_speed)
        
        if self.robot_type == AVOIDER:
            if time_since_collision > self.collision_timeout:
                # No collision in the last 2 seconds, go full speed
                self.set_motor_speed(self.max_speed, self.max_speed)
            else:
                # Recent collision, reduce speed to half
                self.set_motor_speed(self.max_speed//2, self.max_speed//2)

        else:
            # TODO: Follow things with camera
            result = controller.process_image(**self.image_settings)
            sp = int((abs(result - 80) / 80) * 500)
            if not result:
                print("Nothing to see")
                if time_since_last_random > self.random_timeout:
                    print("We are going random")
                    r = np.random.random()
                    self.last_random = time.time()
                    if r < 0.5:
                        self.set_motor_speed(0, self.max_speed)
                        time.sleep(0.1)
                    else:
                        self.set_motor_speed(self.max_speed, 0)
                        time.sleep(0.1)
                
            elif result < 80:
                print("Objective to left")
                self.set_motor_speed(0, sp)
                time.sleep(0.5)
            elif result > 80:
                print("Objective to right")
                self.set_motor_speed(sp, 0)
                time.sleep(0.5)
            else:
                print("Objective in front")
                self.set_motor_speed(self.max_speed, self.max_speed)
                time.sleep(0.5)
                
            self.set_motor_speed(self.max_speed, self.max_speed)
            #self.set_motor_speed(0, 0)

if __name__ == "__main__":

    robot_type = SEEKER ## SET HERE THE ROBOT TYPE
    controller = ThymioController()
    print("LED set to WHITE")
    controller.set_led([255, 255, 255])  # Set the LED to WHITE
    time.sleep(0.5)
    if robot_type == AVOIDER:
        controller.set_led([0, 0, 255])  # Set the LED to BLUE
    else:
        controller.set_led([255, 0, 0])  # Set the LED to RED
    
    b = behaviouralModule(controller, debug=True, max_speed=500, robot_type=robot_type)
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