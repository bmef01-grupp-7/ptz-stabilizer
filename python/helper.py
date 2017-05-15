import time
import os
import platform
from glob import glob
from serial import Serial, SerialException

"""
    the super fancy ascii art for the project
"""
ascii_art = "\n".join([
    "  ____ _____ _____  ____  _        _     _  _  _              ",
    " |  _ \_   _|__  / / ___|| |_ __ _| |__ (_)| |(_)_______ _ __ ",
    " | |_) || |   / /  \___ \| __/ _` | '_ \| || || |_  / _ \ '__|",
    " |  __/ | |  / /_   ___) | || (_| | |_) | || || |/ /  __/ |   ",
    " |_|    |_| /____| |____/ \__\__,_|_.__/|_||_||_/___\___|_|   ",
])

"""
    push and pop
    places x first in list l and deletes the last element,
    keeping the length of l
"""
def pp(x, l):
    l.insert(0, x)
    l.pop()

"""
    unit clamp
    returns the given value constrained to [-1, 1]
"""
def uclamp(x):
    return min(max(x, -1), 1)

"""
    average
    returns mean of list l
"""
def avg(l):
    return sum(l)/len(l)

"""
    no
    returns True if s contains an 'n'
"""
def no(s):
    return "n" in s.lower()

"""
    yes
    returns True if s does not contain an 'n'
"""
def yes(s):
    return not no(s)

"""
    in interval
    i:  [lower bound, upper bound]
    returns True if x is in interval i
"""
def in_interval(x, i):
    return i[0] <= x <= i[1]

"""
    round to int
    returns x rounded to nearest int
"""
def round_to_int(x):
    return int(round(x))

"""
    clear console
    clears the console, independent of os
"""
def clear_console():
    for _ in range(100): print("") # the stupid but fast way
    # os.system("cls" if os.name == "nt" else "clear")

"""
    serial ports
    returns all serial ports available
"""
def serial_ports():
    if platform.system() == "Windows":
        possible_ports = ["COM%s"%(i+1) for i in range(256)]
    elif platform.system() == "Linux":
        possible_ports = glob('/dev/ttyAC*')
    else:
        raise EnvironmentError("unsupported os")

    ports = []
    for port in possible_ports:
        try:
            ser = Serial(port)
            ser.close()
            ports.append(port)
        except(OSError, SerialException):
            pass
    return ports

"""
    now (time)
    returns the current time
"""
def now():
    if platform.system() == "Windows":
        return time.clock()
    elif platform.system() == "Linux":
        return time.time()
    else:
        raise EnvironmentError("unsupported os")

# below follows some special functions for printing diagnostic data

"""
    current, average, minimum
    returns [current, average, minimum] of a buffer list l
"""
def cur_avg_min(l):
    return [l[0], avg(l), min(l)]

"""
    nice format list of floats
    returns a nicely formatted string from a list of floats l
"""
def nice_format_list_of_float(l):
    return " ".join(["{0:6.1f}".format(x) for x in l])

# below follows two quick and dirty functions that I threw together
# to visualize data in 1d and 2d
# /erik

def visualize_1d(x, lim, size):
    size *= 2
    asize = 2*size + 1
    a = [" "]*asize
    f = lambda x: int(round(x/lim*size+size))
    g = lambda x: min(max(f(x), 0), asize-1)
    a[g(x)] = '|'
    return "   [" + "".join(a) + "]"

def visualize_2d(x, y, lim, size):
    msize = 2*size + 1
    m = [[" "]*msize for _ in range(msize)]
    f = lambda x: int(round(x/lim*size+size))
    g = lambda x: min(max(f(x), 0), msize-1)
    m[g(y)][g(x)] = '+'
    return "\n".join(["   "+"-"*(msize*2+1)]+["  | "+" ".join(r)+ " |" for r in m]+["   "+"-"*(msize*2+1)])
