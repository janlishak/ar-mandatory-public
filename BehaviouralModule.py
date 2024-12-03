import time

import numpy as np

from robot import ThymioController


class FakeCamera:
    def __init__(self):
        pass

    def robot_in_view(self):
        return False
        # return np.random.random() > 0.1

class behaviouralModule:

    def __init__(self, thymio, max_speed=500, robot_threshold=100, thresholds={"robot": 1200, "black-line": 40, "safe-zone": 1200, "surface": 400}, debug=False, type="avoider"):
        self.max_speed = max_speed
        self.thymio = thymio
        thymio.set_motors([0,0])
        self.thresholds = thresholds
        self.debug = debug
        self.robot_type = type

    # def get_motor_speed(self):
    #     return self.motor_speed
    
    def set_motor_speed(self, left_motor, right_motor):
        self.thymio.set_motors([left_motor, right_motor])


    def react(self, camera, signal):
        front_sensors = np.array(self.thymio.horizontal_sensors[:5])
        back_sensors = np.array(self.thymio.horizontal_sensors[5:])
        ground_sensors = np.array(self.thymio.ground_sensors)
        
        if self.robot_type == "avoider":
            ## CHECK FOR LINE ##
            # Line in front
            if (ground_sensors < self.thresholds["black-line"]).all():
                # Somebody in our backs?
                if (back_sensors > self.thresholds["robot"]).any():
                    # Then turn either left or right
                    if np.random.random() < 0.5:
                        if self.debug: print("Black line in front, robot in the back -> Turning right.")
                        self.set_motor_speed(self.max_speed, -self.max_speed//2)
                    else:
                        if self.debug: print("Black line in front, robot in the back -> Turning left.")
                        self.set_motor_speed(-self.max_speed//2, self.max_speed)
                # Else nobody in our tails
                else:
                    # 180 Turn
                    if self.debug: print("Black line in front, nobody in the back -> Turning 180.")
                    self.set_motor_speed(self.max_speed, -self.max_speed)
                
            # Black line to the left
            elif ground_sensors[0] < self.thresholds["black-line"]:
                # Turn slightly to the right
                if self.debug: print("Black line at left -> Turning right.")
                self.set_motor_speed(self.max_speed//2, 0)
            # Black line to the right
            elif ground_sensors[1] < self.thresholds["black-line"]:
                if self.debug: print("Black line at right -> Turning left.")
                self.set_motor_speed(0, self.max_speed//2)

            # If we are in the safe zone, and not receiving a signal, stay there
            if (ground_sensors).all() & (not signal):
                self.set_motor_speed(0, 0)

            ## ROBOTS BY CAMERA ##
            if camera.robot_in_view():
                # Robot somewhere in the front, turn slightly left or right
                if np.random.random() < 0.5:
                    self.set_motor_speed(self.max_speed//4, 0)
                else:
                    self.set_motor_speed(0, self.max_speed//4)

            ## OTHER ROBOTS ##
            # If robot is in front
            elif (front_sensors > self.thresholds["robot"]).any():
                # Robot to the left
                if np.argmin(front_sensors) == 0:
                    # Move sharp right
                    if self.debug: print("No black line, robot to the left -> Moving right.")
                    self.set_motor_speed(0, -self.max_speed)
                # Robot to the right
                elif np.argmin(front_sensors) == 4:
                    # Move sharp left
                    if self.debug: print("No black line, robot to the right -> Moving left.")
                    self.set_motor_speed(-self.max_speed, 0)
                # Robot right in front!
                else:
                    # 180 Turn
                    if self.debug: print("No black line, robot right in front -> Turning 180.")
                    self.set_motor_speed(-self.max_speed, self.max_speed)
            # Else there is no robot seen by the sensors
            else:
                # move forward
                if self.debug: print("No black line, no robots in front -> Moving forward.")
                self.set_motor_speed(self.max_speed, self.max_speed)
                pass
        
        else: # Then seeker
            ## CHECK FOR LINE ##
            # Line in front
            if (ground_sensors < self.thresholds["black-line"]).all():
                if self.debug: print("Black line in front. -> Turning 180.")
                self.set_motor_speed(-self.max_speed, self.max_speed)
                # Else nobody in our tails
                
            # Black line to the left
            elif ground_sensors[0] < self.thresholds["black-line"]:
                # Turn sharply to the right
                if self.debug: print("Black line at left -> Turning right.")
                self.set_motor_speed(self.max_speed, 0)
            # Black line to the right
            elif ground_sensors[1] < self.thresholds["black-line"]:
                if self.debug: print("Black line at right -> Turning left.")
                self.set_motor_speed(0, self.max_speed)

            ## ROBOTS BY CAMERA ##
            if camera.robot_in_view():
                # Robot somewhere in the front, follow it
                # TODO
                pass

            # Else there is no robot seen by the sensors
            else:
                # move forward
                if self.debug: print("No black line, no robots in front -> Moving randomly.")
                self.set_motor_speed(np.random.randint(0, self.max_speed), np.random.randint(0, self.max_speed))
                pass


# b = behaviouralModule(debug=True)
# 
# 
# tests = {
#     "line_in_front": np.array([500,500,500,500,500,500,500,20,20]),
#     "line_at_left": np.array([500,500,500,500,500,500,500,20,100]),
#     "line_at_right": np.array([500,500,500,500,500,500,500,100,20]),
#     "line_in_front_robot_back": np.array([500,500,500,500,500,1500,100,20,20]),
#     "no-line-robot-front": np.array([500,500,500,500,500,1500,1500,500,500]),
#     "no-line-no-robot": np.array([500,500,500,500,500,500,500,400,400]),
# }
# 
# cam = Camera()
# 
# for test, vals in tests.items():
# 
#     print(f"TESTING: {test}\n")
# 
#     print(b.get_motor_speed())
#     b.react(sensors=vals, camera=cam, signal=None)
#     print(b.get_motor_speed())
#     print("\n\n")


if __name__ == "__main__":
    controller = ThymioController()

    print("LED set to green")
    controller.set_led([0, 32, 0])  # Set the LED to green
    time.sleep(3)

    b = behaviouralModule(controller, debug=True)
    c = FakeCamera()

    while True:
        b.react(c, None)
        time.sleep(0.5)

    print("LED set to yellow")
    controller.set_led([32, 32, 0])  # Set the LED to yellow
    time.sleep(1)

    # Stop the controller when done
    controller.stop()
    print("Controller stopped")