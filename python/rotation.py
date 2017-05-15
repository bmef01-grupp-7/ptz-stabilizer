from math import sin, cos, pi, atan, acos, degrees, atan2, radians
import numpy as np

class Rotator:
    def __init__(self, pan, tilt):
        pan, tilt = map(radians, [pan, tilt])
        self.target_pan = pan
        self.target_pt = np.array([
            sin(tilt)*cos(pan),
            sin(tilt)*sin(pan),
            cos(tilt)
        ])

    """
        rotates xyz coordinates [x, y, z] to pan and tilt
        returns [pan, tilt] in degrees
    """
    def rotate(self, xyz):
        ## construct rotational matrix, rotates in order x, y, z

        # initalizes 3x3 matrix with all elem = 0.0
        rot_mat = np.full((3, 3), 0.0)

        # we want to reverse angles to compensate movement
        xyz = [-x for x in xyz]

        # precompute sin and cos for all components
        s = [np.sin(x) for x in xyz]
        c = [np.cos(x) for x in xyz]

        rot_mat[0, 0] =  c[2]*c[1]
        rot_mat[0, 1] = -s[2]*c[1]
        rot_mat[0, 2] =  s[1]

        rot_mat[1, 0] =  s[1]*c[2]*s[0]+s[2]*c[0]
        rot_mat[1, 1] =  -s[2]*s[1]*s[0]+c[2]*c[0]
        rot_mat[1, 2] = -c[1]*s[0]

        rot_mat[2, 0] = -c[2]*s[2]*c[0]+s[2]*s[0]
        rot_mat[2, 1] =  s[2]*s[1]*c[0]+c[2]*s[0]
        rot_mat[2, 2] =  c[1]*c[0]

        # rot_max*target_pt applies the rotation to the original vector
        pt = np.dot(self.target_pt, rot_mat)

        # correct angles
        if pt[0] == 0:
            if pt[1] < 0:
                pan = -90
            if pt[1] > 0:
                pan = 90
            else:
                pan  = self.target_pan
        elif pt[0] <  0:
            pan = pi - atan2(pt[1],pt[0])
        else:
            pan = atan2(pt[1], pt[0])

        tilt = acos(pt[2]) # tilt = arccos(z/[r = 1])
        if tilt > pi/2:
            tilt  = pi - tilt

        return map(degrees, [pan, tilt])
