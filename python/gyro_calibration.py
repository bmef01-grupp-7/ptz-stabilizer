from serial import Serial
from math import degrees, sin,radians
import sys

from helper import *

def main():
    ### setup
    clear_console()
    print(ascii_art)

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

    ser = Serial(port, 115200, timeout=0)

    acc_reads = []
    gyro_reads = []
    n = 100

    ser_buffer = ""

    print("\nReading...")

    while len(gyro_reads) < n or len(acc_reads) < n:
        if ser.in_waiting:
            ser_buffer += ser.read(size=24)
            if "\n" in ser_buffer:
                i = ser_buffer.index("\n")
                s = ser_buffer[:i-1]
                ser_buffer = ser_buffer[i+1:]
                try:
                    ss = s.split()
                    if ss[0] == "atxy" and len(ss) == 4:
                        acc_raw = [float(s) for s in ss[2:4]]
                        acc_reads.append(acc_raw)
                    elif ss[0] == "gtxyz" and len(ss) == 5:
                        gyro_raw = [float(s) for s in ss[2:5]]
                        gyro_reads.append(gyro_raw)
                except Exception as e:
                    pass
                continue

    acc = ["%.1f"%avg([read[i] for read in acc_reads]) for i in range(2)]
    print(acc)
    gyro = ["%.1f"%avg([read[i] for read in gyro_reads]) for i in range(3)]
    print(gyro)


if __name__ == "__main__":
    main()
