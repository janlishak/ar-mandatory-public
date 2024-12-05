import cv2
import time
from picamera2 import Picamera2


class ThymioCamera:
    def __init__(self) -> None:
        self.camera = Picamera2()
        camera_config = self.camera.create_still_configuration({
            "size": (1640, 1232),  # Full sensor resolution at a lower resolution
            "format": "RGB888"  # Fast processing format
        })
        self.camera.configure(camera_config)
        self.camera.start()

        # Get current auto settings
        time.sleep(2)
        controls = self.camera.capture_metadata()
        auto_exposure_time = controls["ExposureTime"]
        auto_gain = controls["AnalogueGain"]
        auto_white_balance = controls.get("ColourGains", (1.0, 1.0))  # Default to (1.0, 1.0) if not available
        print(f"Auto Exposure Time: {auto_exposure_time}")
        print(f"Auto Gain: {auto_gain}")
        print(f"Auto White Balance Gains: {auto_white_balance}")

        # Lock the settings by switching to manual
        self.camera.set_controls({
            "ExposureTime": auto_exposure_time,  # Lock the current exposure time
            "AnalogueGain": auto_gain,  # Lock the current gain
            "AwbEnable": False,  # Disable Auto White Balance
            "ColourGains": auto_white_balance  # Lock the current white balance gains
        })

    def read_frame(self):
        image = self.camera.capture_array()
        image = cv2.flip(image, 0)
        return image

    def stop_camera(self):
        self.camera.stop()