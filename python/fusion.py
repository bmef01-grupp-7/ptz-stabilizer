from math import asin, degrees, pi, radians, sin, cos, sqrt
from helper import *

default_config = {
    "acc_cal": [4968.7, 4981.1], # zero-value for acc
    "acc_g": [1240.0, 1240.0], # 1g value for acc
    "acc_fc": 10.0, # lp cutoff frequency, Hz
    "gyro_cal": [-12.0, 15.0, 0.1], # zero-value for gyro
    "gyro_signs": [1.0, 1.0, -1.0],
    "gyro_to_dps_factor": 2000.0 / 2**15, # full range (dps) / full range (bits)
    "acc_fuse_f": 1.0 # Hz
}

class Fuser:
    def __init__(self, config=default_config, buffer_size=100):
        # save config
        self.config = config

        # data stored by process() for filtering purposes
        self.filt_acc = [0.0]*2

        # final rotation vector [x, y, z]
        self.angles = [0]*3

        # buffers for diagnostics, newest first
        self.acc_f_buf = [0.0]*buffer_size
        self.gyro_f_buf = [0.0]*buffer_size

    """
        processes a line s sent via serial from arduino

        for example,
        s =
            "atxy 10000 4000 6000" (acc)
            "gtxyz 10000 150 -200 50" (gyro)
            "w skipped gyro read" (warning)
    """
    def process(self, s):
        c = self.config # just shorter

        ss = s.split() # ex. ss = ["atxy", "10000", "5000", "5000"]

        if ss[0] == "atxy" and len(ss) == 4: # acc
            # get dt and convert from microseconds to seconds
            dt = float(ss[1])*1e-6

            # save f=dt^-1 to buffer
            pp(1/dt, self.acc_f_buf)

            # low pass filter smoothing factor
            sf_lp = lp_smoothing_factor(c["acc_fc"], dt)

            # read raw data
            acc_raw = [float(s) for s in ss[2:4]]

            # get data in g, ((raw data)-(zero value))/(1g value)
            # then clamp to max 1g
            acc = [uclamp((a-cal)/g) for a, cal, g \
                in zip(acc_raw, c["acc_cal"], c["acc_g"])]

            # low pass filter data
            self.filt_acc = [sf_lp*a + (1.0-sf_lp)*fa for fa, a in \
                zip(self.filt_acc, acc)]

            # take corresponding angle from data
            # assuming total acceleration is 1g, z = sqrt(1-(other axis)^2)
            filt_acc_angle = [
                asin(a/max(1.0, sqrt(1-oa**2))) for a, oa \
                in zip(self.filt_acc, self.filt_acc[::-1])]

            # angles to fuse into final angle data
            acc_fusion_angle = [
                filt_acc_angle[1],
                -filt_acc_angle[0],
                self.angles[2]
            ]

            # fusion factor
            sf_f = lp_smoothing_factor(c["acc_fuse_f"], dt) # typically very small

            # fuse into final angle data (angles)
            self.angles = [sf_f*afa + (1.0-sf_f)*ang for ang, afa \
                in zip(self.angles, acc_fusion_angle)]

        elif ss[0] == "gtxyz" and len(ss) == 5: # gyro
            # get dt and convert from microseconds to seconds
            dt = float(ss[1])*1e-6

            # save f=dt^-1 to buffer
            pp(1/dt, self.gyro_f_buf)

            # read raw data
            gyro_raw = [float(s) for s in ss[2:5]]

            # apply calibration
            gyro_raw = [x - cal for x, cal in \
                zip(gyro_raw, c["gyro_cal"])]

            # flip signs to correct raw data
            gyro_raw = [g*s for g, s in zip(gyro_raw, c["gyro_signs"])]

            # convert to degrees per second
            gyro_dps = [x*c["gyro_to_dps_factor"] for x in gyro_raw]

            # convert to radians per second
            gyro_rps = [radians(x) for x in gyro_dps]

            # get difference from last angle (da)
            gyro_da = [x*dt for x in gyro_rps]

            # rotate angles
            # https://en.wikipedia.org/wiki/Rotation_matrix
            old_angles = [x for x in self.angles] # copy
            self.angles[0] = +old_angles[0]*cos(gyro_da[2]) \
                                -old_angles[1]*sin(gyro_da[2])
            self.angles[1] = +old_angles[0]*sin(gyro_da[2]) \
                                +old_angles[1]*cos(gyro_da[2])

            # integrate
            self.angles = [ang + da for ang, da in zip(self.angles, gyro_da)]

        elif ss[0] == "w": # warning
            raise Exception(" ".join(ss[1:]))
        else:
            raise Exception("invalid data")

"""
    low pass filter smoothing factor
    returns the smoothing factor for a first order low pass filter given a
    cutoff frequency (fc) and delta time (dt)
    https://en.wikipedia.org/wiki/Low-pass_filter
"""
def lp_smoothing_factor(fc, dt):
    return 1.0/(1.0 + 1.0/(2.0*pi*fc*dt))

"""
    dummy main
    quick test without needing to run the main file
"""
def main():
    f = Fuser()
    f.process("atxy 10000 4000 6000")
    f.process("gtxyz 10000 150 -200 50")
    print(f.angles)

if __name__ == "__main__":
    main()
