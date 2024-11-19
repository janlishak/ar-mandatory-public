import time
import  threading
from tdmclient import ClientAsync


class ThymioController:
    def __init__(self):
        self.motor_values = [0, 0]  # Default motor values
        self.led_values = [0, 0, 0]  # Default LED values
        self.running = True
        # Start the background thread that will run the Thymio control loop
        self.thread = threading.Thread(target=self.run_background, daemon=True)
        self.thread.start()

    def run_background(self):
        # Use the ClientAsync context manager to handle the connection to the Thymio robot.
        with ClientAsync() as client:
            async def prog():
                with await client.lock() as node:

                    # Wait for the robot's proximity sensors to be ready.
                    await node.wait_for_variables({"prox.horizontal"})

                    node.send_set_variables({"leds.top": [0, 0, 32]})
                    print("Thymio started successfully!")
                    while self.running:
                        # Apply the latest motor and LED values
                        node.v.motor.left.target = self.motor_values[0]
                        node.v.motor.right.target = self.motor_values[1]
                        node.v.leds.top = self.led_values
                        # Apply changes to the Thymio
                        node.flush()
                        # Sleep for 0.1 seconds to prevent overloading
                        time.sleep(0.3)

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

    def perform_action(self, action: str):
        if action == "LEFT":
            self.set_motors([50, -50])
        if action == "RIGHT":
            self.set_motors([-50, 50])
        if action == "FORWARD":
            self.set_motors([50, 50])
        if action == "STOP":
            self.set_motors([0, 0])
        else:
            print("Invalid action!")
            self.set_motors([0, 0])

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


if __name__ == "__main__":
    controller = ThymioController()

    print("LED set to green")
    controller.set_led([0, 32, 0])  # Set the LED to green
    time.sleep(2)

    # RUN TEST
    test1()
    # todo: run test2

    print("LED set to yellow")
    controller.set_led([32, 32, 0])  # Set the LED to yellow
    time.sleep(1)

    # Stop the controller when done
    controller.stop()
    print("Controller stopped")