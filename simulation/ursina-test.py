import time

from ursina import *
import numpy as np
from OpenGL.GL import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE
import cv2
import random
import threading

max_x = 5
max_z = 20
random_x = random.uniform(-max_x, max_x)
random_z = random.uniform(10, max_z)
random_y = 0

app = Ursina(borderless=False, size=(220,160))

ground = Entity(model='plane', scale=(50, 1, 50), position=(0, 0, 0), texture=load_texture('ground.png'))
tennis_ball = Entity(model='sphere', color=color.green, scale=1, position=(random_x, random_y + 0.5, random_z))
robot = Entity(model='cube', color=color.red, scale=(1, 1, 1), position=(0, 0.5, 0))

camera_angle = 12
camera.position = Vec3(0,1,0)
camera.parent = robot
camera.mode = 'perspective'
camera.fov = 62
# camera.position = Vec3(0,70,0); camera_angle = 90

sky = Sky()
light_angle = 45
light_front = DirectionalLight(rotation=(90 - light_angle, 0, 0))
light_front = DirectionalLight(rotation=(90 - light_angle, 90, 0))
light_front = DirectionalLight(rotation=(90 - light_angle, 180, 0))
light_front = DirectionalLight(rotation=(90 - light_angle, 270, 0))
light_front = DirectionalLight(rotation=(-90, 0, 0)) # bottom


def capture_frame_to_numpy():
    width, height = map(int, window.size)
    glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, numpy_frame)
    # Reshape to (height, width, 3) for RGB format and flip vertically
    numpy_frame_rgb = np.frombuffer(numpy_frame, dtype=np.uint8).reshape(int(height), int(width), 3)
    numpy_frame_rgb = np.flipud(numpy_frame_rgb)  # Flip vertically as OpenGL reads bottom to top
    # Convert from BGR to RGB (OpenGL outputs BGR, OpenCV expects RGB)
    numpy_frame_rgb = np.flip(numpy_frame_rgb, axis=-1)
    return numpy_frame_rgb


# Create a NumPy buffer to hold the frame data
width, height = map(int, window.size)
numpy_frame = np.zeros((width * height * 3), dtype=np.uint8)


# Simple movement for the cube
def update():
    # global camera_angle
    #
    # if held_keys['up arrow']:
    #     robot.position += robot.forward * 0.1
    # if held_keys['down arrow']:
    #     robot.position -= robot.forward * 0.1
    #
    # if held_keys['left arrow']:
    #     robot.rotation_y -= 1
    # if held_keys['right arrow']:
    #     robot.rotation_y += 1
    #
    # if held_keys['w']:
    #     camera_angle -= 1
    # if held_keys['s']:
    #     camera_angle += 1

    camera.rotation = Vec3(camera_angle, camera.rotation_y, camera.rotation_z)

    # frame_array = capture_frame_to_numpy()
    # cv2.imshow("Frame", frame_array)
    # cv2.waitKey(1)  # Display frame briefly in a non-blocking way


if __name__ == '__main__':
    # app.run()
    thread = threading.Thread(target=app.run)
    thread.daemon = True  # Ensure it exits when the main program exits
    thread.start()
    #
    # time.sleep(10)
    #
    # cv2.destroyAllWindows()  # Close OpenCV window when the app stops

