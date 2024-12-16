from thymio_camera import ThymioCamera
from robot import ThymioController
import cv2
import time


class Metal:
    def __init__(self):
        self.controller = ThymioController()
        self.controller.set_motors([0,0])
        self.camera = ThymioCamera()
        self.current_action = "STOP"
        self.speed = 100

    def capture_frame_to_numpy(self):
        return self.camera.read_frame()

    def update(self):
        pass

    def perform_action(self, action: str):
        if self.controller.is_safe:
            self.controller.perform_action(action, self.speed)
        else:
            print("Robot is not safe! Seeking disabled")


def test_move_left_right_forward(metal):
    print("Turn Right")
    metal.perform_action("RIGHT")
    time.sleep(1)

    print("Turn Left")
    metal.perform_action("LEFT")
    time.sleep(1)

    print("Forward")
    metal.perform_action("FORWARD")
    time.sleep(1)


if __name__ == '__main__':
    metal = Metal()

    # Capture a single image
    image = metal.capture_frame_to_numpy()
    # image = cv2.resize(image, (640, 480), interpolation=cv2.INTER_AREA)
    # image = cv2.flip(image, 0)

    # Save the image using OpenCV
    filename = "metal-test1.jpg"
    cv2.imwrite(filename, image)
    print(f"Image saved as {filename}")

    # Test movement
    test_move_left_right_forward(metal)
    metal.perform_action("STOP")
    time.sleep(1)

