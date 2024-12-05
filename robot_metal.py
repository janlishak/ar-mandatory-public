from thymio_camera import ThymioCamera
from robot import ThymioController
import cv2


class Metal:
    def __init__(self):
        self.camera = ThymioCamera()
        self.controller = ThymioController()
        self.current_action = "STOP"

    def set_motors(self, values):
        self.controller.set_motors(values)

    def capture_frame_to_numpy(self):
        return self.camera.read_frame()

    def update(self):
        pass

    def perform_action(self, action: str):
        if action == "LEFT":
            self.set_motors([0, 50])
            self.current_action = action
            return
        if action == "RIGHT":
            self.set_motors([50, 0])
            self.current_action = action
            return
        if action == "FORWARD":
            self.set_motors([50, 50])
            self.current_action = action
            return
        if action == "STOP":
            self.set_motors([0, 0])
            self.current_action = "STOP"
            return

        print("Invalid action!")
        self.set_motors([0, 0])


if __name__ == '__main__':
    metal = Metal()

    # Capture a single image
    image = metal.capture_frame_to_numpy()
    image = cv2.resize(image, (640, 480), interpolation=cv2.INTER_AREA)
    image = cv2.flip(image, 0)

    # Save the image using OpenCV
    filename = "metal-test1.jpg"
    cv2.imwrite(filename, image)
    print(f"Image saved as {filename}")

