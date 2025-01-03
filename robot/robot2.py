import time
import threading
from thymio_camera import ThymioCamera
from tdmclient import ClientAsync
import cv2
import numpy as np

AVOIDER = """
# Variables must be at start
var send_interval = 200  # time in milliseconds
var signal_detected = 0  # For storing received signal
var reset_delay = 500   # Reset after 500ms

# Enable communication first
call prox.comm.enable(1)

# Initialize timer
timer.period[0] = send_interval

# Set constant transmission
onevent timer0
    prox.comm.tx = 2  # Continuously send 2
    
# Force update rx value in every timer tick
    if prox.comm.rx == 0 then
        signal_detected = 0
    end

onevent prox.comm
    signal_detected = prox.comm.rx
    if signal_detected != 0 then
        timer.period[1] = reset_delay
    end

onevent timer1
    prox.comm.rx = 0  # Force reset rx
    signal_detected = 0
    timer.period[1] = 0
"""

SEEKER = """
# Variables must be at start
var send_interval = 200  # time in milliseconds
var signal_detected = 0  # For storing received signal
var reset_delay = 500   # Reset after 500ms

# Enable communication first
call prox.comm.enable(1)

# Initialize timer
timer.period[0] = send_interval

# Set constant transmission
onevent timer0
    prox.comm.tx = 1 # Continuously send 1
    
# Force update rx value in every timer tick
    if prox.comm.rx == 0 then
        signal_detected = 0
    end

onevent prox.comm
    signal_detected = prox.comm.rx
    if signal_detected != 0 then
        timer.period[1] = reset_delay
    end

onevent timer1
    prox.comm.rx = 0  # Force reset rx
    signal_detected = 0
    timer.period[1] = 0
"""

class ThymioController:
    def __init__(self, robot_type):
        self.motor_values = [0, 0]  # Default motor values
        self.led_values = [0, 0, 255]  # Default LED values
        self.running = True
        self.horizontal_sensors = None
        self.ground_sensors = None
        # Start the background thread that will run the Thymio control loop
        self.thread = threading.Thread(target=self.run_background, daemon=True)
        self.thread.start()
        if robot_type == "SEEKER":
            self.program = SEEKER
        else:
            self.program = AVOIDER
        self.robot_type = robot_type
        self.is_safe = False
        self.camera = ThymioCamera()
        self.img_id = 0


    def process_image(self, height=120, width=160, min_area=1500, blr=3, ):

        # warning - mutation of frame
        frame = self.camera.read_frame()
        frame = cv2.resize(frame, (width, height))

        if blr%2 == 0:
            blr+=1

        blurred_image = cv2.GaussianBlur(frame, (blr, blr), 0)

        # Convert the image to HSV
        hsv_image = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2HSV)

        # Define the blue color range
        lower_blue = np.array([110, 50, 50])
        upper_blue = np.array([130, 255, 255])

        mask = cv2.inRange(hsv_image, lower_blue, upper_blue)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Initialize variables to find the largest contour
        largest_contour = None

        if contours:
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)

            area = cv2.contourArea(largest_contour)
            if area > min_area:  # Only consider contours above a certain area threshold
            
                # Calculate moments to find the centroid
                M = cv2.moments(largest_contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])  # X coordinate of centroid
                    cy = int(M['m01'] / M['m00'])  # Y coordinate of centroid
                    print(f"Centroid of the robot: ({cx}, {cy})")
                    
                    # Draw the contour and centroid on the original image
                    cv2.drawContours(blurred_image, [largest_contour], -1, (0, 255, 0), 3)
                    cv2.circle(blurred_image, (cx, cy), 25, (255, 0, 0), -1)
                    self.img_id += 1
                    cv2.imwrite(f"../../image{self.img_id}.jpg", blurred_image)
                    return cx
                else:
                    pass
                    print("No centroid found due to zero area.")
            else:
                pass
                print("No blue robot detected.")

        return False
    

    def run_background(self):
        # Use the ClientAsync context manager to handle the connection to the Thymio robot.
        with ClientAsync() as client:
            async def prog():
                with await client.lock() as node:

                    # Compile and send the program to the Thymio.
                    error = await node.compile(self.program) ## IR MODULE
                    if error is not None:
                        print(f"Compilation error: {error['error_msg']}")
                    else:
                        error = await node.run()
                        if error is not None:
                            print(f"Error {error['error_code']}")

                    # Wait for the robot's proximity sensors to be ready.
                    await node.wait_for_variables({"prox.horizontal"})

                    node.send_set_variables({"leds.top": [0, 0, 32]})
                    print("Thymio started successfully!")
                    while self.running:

                        message = node.v.prox.comm.rx
                        print(f"I'm a {self.robot_type} | Message receving: {message}; Sending: {node.v.prox.comm.tx}")

                        if (message == 1) and (self.robot_type == "AVOIDER"):
                            print(f"I'M SO ASHAMED!! (msg={message})")
                            node.v.motor.left.target = 0
                            node.v.motor.right.target = 0
                            node.v.leds.top = [32, 0, 32]
                            node.v.leds.bottom.left = [32, 0, 32]
                            node.v.leds.bottom.right = [32, 0, 32]
                            break

                        # Testing explore
                        # self.explore()
                        # Apply the latest motor and LED values
                        node.v.motor.left.target = self.motor_values[0]
                        node.v.motor.right.target = self.motor_values[1]
                        node.v.leds.top = self.led_values
                        node.v.leds.bottom.left = self.led_values
                        node.v.leds.bottom.right = self.led_values
                        # Pass the sensors to the robot
                        h = node.v.prox.horizontal
                        self.horizontal_sensors = [h[0], h[1], h[2], h[3], h[4], h[5], h[6]]
                        g = node.v.prox.ground.reflected
                        self.ground_sensors = [g[0], g[1]]
                        # Apply changes to the Thymio
                        node.flush()
                        # Sleep for 0.1 seconds to prevent overloading
                        time.sleep(0.1)

                    # Once out of the loop, stop the robot and set the top LED to red.
                    print("Thymio stopped successfully!")
                    node.v.motor.left.target = 0
                    node.v.motor.right.target = 0
                    #node.v.leds.top = [32, 0, 0]
                    node.flush()

            # Run the asynchronous function to control the Thymio.
            client.run_async_program(prog)


    def set_motors(self, values):
        self.motor_values = values

    def set_led(self, values):
        self.led_values = values

    def stop(self):
        self.running = False
        self.thread.join()

    def perform_action(self, action: str, speed: int = 100):
        print("taking::" + action)
        # Keep speed within motor ranges
        if speed > 500:
            speed = 500
        elif speed < -500:
            speed = -500

        if action == "LEFT":
            self.set_motors([0, speed])
            return
        if action == "RIGHT":
            self.set_motors([speed, 0])
            return
        if action == "FORWARD":
            self.set_motors([speed, speed])
            return
        if action == "STOP":
            self.set_motors([0, 0])
        else:
            print("Invalid action!")
            self.set_motors([0, 0])

    def explore(self):

        whereami = self.detect_surface()

        if whereami == "safe-zone":
            self.perform_action("STOP")
        elif whereami == "safe-zone-left":
            self.perform_action("LEFT", 50)
        elif whereami == "safe-zone-right":
            self.perform_action("RIGHT", 50)
        elif whereami == "black-tape":
            self.perform_action("LEFT", 250)
        elif whereami == "black-tape-left":
            self.perform_action("RIGHT", 150)
        elif whereami == "black-tape-right":
            self.perform_action("LEFT", 150)
        else:  ## JUST MOVE AHEAD
            self.perform_action("FORWARD", 500)

        return

    def detect_surface(self):
        ## First, check where you are standing
        if (self.ground_sensors[0] > 900) & (self.ground_sensors[1] > 900):  # Safe zone
            return "safe-zone"
        elif (self.ground_sensors[0] > 900):  # Safe zone to the left
            return "safe-zone-left"
        elif (self.ground_sensors[1] > 900):
            return "safe-zone-right"
        elif (self.ground_sensors[0] < 400) & (self.ground_sensors[1] < 400):  # Black tape
            return "black-tape"
        elif (self.ground_sensors[0] < 400):
            return "black-tape-left"
        elif (self.ground_sensors[0] < 400):
            return "black-tape-right"
        else:
            return "open-ground"


def test1():
    print("Motors set to [100, -100]")
    controller.set_motors([100, -100])
    time.sleep(1)

    print("Motors set to [-100, 100]")
    controller.set_motors([-100, 100])
    time.sleep(1)

    print("Motors set to [50, -50]")
    controller.set_motors([50, -50])
    time.sleep(1)

    print("Motors set to [-50, 50]")
    controller.set_motors([-50, 50])
    time.sleep(1)

    print("Motors set to [50, 50]")
    controller.set_motors([50, 50])
    time.sleep(1)


def test2():
    print("Turn Right")
    controller.perform_action("RIGHT")
    time.sleep(1)

    print("Turn Left")
    controller.perform_action("LEFT")
    time.sleep(1)

    print("Forward")
    controller.perform_action("FORWARD")
    time.sleep(1)


def test3():
    controller.set_motors([200, 200])
    time.sleep(120)


if __name__ == "__main__":
    controller = ThymioController()

    print("LED set to green")
    controller.set_led([0, 32, 0])  # Set the LED to green
    time.sleep(2)

    # RUN TEST
    # test1()
    # todo: run test2
    test3()

    print("LED set to yellow")
    controller.set_led([32, 32, 0])  # Set the LED to yellow
    time.sleep(1)

    # Stop the controller when done
    controller.stop()
    print("Controller stopped")