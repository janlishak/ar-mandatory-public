from thymio_camera import ThymioCamera
from robot import ThymioController
import cv2
import time


class Metal:
    def __init__(self):
        self.camera = ThymioCamera()
        self.controller = ThymioController()
        self.current_action = "STOP"
        self.speed = 100

    def set_motors(self, values):
        self.controller.set_motors(values)

    def capture_frame_to_numpy(self):
        return self.camera.read_frame()

    def update(self):
        pass

    def perform_action(self, action: str):
        self.controller.perform_action(action, self.speed)


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

