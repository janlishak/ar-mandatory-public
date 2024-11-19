from ursina import *
import numpy as np
from OpenGL.GL import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE
import cv2
import random
import math
import time as pytime


class Simulation:
    def __init__(self):
        # Ursina setup
        self.reset_threshold = 30
        self.current_action = "STOP"
        self.app = Ursina(borderless=False, size=(220, 160))

        # Create entities
        self.ground = Entity(model='plane', scale=(50, 1, 50), position=(0, 0, 0), texture=load_texture('ground.png'))
        self.tennis_ball = Entity(model='sphere', color=color.green, scale=1, position=(random.uniform(-5, 5), 0.5, random.uniform(10, 20)))
        self.robot = Entity(model='cube', color=color.red, scale=(1, 1, 1), position=(0, 0.5, 0))

        # Setup Camera
        self.camera_angle = 12
        camera.position = Vec3(0, 1, 0)
        camera.parent = self.robot
        camera.mode = 'perspective'
        camera.fov = 62

        # self.camera_angle = 90
        # camera.position = Vec3(0, 30, 0)

        # Setup skybox and lights
        light_angle = 45
        self.sky = Sky()
        self.light_front = DirectionalLight(rotation=(90 - light_angle, 0, 0))
        self.light_front = DirectionalLight(rotation=(90 - light_angle, 90, 0))
        self.light_front = DirectionalLight(rotation=(90 - light_angle, 180, 0))
        self.light_front = DirectionalLight(rotation=(90 - light_angle, 270, 0))
        self.light_front = DirectionalLight(rotation=(-90, 0, 0))  # bottom

        # Create NumPy buffer to hold frame data
        self.width, self.height = map(int, window.size)
        self.numpy_frame = np.zeros((self.width * self.height * 3), dtype=np.uint8)

        # Reset
        self.init()

    def init(self):
        self.tennis_ball.position=(random.uniform(-8, 8), 0.5, random.uniform(10, 20))
        self.x = 0.0  # Robot position (x)
        self.y = 0.0  # Robot position (y)
        self.q = math.pi/2  # Robot heading in radians
        self.left_wheel_velocity = 0
        self.right_wheel_velocity = 0
        self.start_time = pytime.time()

    def set_motors(self, values):
        self.left_wheel_velocity = values[0]
        self.right_wheel_velocity = values[1]

    def capture_frame_to_numpy(self):
        glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE, self.numpy_frame)
        # Reshape to (height, width, 3) for RGB format and flip vertically
        numpy_frame_rgb = np.frombuffer(self.numpy_frame, dtype=np.uint8).reshape(int(self.height), int(self.width), 3)
        numpy_frame_rgb = np.flipud(numpy_frame_rgb)  # Flip vertically as OpenGL reads bottom to top
        # Convert from BGR to RGB (OpenGL outputs BGR, OpenCV expects RGB)
        numpy_frame_rgb = np.flip(numpy_frame_rgb, axis=-1)
        return numpy_frame_rgb

    def updateRobot(self):
        R = 0.05  # radius of wheels in meters
        L = 2  # distance between wheels in meters

        v_x = cos(self.q) * (R * self.left_wheel_velocity / 2 + R * self.right_wheel_velocity / 2)
        v_y = sin(self.q) * (R * self.left_wheel_velocity / 2 + R * self.right_wheel_velocity / 2)
        omega = (R * self.right_wheel_velocity - R * self.left_wheel_velocity) / (2 * L)

        self.x += v_x * time.dt
        self.y += v_y * time.dt
        self.q = (self.q + omega * time.dt)%(2*math.pi)

        self.robot.position = (self.x, 0, self.y)
        self.robot.rotation = (0, math.degrees(-self.q) + 90, 0)

    def update(self):
        # Simple movement
        # if held_keys['up arrow']:
        #     self.robot.position += self.robot.forward * 0.1
        # if held_keys['down arrow']:
        #     self.robot.position -= self.robot.forward * 0.1
        if held_keys['left arrow']:
            self.perform_action("LEFT")
        if held_keys['right arrow']:
            self.perform_action("RIGHT")
        if held_keys['w']:
            self.camera_angle -= 1
        if held_keys['s']:
            self.camera_angle += 1

        dis = distance(self.robot, self.tennis_ball.position)
        if dis < 2:
            print("Reset - distance between entities:", dis)
            self.init()

        elapsed_time = pytime.time() - self.start_time
        if elapsed_time > self.reset_threshold:
            print(f"Game has been running for {elapsed_time:.2f} seconds. Resetting game...")
            self.init()

        # Update camera
        camera.rotation = Vec3(self.camera_angle, camera.rotation_y, camera.rotation_z)

        # Update frame
        # frame_array = self.capture_frame_to_numpy()
        # cv2.imshow("Frame", frame_array)
        # cv2.waitKey(1)  # Display frame briefly in a non-blocking way
        self.updateRobot()

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
    simulation = Simulation()  # Starts the simulation in a non-blocking way

    def update():
        simulation.update()

    simulation.app.run()
    cv2.destroyAllWindows()  # Close OpenCV window when the app stops