
import math
import random
import numpy as np
from shapely.geometry import Point, LineString


environment_settings = {
    "black_tape": 70,
    "open_arena": 400,
    "safe_zone": 1200,
}


class HorizontalSensors:
    def __init__(self, num_beams, max_distance_cm):
        self.num_beams = num_beams
        self.max_distance_cm = max_distance_cm


    def generate_scans(self, robot_pose, robots):
        x = robot_pose.x
        y = robot_pose.y
        theta = robot_pose.theta
        
        # Calculate the starting angle based on the robot's heading
        starting_angle = theta

        # Initialize a list to store distances for each beam
        distances = []
        intersect_points = []

        for angle in np.linspace(-math.pi / 8, math.pi / 8, 5, endpoint=False): ## ADAPT TO ACTUAL ANGLE OF SENSORS
            # Correct angle considering the starting angle and Pygame coordinate system
            corrected_angle = starting_angle + angle
            x2, y2 = (x + self.max_distance_cm * math.cos(corrected_angle), y + self.max_distance_cm * math.sin(corrected_angle))
        
            # Calculate the end point of the beam
            end_point = Point(x2, y2)

            # Create a LineString representing the Lidar beam
            front_sensors = LineString([(x, y), end_point])
            print("Front sensors: ", front_sensors)
            
            # Check for intersections with obstacles
            intersection = self._check_intersections(front_sensors, robots)

            # Calculate distance based on intersection or max distance
            if intersection:
                distance = Point(x, y).distance(intersection)
                intersect_points.append(intersection)
            else:
                distance = self.max_distance_cm
                intersect_points.append(end_point)
            distances.append(distance)

        return distances, intersect_points


    def _calculate_end_point(self, robot_pose, angle):
        """
        Calculate the end point of the Lidar beam based on the robot's pose and angle.

        Parameters:
            - robot_pose (Point): The current pose (location) of the robot with x, y, and theta.
            - angle (float): The angle of the Lidar beam in degrees.

        Returns:
            - Point: The end point of the Lidar beam.
        """
        x = robot_pose.x
        y = robot_pose.y
        theta = robot_pose.theta + angle  # Add angle to initial theta

        # Ensure the angle is within the valid range (0 to 360 degrees)
        theta %= 360

        # Convert angle to radians
        angle_rad = math.radians(theta)

        # Calculate the end point coordinates
        x_end = x + self.max_distance_cm * math.cos(angle_rad)
        y_end = y + self.max_distance_cm * math.sin(angle_rad)

        return Point(x_end, y_end)
    

    def _check_intersections(self, lidar_beam, robots):
        """
        Check for intersections between the Lidar beam and obstacles.

        Parameters:
            - lidar_beam (LineString): LineString representing the Lidar beam.
            - obstacles (list of LineString): List of LineString objects representing obstacles.

        Returns:
            - Point or None: The closest intersection point if there is one, otherwise None.
        """
        intersection_points = [lidar_beam.intersection(Point(robot.x, robot.y)) for robot in robots]
        # Filter valid points and ensure they are of type Point
        valid_intersections = [point for point in intersection_points if not point.is_empty and isinstance(point, Point)]
        if valid_intersections:
            closest_intersection = min(valid_intersections, key=lambda point: lidar_beam.project(point))
            return closest_intersection
        else:
            return None


class AvoiderRobot:
    def __init__(self, x, y, theta, axl_dist=5, wheel_radius=2.2):
        self.x = x
        self.y = y
        self.theta = theta  # Orientation in radians
        self.axl_dist = axl_dist
        self.wheel_radius = wheel_radius
        self.currently_turning = 0
        self.angular_velocity = 0
        self.linear_velocity = 0
    
        self.landmarks = []
        self.left_motor_speed = 0
        self.right_motor_speed = 0
        self.compass = CompassSensor()
        self.odometry_weight = 0.0
        self.odometry_noise_level = 0.01


    def predict(self, delta_time):
        self.move(delta_time)
        # Update orientation (theta) using the robot's compass sensor
        #compass_heading = self.compass.read_compass_heading(self.theta,self.angular_velocity, delta_time)

        # Blend odometry and compass headings
        #blended_heading = (self.odometry_weight * self.theta) + ((1-self.odometry_weight) * compass_heading)

        # Update the robot's orientation
        #self.theta = blended_heading
        
        return RobotPose(self.x, self.y, self.theta)
    

    def move(self, delta_time):
        
        # Assume maximum linear velocity at motor speed 500
        v_max = 10  # pixels/second
        
        # Calculate the linear velocity of each wheel
        left_wheel_velocity = (self.left_motor_speed / 500) * v_max
        right_wheel_velocity = (self.right_motor_speed / 500) * v_max
        
        v_x = math.cos(self.theta) * (self.wheel_radius * (left_wheel_velocity + right_wheel_velocity) / 2)
        v_y = math.sin(self.theta) * (self.wheel_radius * (left_wheel_velocity + right_wheel_velocity) / 2)
        omega = (self.wheel_radius * (left_wheel_velocity - right_wheel_velocity)) / (2 * self.axl_dist)
        
        self.x += (v_x * delta_time)
        self.y += (v_y * delta_time)
        self.theta += (omega * delta_time)

        # Ensure the orientation is within the range [0, 2*pi)
        self.theta = self.theta % (2 * math.pi)

        # Add a small amount of noise to the orientation
        noise = random.gauss(0, self.odometry_noise_level)
        self.theta += noise


    def set_motor_speeds(self, left_motor_speed, right_motor_speed):
        self.left_motor_speed = left_motor_speed
        self.right_motor_speed = right_motor_speed
        

    def get_robot_position(self):
        return RobotPose(self.x, self.y, self.theta)
    

    def update_estimated_position(self, estimated_pose):
        self.x = estimated_pose.x
        self.y= estimated_pose.y
        self.theta = estimated_pose.theta


    def getMotorspeeds(self):
        return (self.left_motor_speed, self.right_motor_speed)


    def explore_environment(self, sensors: np.array, camera: int):

        front_sensors = sensors[:5]
        back_sensors = sensors[5:7]
        ground_sensors = sensors[7:]

        base_speed = 500
        robot_threshold = 100 # See another robot
        turn_speed = 500
        
        ## CHECK FOR LINE ##
        # Line in front
        if (ground_sensors < 40).all():
            # 180 Turn
            self.set_motor_speeds(-base_speed, base_speed)
        # Black line to the left
        elif ground_sensors[0] < 40:
            # Turn slightly to the right
            self.set_motor_speeds(200, 0)
        elif ground_sensors[1] < 40:
            self.set_motor_speeds(0, 200)

        ## OTHER ROBOTS ##
        # If no robot in front
        elif (sensors > robot_threshold).any():
            # move forward
            self.set_motor_speeds(base_speed, base_speed)
        # Robot to the left
        elif np.argmin(front_sensors) == 0:
            # Move sharp right
            self.set_motor_speeds(0, -base_speed)
        # Robot to the right
        elif np.argmin(front_sensors) == 4:
            # Move sharp left
            self.set_motor_speeds(-base_speed, 0)
        # Robot in front!
        else:
            # 180 Turn
            self.set_motor_speeds(-base_speed, base_speed)


    def get_sensor_readings(self, environment):
        pass
        #for r in environment:
            #if r.x
    

class CompassSensor:

    drift_rate=0.0001
    USE_DRIFT=False

    def __init__(self, noise_stddev=0.0001) -> None:
        self.noise_level = noise_stddev

    def read_compass_heading(self, start_heading, angular_velocity, delta_time):
         # Update orientation (theta) based on angular velocity
        start_heading += angular_velocity * delta_time

        # Ensure the orientation is within the range [0, 2*pi)
        start_heading = start_heading % (2 * math.pi)

        # Add a small amount of noise to the orientation
        noise = random.gauss(0, self.noise_level)
        start_heading += noise

        # Introduce a small constant angular drift
        if self.USE_DRIFT:
            drift = self.drift_rate * delta_time
            start_heading += drift

        # Return the updated theta in radians
        return start_heading
    

class RobotPose:
    def __init__(self, x, y, theta):
        self.x = x
        self.y = y
        self.theta = theta
    #this is for pretty printing
    def __repr__(self) -> str:
        return f"x:{self.x},y:{self.y},theta:{self.theta}"



# Set up environment - The resolution of the world
width, height = 95, 225
#info = pygame.display.Info()
#width, height = info.current_w, info.current_h

env = np.ndarray((width, height))

# initialize lidar and robot
robot = AvoiderRobot(width / 2, height / 2, 2.6)
# Create a Lidar sensor with 60 beams and a max distance of 500 units
max_lidar_beam_distance = 500
# max_lidar_beam_distance = 200
sensors = HorizontalSensors(num_beams=5, max_distance_cm=max_lidar_beam_distance)



if __name__ == "__main__":
    # Game loop
    running = True
    pause = False
    steps = 0

    # Start 4 robots in corners
    robots = [AvoiderRobot(0,0,90), AvoiderRobot(width,0,90), AvoiderRobot(0,height,270), AvoiderRobot(width,height,270)]

    seeker = AvoiderRobot(50, 110, 90)

    sensor_readings, _intersect_points_estimated = sensors.generate_scans(seeker, robots)

    print(sensor_readings)

    import sys; sys.exit()

    while running:
        
        steps+=1

        

        """

        # this is the odometry where we use the wheel size and speed to calculate
        # where we approximately end up.
        robot_pose = robot.predict(time_step)

        # Generate Lidar scans - for these exercises, you wil be given these.
        lidar_scans, _intersect_points = lidar.generate_scans(robot_pose, env.get_environment())

        # This is what you will use in landmark detection
        landmark_sightings = landmark_handler.find_landmarks(_intersect_points, env.get_environment(), robot_pose)

        # print(f"Landmark sights: \n{landmark_sightings}")

        # this is where the particle filtering localisation happens
        particle_filter.update(time_step, landmark_sightings, robot.getMotorspeeds())

        # this is where we get the estimated position from the particles.
        particle_estimated_pose = particle_filter.get_estimate()

        lidar_scans_estimated, _intersect_points_estimated = lidar.generate_scans(particle_estimated_pose, env.get_environment())

        particle_filter.update_map(lidar_scans_estimated, max_lidar_beam_distance, _intersect_points_estimated, map_size=(800, 600), visualize=True, save=False)
        
        # mix the update, sense data into one position
        mixed_pose = RobotPose((0.1 * robot_pose.x + 0.9 * particle_estimated_pose.x),
                               (0.1 * robot_pose.y + 0.9 * particle_estimated_pose.y),
                               (robot_pose.theta))

        # EXERCISE 6.1: make the robot move and navigate the environment based on our current sensor information and our current map.
        robot.explore_environment_robot(lidar_scans)
        #robot.explore_environment_manual(lidar_scans)
        """
