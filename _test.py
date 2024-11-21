

class test:

    def __init__(self, sensors=[0,0]):
        self.ground_sensors = sensors

    def detect_surface(self):
        ## First, check where you are standing
        if (self.ground_sensors[0] > 900) & (self.ground_sensors[1] > 900): # Safe zone
            return "safe-zone"
        elif (self.ground_sensors[0] > 900): # Safe zone to the left
            return "safe-zone-left"
        elif (self.ground_sensors[1] > 900):
            return "safe-zone-right"
        elif (self.ground_sensors[0] < 400) & (self.ground_sensors[1] < 400): # Black tape
            return "black-tape"
        elif (self.ground_sensors[0] < 400):
            return "black-tape-left"
        elif (self.ground_sensors[1] < 400):
            return "black-tape-right"
        else:
            return "open-ground"
        


t = test([50,50])

print(t.detect_surface())