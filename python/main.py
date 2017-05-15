from serial import Serial
from math import degrees, sin,radians
import time
import sys

import fusion
import camera
import rotation
from helper import *

def main():
    ### setup
    clear_console()
    print(ascii_art)

    # arg --offline-test is used to skip camera and angle setup
    offline_test = len(sys.argv) > 1 and sys.argv[1] == "--offline-test"
    if offline_test:
        print("\nOffline test mode")

    ## prompts user for serial port
    ports = serial_ports()
    print("\nSerial setup:")
    if ports:
        if len(ports) > 1:
            print("  Available serial ports:")
            print("\n".join(["    %s: %s"%(i+1, v) for i, v in enumerate(ports)]))
            inp = raw_input("  Pick a serial port: [1 - %s] "%len(ports))
            try:
                index = int(inp) - 1
                if not in_interval(index, [0, len(ports-1)]):
                    raise Exception()
                port = ports[index]
            except Exception as e:
                exit("Invalid input, exiting...")
        else:
            port = ports[0]
    else:
        exit("  No serial port found, exiting...")
    print("  Serial port: %s"%port)

    ## prompts user for camera control
    print("\nCamera setup:")
    if offline_test:
        camera_control = False
        print("  Camera control disabled")
    else:
        inp = raw_input("  Enable camera control? [Y/n] ")
        camera_control = yes(inp)
    if camera_control:
        ips = [
            "169.254.20.202",
            "169.254.20.203"
        ]
        print("  IP:")
        print("    0: custom")
        print("\n".join(["    %s: %s"%(i+1, v) for i, v in enumerate(ips)]))
        inp = raw_input("  Pick an IP: [0 - %s] "%(len(ips)))
        try:
            inp = int(inp)
            if not in_interval(inp, [0, len(ips)]):
                raise Exception()
            if inp:
                ip = ips[inp-1]
            else:
                ip = raw_input("  Enter custom IP: ")
        except Exception as e:
            exit("  Invalid input, exiting...")
        print("  IP: %s"%ip)

    ## prompts user for default pan and tilt
    tgt_pan = 0
    tgt_tilt = 45
    print("\nAngle setup:")
    if offline_test:
        print("  Using (%d, %d) as target (pan, tilt)"%(tgt_pan, tgt_tilt))
    else:
        tgt_pan_range = [-90, 90]
        tgt_tilt_range = [0, 90]
        inp = raw_input("  Use (%d, %d) as target (pan, tilt)? [Y,n] "%(tgt_pan, tgt_tilt))
        if no(inp):
            try:
                tgt_pan = int(raw_input("  Enter target pan value: [%s - %s] "%tuple(tgt_pan_range)))
                if not in_interval(pan, tgt_pan_range):
                    raise Exception()
                tgt_tilt = int(raw_input("  Enter target tilt value: [%s - %s] "%tuple(tgt_tilt_range)))
                if not in_interval(tilt, tgt_tilt_range):
                    raise Exception()
            except:
                exit("  Invalid input, exiting...")
    print("\nSetup finished, starting stabilization...")

    ### initialize

    # hardcoded setting
    output_freq = 25.0

    # used for lookup
    output_dt = 1.0/output_freq

    # camera movement "gain"
    cam_dt = 2.0*output_dt

    # used for measuring output freq
    last_output_time = 0.0

    # buffer length is set such that the buffer is 1 second long
    buf_len = int(output_freq)

    # start serial
    ser = Serial(port, 115200, timeout=0)
    ser_buffer = "" # serial buffer for reading continuously

    # create and initalize a fuser
    f = fusion.Fuser(buffer_size=buf_len)

    # create and initalize a camera object
    if camera_control:
        c = camera.Camera(ip)

    # create and initalize a rotator
    rotator = rotation.Rotator(tgt_pan, tgt_tilt)

    # create empty buffers
    out_f_buf = [0.0]*buf_len
    fuse_t_buf = [0.0]*buf_len
    rot_t_buf = [0.0]*buf_len
    out_t_buf = [0.0]*buf_len
    exc_buf = [None]*buf_len

    ### run

    time.clock() # needs to be called once to initalize

    time.sleep(1)

    while True:
        # read from serial
        # if possible, process data
        if ser.in_waiting:
            ser_buffer += ser.read(size=24) # a line won't be longer than 24B
            if "\n" in ser_buffer: # if a complete line is in the buffer
                # extract the line
                i = ser_buffer.index("\n")
                s = ser_buffer[:i-1]
                ser_buffer = ser_buffer[i+1:]
                try: # and process it
                    t = now()
                    f.process(s)
                    pp(now() - t, fuse_t_buf)
                    pp(None, exc_buf)
                except Exception as e:
                    pp(e, exc_buf) # save the exception for diagnostic output
                continue

        # if long enough time passed, output data
        t = now()
        dt = t - last_output_time
        if dt >= output_dt:
            last_output_time = t
            freq = 1.0/dt
            pp(freq, out_f_buf)

            angles = f.angles
            rot_t = now()
            pan, tilt = rotator.rotate(angles)
            pp(now()-rot_t, rot_t_buf)

            if camera_control:
                c.move(pan, tilt, cam_dt)

            # calculate diagnostic data
            acc_f_data = \
                map(round_to_int, cur_avg_min(f.acc_f_buf))
            gyro_f_data = \
                map(round_to_int, cur_avg_min(f.gyro_f_buf))
            out_f_data = \
                map(round_to_int, [output_freq]+cur_avg_min(out_f_buf))
            fus_t_data = \
                [int(x*1.0e6) for x in [avg(fuse_t_buf), max(fuse_t_buf)]]
            rot_t_data = \
                [int(x*1.0e6) for x in [avg(rot_t_buf), max(rot_t_buf)]]
            out_t_data = \
                [int(x*1.0e6) for x in [avg(out_t_buf), max(out_t_buf)]]
            excs = \
                [str(x) for x in exc_buf if x]
            x, y, z = \
                map(degrees, angles)

            clear_console()
            print("\n".join([
                ascii_art+"\n",
                "serial: %s"%port,
                "camera: %s"%(ip if camera_control else "disabled"),
                "target:",
                "  pan:  %3d"%tgt_pan,
                "  tilt: %3d"%tgt_tilt,
                "freq [hz]:",
                "  acc       cur avg min:     {:3d} {:3d} {:3d}".format(*acc_f_data),
                "  gyro      cur avg min:     {:3d} {:3d} {:3d}".format(*gyro_f_data),
                "  out   tgt cur avg min: {:3d} {:3d} {:3d} {:3d}".format(*out_f_data),
                "time [us]:",
                "  fus  avg max: {:5d} {:5d}".format(*fus_t_data),
                "  rot  avg max: {:5d} {:5d}".format(*rot_t_data),
                "  out  avg max: {:5d} {:5d}".format(*out_t_data),
                "status:\n  " + (excs[0] if excs else "ok"),
                "",
                "pan tilt:",
                nice_format_list_of_float([pan, tilt]),
                "",
                "fusion data:",
                nice_format_list_of_float(map(degrees, angles)),
                visualize_2d(x, y, 90, 4),
                visualize_1d(z, 90, 4)
            ]))

            pp(now() - t, out_t_buf)

if __name__ == "__main__":
    main()
