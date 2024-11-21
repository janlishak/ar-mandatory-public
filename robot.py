import time
import  threading
from tdmclient import ClientAsync


class ThymioController:
    def __init__(self):
        self.motor_values = [0, 0]  # Default motor values
        self.led_values = [0, 0, 0]  # Default LED values
        self.running = True
        self.horizontal_sensors = None
        self.ground_sensors = None
        # Start the background thread that will run the Thymio control loop
        #self.thread = threading.Thread(target=self.run_background, daemon=True)
        #self.thread.start()

    def run_background(self):
        # Use the ClientAsync context manager to handle the connection to the Thymio robot.
        with ClientAsync() as client:
            async def prog():
                with await client.lock() as node:

                    # Wait for the robot's proximity sensors to be ready.
                    await node.wait_for_variables({"prox.horizontal"})
                    await node.wait_for_variables({"prox.ground"})

                    node.send_set_variables({"leds.top": [0, 0, 32]})
                    print("Thymio started successfully!")
                    while self.running:
                        # Apply the latest motor and LED values
                        node.v.motor.left.target = self.motor_values[0]
                        node.v.motor.right.target = self.motor_values[1]
                        node.v.leds.top = self.led_values
                        node.v.leds.bottom.left = self.led_values
                        node.v.leds.bottom.right = self.led_values
                        # Pass the sensors to the robot
                        self.horizontal_sensors = node.v.prox.horizontal
                        self.ground_sensors = node.v.prox.ground.reflected
                        # Apply changes to the Thymio
                        node.flush()
                        # Sleep for 0.1 seconds to prevent overloading
                        time.sleep(0.3)
                        # Testing explore
                        self.explore()

                    # Once out of the loop, stop the robot and set the top LED to red.
                    print("Thymio stopped successfully!")
                    node.v.motor.left.target = 0
                    node.v.motor.right.target = 0
                    node.v.leds.top = [32, 0, 0]
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

    def perform_action(self, action: str, speed: int=100):
        # Keep speed within motor ranges
        if speed > 500:
            speed = 500
        elif speed < -500:
            speed = -500

        if action == "LEFT":
            self.set_motors([-speed, speed])
            return
        if action == "RIGHT":
            self.set_motors([speed, -speed])
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

        with ClientAsync() as client:

            async def prog():
                """
                Asynchronous function controlling the Thymio.
                """

                # Lock the node representing the Thymio to ensure exclusive access.
                with await client.lock() as node:
                    
                    # Wait for the robot's proximity sensors to be ready.
                    await node.wait_for_variables({"prox.horizontal"})
                    print("Thymio started successfully!")
                    i=0
                    while i < 20:
                        # get the values of the proximity sensors
                        self.horizontal_sensors = node.v.prox.horizontal
                        self.ground_sensors = node.v.prox.ground.reflected

                        whereami = self.detect_surface()

                        print(f"I am here {whereami}")

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
                        else: ## JUST MOVE AHEAD
                            self.perform_action("FORWARD", 500)

                        node.flush()  # Send the set commands to the robot.

                        await client.sleep(0.3)  # Pause for 0.3 seconds before the next iteration.
                        i +=1

                    # Once out of the loop, stop the robot and set the top LED to red.
                    print("Thymio stopped successfully!")
                    node.v.motor.left.target = 0
                    node.v.motor.right.target = 0
                    node.v.leds.top = [32, 0, 0]
                    node.flush()


            # Run the asynchronous function to control the Thymio.
            client.run_async_program(prog)

            

    def detect_surface(self):
        ## First, check where you are standing
        if (self.ground_sensors[0] > 900) & (self.ground_sensors[1] > 900): # Safe zone
            return "safe-zone"
        elif (self.ground_sensors[0] > 900): # Safe zone to the left
            return "safe-zone-left"
        elif (self.ground_sensors[1] > 900):
            return "safe-zone-right"
        elif (self.ground_sensors[0] < 400) & (self.ground_sensors[1] < 400): # Black tape
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
    time.sleep(3)


def test4():
    controller.run_background()


if __name__ == "__main__":
    controller = ThymioController()

    #print("LED set to green")
    #controller.set_led([0, 32, 0])  # Set the LED to green
    #time.sleep(2)

    # RUN TEST
    # test1()
    # todo: run test2
    test4()

    #print("LED set to yellow")
    #controller.set_led([32, 32, 0])  # Set the LED to yellow
    #time.sleep(1)

    # Stop the controller when done
    controller.stop()
    print("Controller stopped")