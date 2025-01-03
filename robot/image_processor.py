import cv2
import numpy as np
import time
import threading


class ComputerCamera:
    def __init__(self) -> None:
        # Start capturing video
        self.cap = cv2.VideoCapture(1)
        if not self.cap.isOpened():
            print("Cannot open camera")
            exit()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # set camera size to 1/2
        cam_driver_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        cam_driver_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Current camera driver resolution: {cam_driver_width}x{cam_driver_height}")

        # Set the camera to automatic mode
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Enable automatic exposure
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)  # Enable automatic white balance

        # Allow some time for the camera to adjust settings
        time.sleep(2)  # Wait for 2 seconds for adjustments

        # Lock the settings by switching to manual
        # Get the current values for exposure and white balance
        exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        white_balance = self.cap.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U)

        # Set the camera to manual mode
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Switch to manual exposure mode
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)  # Set the current exposure value
        self.cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, white_balance)  # Set the current white balance
        print("Camera settings locked. Exposure:", exposure, "White Balance:", white_balance)

    def read_frame(self):
        # Capture frame-by-frame
        ret, frame = self.cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            exit()
        return frame


class ImageProcessor:
    def __init__(self) -> None:
        self.found = False
        self.height = None
        self.width = None
        self.cY = 0
        self.cX = 0
        self.image_read_function = None

        cv2.namedWindow('image')
        cv2.createTrackbar('HUE low', 'image', 19, 359, self.print_trackbar_values)
        cv2.createTrackbar('HUE high', 'image', 41, 359, self.print_trackbar_values)
        cv2.createTrackbar('SAT low', 'image', 145, 255, self.print_trackbar_values)
        cv2.createTrackbar('SAT high', 'image', 255, 255, self.print_trackbar_values)
        cv2.createTrackbar('VAL low', 'image', 154, 255, self.print_trackbar_values)
        cv2.createTrackbar('VAL high', 'image', 252, 255, self.print_trackbar_values)
        cv2.createTrackbar('BLR', 'image', 3, 255, self.print_trackbar_values)
        cv2.createTrackbar('AREA', 'image', 500, 1000, self.print_trackbar_values)

    def get_frame(self):
        if self.image_read_function is None:
            raise Exception("Set image read function!")
        return self.image_read_function()

    def set_frame_provider(self, image_read_function):
        self.image_read_function = image_read_function

    def update(self):
        # Get the trackbar positions for HSV bounds
        lower_hue = cv2.getTrackbarPos('HUE low', 'image')
        upper_hue = cv2.getTrackbarPos('HUE high', 'image')
        lower_saturation = cv2.getTrackbarPos('SAT low', 'image')
        upper_saturation = cv2.getTrackbarPos('SAT high', 'image')
        lower_value = cv2.getTrackbarPos('VAL low', 'image')
        upper_value = cv2.getTrackbarPos('VAL high', 'image')
        blr = cv2.getTrackbarPos('BLR', 'image')
        min_area = cv2.getTrackbarPos('AREA', 'image')
        if blr%2 == 0:
            blr+=1
            cv2.setTrackbarPos('BLR', 'image', blr)

        frame = self.get_frame()

        # # resize to half resolution
        # frame_height, frame_width = frame.shape[:2]
        # self.height = frame_height // 2
        # self.width = frame_width // 2

        # resize to fixed resolution
        self.height = 120
        self.width = 160

        # warning - mutation of frame
        frame = cv2.resize(frame, (self.width, self.height))

        # Apply Gaussian Blur and convert to HSV
        # Loop over different blur kernel sizes
        # for blr in range(1, 10, 2):  # Using odd kernel sizes from 1 to 19
        #     blurred_image = cv2.GaussianBlur(frame, (blr, blr), 0)
        blurred_image = cv2.GaussianBlur(frame, (blr, blr), 0)

        hsv = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2HSV)

        # Set lower and upper bounds for HSV
        lower_bound = np.array([lower_hue, lower_saturation, lower_value])
        upper_bound = np.array([upper_hue, upper_saturation, upper_value])

        # Create a mask
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        # Optionally find and draw contours on the original frame
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Initialize variables to find the largest contour
        largest_contour = None
        largest_area = 0

        # Iterate through contours to find the largest one
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:  # Only consider contours above a certain area threshold
                if area > largest_area:
                    largest_area = area
                    largest_contour = contour

        # Draw contours and find the midpoint
        if largest_contour is not None:
            self.found = True
            # Draw the largest contour in red
            cv2.drawContours(frame, [largest_contour], -1, (0, 0, 255), 3)  # Red

            # Calculate the centroid of the largest contour
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                # Calculate x, y coordinates of the centroid
                self.cX = int(M["m10"] / M["m00"])
                self.cY = int(M["m01"] / M["m00"])

                # Draw a circle at the centroid
                cv2.circle(frame, (self.cX, self.cY), 7, (255, 0, 0), -1)  # Blue circle

                # Put text on the image to display the centroid coordinates
                cv2.putText(frame, f'X: {self.cX}, Y: {self.cY}', (self.cX + 10, self.cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)  # White text

                resolution = 10
                mapped_x = int(self.cX * resolution / self.width)
                mapped_y = int(self.cY * resolution / self.height)
                cv2.putText(frame, f'X: {mapped_x}, Y: {mapped_y}', (self.cX + 10, self.cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)  # White text
        else:
            self.found = False

        # Draw other contours in green
        for contour in contours:
            if contour is not largest_contour and cv2.contourArea(contour) > min_area:
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 3)  # Green

        # Convert the mask to a 3-channel image for concatenation
        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Concatenate original frame and mask side by side
        combined = np.hstack((frame, mask_3channel))
        # combined = np.hstack((blurred_image, mask_3channel))

        # Display the combined image
        cv2.imshow('image', combined)

        # todo: I doesn't show the windows if waitkey is not called ??
        if cv2.waitKey(1) == ord('q'):
            self.quit()
            exit()

    def updateForSeconds(self, duration):
        start_time = time.time()
        while time.time() - start_time < duration:
            self.update()

    def quit(self):
        # Release the capture and close windows
        self.cap.release()
        cv2.destroyAllWindows()

    def print_trackbar_values(self, trackbar_values):
        # Retrieve all trackbar values and print them in a list format
        values = [
            cv2.getTrackbarPos('HUE low', 'image'),
            cv2.getTrackbarPos('HUE high', 'image'),
            cv2.getTrackbarPos('SAT low', 'image'),
            cv2.getTrackbarPos('SAT high', 'image'),
            cv2.getTrackbarPos('VAL low', 'image'),
            cv2.getTrackbarPos('VAL high', 'image'),
            cv2.getTrackbarPos('BLR', 'image'),
            cv2.getTrackbarPos('AREA', 'image')
        ]
        print("Trackbar Values:", values)

    def set_trackbar_values(self, values):
        # Set all trackbars from a list of values
        cv2.setTrackbarPos('HUE low', 'image', values[0])
        cv2.setTrackbarPos('HUE high', 'image', values[1])
        cv2.setTrackbarPos('SAT low', 'image', values[2])
        cv2.setTrackbarPos('SAT high', 'image', values[3])
        cv2.setTrackbarPos('VAL low', 'image', values[4])
        cv2.setTrackbarPos('VAL high', 'image', values[5])
        cv2.setTrackbarPos('BLR', 'image', values[6])
        cv2.setTrackbarPos('AREA', 'image', values[7])


if __name__ == '__main__':
    computer_camera = ComputerCamera()
    # thymio_camera = ThymioCamera()
    image_processor = ImageProcessor()
    image_processor.set_frame_provider(computer_camera.read_frame)

    while True:
        image_processor.update()

