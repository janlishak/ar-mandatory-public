#−−−−−−−−−−−−−− PI camera py thon example −−−−−−−−−−−−−−−−−−
# t h i s im p o r t s t h e camera
import cv2
import numpy as np
#from picamera import PiCamera

# i n i t i a l i z e
#camera = PiCamera()

def testCamera():
    print("Camera test")
    camera.start_preview()
    sleep(5)
    #we c a p t u r e t o openCV c om p a t i bl e forma t


    #you m igh t want t o i n c r e a s e r e s o l u t i o n
    camera.resolution = (320, 240)
    camera.framerate = 24
    sleep(2)
    image = np.empty((240,320,3) , dtype=np.uint8)
    camera.capture(image, 'bgr')
    cv2.imwrite('out.png', image)
    camera.stop_preview()
    print("saved_image_to_output.png")

def testCamera2():
    # i n i t i a l i z e
    camera = cv2.VideoCapture(0)
    if camera.isOpened():
        print("Camera Opened!")
    cv2.startWindowThread()
    print("This part worked")
    while True:
        # Capture a frame from the camera
        ret, frame = camera.read()
        if not ret:
            print("Not reading anything")
            break
        # Display the camera feed with detection results
        cv2.imwrite('./imgs/test.png', frame)
        cv2.waitKey(1)

    # Release the camera and close the OpenCV window
    camera.release()
    cv2.destroyAllWindows()

cv2.startWindowThread()
testCamera2()
cv2.destroyAllWindows()