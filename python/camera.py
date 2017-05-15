import requests

class Camera:
    """
        sets the default ip address and resets the camera
    """
    def __init__(self, ip):
        self.s = requests.Session()
        self.addr = "http://root:pass@" + ip + "/axis-cgi/com/"

    """
        moves the camera to pan, tilt in t seconds
        returns true if successful
    """
    def move(self, pan, tilt, t):
        r = self.s.get(self.addr + "ptz.cgi?query=position")
        d = dict([s.split("=") for s in r.content.strip().splitlines()[0:2]])
        cpan = float(d["pan"])
        ctilt = float(d["tilt"])

        vpan = (pan - cpan)/t
        vtilt = (tilt - ctilt)/t

        self.s.get(self.addr + 'ptz.cgi?continuouspantiltmove=%s,%s'%(vpan, vtilt))

    """
        stops the camera
    """
    def stop(self):
        self.get(self.addr + "ptz.cgi?continuouspantiltmove=0,0")
