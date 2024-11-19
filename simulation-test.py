from simulation import Simulation
from image_processor import ImageProcessor

if __name__ == "__main__":
    simulation = Simulation()
    image_processor = ImageProcessor()
    image_processor.set_frame_provider(simulation.capture_frame_to_numpy)
    image_processor.set_trackbar_values([29, 78, 139, 255, 110, 255, 5, 30])

    def update():
        simulation.update()
        image_processor.update()

    simulation.app.run()