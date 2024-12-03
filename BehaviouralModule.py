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
    def __init__(self,
                 thymio,
                 max_speed=80,
                 thresholds={"robot": 1200, "black-line": 150, "safe-zone": 800, "front": 3000},
                 debug=False,
                 type="avoider"):
        self.max_speed = max_speed
        self.thymio = thymio
        self.thresholds = thresholds
        self.debug = debug
        self.robot_type = type
        self.last_collision_time = 0  # Timestamp of the last collision
        self.collision_timeout = 2

        thymio.set_motors([0, 0])

    def set_motor_speed(self, left_motor, right_motor):
        self.thymio.set_motors([left_motor, right_motor])


    def react(self, camera, signal):
        front_sensors = np.array(self.thymio.horizontal_sensors[:5])
        back_sensors = np.array(self.thymio.horizontal_sensors[5:])
        ground_sensors = np.array(self.thymio.ground_sensors)
        print(ground_sensors)
        
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
            if (ground_sensors > self.thresholds["safe-zone"]).all() & (not signal):
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

        elif self.robot_type == "avoider2":
            # Line in front
            if (ground_sensors < self.thresholds["black-line"]).all() or (front_sensors > self.thresholds["front"]).all():
                self.set_motor_speed(self.max_speed//2, -self.max_speed//2)
                if self.debug: print("Black line in front -> Turning 180.")
                self.last_collision_time = time.time()
                time.sleep(1)
                return

            # Black line to the left
            if ground_sensors[0] < self.thresholds["black-line"]:
                # Turn slightly to the right
                if self.debug: print("Black line at left -> Turning right.")
                self.set_motor_speed(self.max_speed//2, -self.max_speed//2)
                self.last_collision_time = time.time()
                return

            # Black line to the right
            if ground_sensors[1] < self.thresholds["black-line"]:
                if self.debug: print("Black line at right -> Turning left.")
                self.set_motor_speed(-self.max_speed//2, self.max_speed//2)
                self.last_collision_time = time.time()
                return


            current_time = time.time()
            time_since_collision = current_time - self.last_collision_time

            if time_since_collision > self.collision_timeout:
                # No collision in the last 2 seconds, go full speed
                self.set_motor_speed(self.max_speed, self.max_speed)
            else:
                # Recent collision, reduce speed to half
                self.set_motor_speed(self.max_speed//2, self.max_speed//2)

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


if __name__ == "__main__":
    controller = ThymioController()

    print("LED set to green")
    controller.set_led([0, 32, 0])  # Set the LED to green
    time.sleep(3)

    b = behaviouralModule(controller,
                          debug=True,
                          max_speed=300,
                          type="avoider2")
    c = FakeCamera()

    while True:
        b.react(c, None)
        time.sleep(0.2)

    print("LED set to yellow")
    controller.set_led([32, 32, 0])  # Set the LED to yellow
    time.sleep(1)

    # Stop the controller when done
    controller.stop()
    print("Controller stopped")