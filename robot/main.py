from robot2 import ThymioController
from BehaviouralModule import behaviouralModule
import time
import threading

if __name__ == "__main__":

    robot_type = "AVOIDER" ## SET HERE THE ROBOT TYPE

    controller = ThymioController(robot_type=robot_type)
    print("LED set to WHITE")
    controller.set_led([255, 255, 255])  # Set the LED to WHITE
    time.sleep(0.5)
    if robot_type == "SEEKER":
        controller.set_led([0, 0, 255])  # Set the LED to BLUE
    else:
        controller.set_led([255, 0, 0])  # Set the LED to RED
    
    b = behaviouralModule(controller, debug=True, max_speed=0, robot_type=robot_type)
    def behavior_loop():
        while True:
            b.update()
            time.sleep(0.2)
    thread = threading.Thread(target=behavior_loop, daemon=True)
    thread.start()

    # Wait and shutdown
    time.sleep(200)
    controller.set_led([32, 32, 0])  # Set the LED to yellow
    time.sleep(1)
    controller.stop()
    print("Controller stopped")