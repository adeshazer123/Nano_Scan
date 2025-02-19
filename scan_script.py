import time
from datetime import datetime
from pathlib import Path
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from shrc203_VISADriver import (SHRC203VISADriver as SHRC203)
import logging
import matplotlib.pyplot as plt  # type: ignore
from keithley2100_VISADriver import Keithley2100VISADriver as KEITHLEY2100
from sr830_VISADriver import SR830VISADriver as SR830

logname = 'scan_logger.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger('scanTest')

# parameters
path_root = Path(r"C:\Users\DK-microscope\Measurement Data\Astha\keithley")
path_root_lockin = Path(r"C:\Users\DK-microscope\Measurement Data\Astha\lock-in-amplifier")

# initialize SHRC
com = "ASRL3::INSTR"
shrc = SHRC203(com)
shrc.open_connection()

# * initialize Keithely
# ( 1) USB0::0x05E6::0x2100::1149087::INSTR -> KEITHLEY INSTRUMENTS INC.,MODEL 2100,1,01.08-01-01
com = "USB0::0x05E6::0x2100::1149087::INSTR"
keithely = KEITHLEY2100(com)
keithely.init_hardware()

com = "GPIB0::1::INSTR"
sr830 = SR830(com)

# Move to home of Axis 1, 2, and 3 (X, Y, Z, respectively)
shrc.home(1)
shrc.home(2)
shrc.home(3)
print("Waiting for 5 s")
time.sleep(5)


# Move relative
# shrc.move_relative(10,1)

# Focus (move absolute)
shrc.move(8.282*1e3,3) # position (um), axis

def read_moke(wait_time):
    sr830.set_harmonics(1)
    sr830.read_r_theta()

    time.sleep(wait_time)
    r1, theta1 = sr830.read_r_theta()

    sr830.set_harmonics(2)
    sr830.read_r_theta()
    time.sleep(wait_time)
    r2, theta2 = sr830.read_r_theta()
    return r1, theta1, r2, theta2

def auto_focus(x,y,z):

    print(f"Moving to ({x},{y})")
    shrc.move(x, 1)
    time.sleep(2)
    shrc.move(y, 2)
    time.sleep(2)
    z_array, v_array = scan1d(z-20, z+20, 0.5, axis=3, myname="scan1d_focus", wait_time=0.2)
    z_max = z_array[np.argmax(v_array)]

    print(f"moving to z={z_max}")
    shrc.move(z_max, 3)
    time.sleep(1)
#
def generate_filename(path_root, myname, extension="csv"):
    now = datetime.now()
    prefix = now.strftime("%Y%m%d_%H%M%S")

    filename = Path.joinpath(path_root,f"{prefix}_{myname}.{extension}")
    return filename

def get_position_xyz():
    x = shrc.get_position(1)
    y = shrc.get_position(2)
    z = shrc.get_position(3)
    return x, y, z

def scan1d(x_start, x_stop, x_step, axis=1, myname="scan1d", wait_time=0.2):
    axis_name = ["x", "y", "z"]
    x_scan = np.arange(x_start, x_stop, x_step)

    x = np.array([])
    v = np.array([])
    # * voltage, too

    shrc.move(x_scan[0], axis)
    time.sleep(5)

    plt.ion()


    for i in range(len(x_scan)):
        # print(f"shrc.move(x_scan[i], axis): {x_scan[i], axis}")
        shrc.move(x_scan[i], axis)
        time.sleep(wait_time)
        x = np.append(x, x_scan[i])

        voltage = np.abs(keithely.read())

        v = np.append(v, voltage)

        plt.clf()
        plt.plot(x, v, "o")
        plt.pause(0.05)

    df = pd.DataFrame({f"{axis_name[axis-1]} (um)":x, "v (V)":v})
    df.to_csv(generate_filename(path_root,f"{myname}", "csv"))
    plt.savefig(generate_filename(path_root,f"{myname}", "png"))
    return x, v

def scan2d(x_start, x_stop, x_step, y_start, y_stop, y_step, myname="scan2d", wait_time=0.2):
    x_scan = np.arange(x_start, x_stop, x_step)
    y_scan = np.arange(y_start, y_stop, y_step)

    x = np.array([])
    y = np.array([])
    v = np.array([])
    # * voltage, too

    shrc.move(x_scan[0], 1)
    time.sleep(5)
    shrc.move(y_scan[0], 2)
    time.sleep(5)

    x_current, y_current, z_current = get_position_xyz()
    auto_focus(x_current, y_current, z_current)

    plt.ion()

    for j in range(len(y_scan)):
        # print(f"Y: {y_scan[j]}")
        shrc.move(y_scan[j], 2)
        time.sleep(wait_time)

        for i in range(len(x_scan)):
            # print(f"X: {x_scan[i]}")
            shrc.move(x_scan[i], 1)
            time.sleep(wait_time)
            x = np.append(x, x_scan[i])
            y = np.append(y, y_scan[j])

            voltage = np.abs(keithely.read())

            v = np.append(v, voltage)

            plt.clf()
            plt.scatter(x, y, c=v)
            plt.pause(0.05)

    plt.pcolormesh(x_scan,y_scan,v.reshape(len(y_scan), len(x_scan)),shading="auto")
    plt.colorbar()
    plt.savefig(generate_filename(path_root,f"{myname}", "png"))

    df = pd.DataFrame({"x (um)":x, "y (um)":y, "v (V)":v})
    df.to_csv(generate_filename(path_root,f"{myname}", "csv"))

def scan2d_moke(x_start, x_stop, x_step, y_start, y_stop, y_step, myname="scan2d_moke", wait_time=0.2):
    x_scan = np.arange(x_start, x_stop, x_step)
    y_scan = np.arange(y_start, y_stop, y_step)

    x = np.array([])
    y = np.array([])
    v = np.array([])
    r1 = np.array([])
    theta1 = np.array([])
    r2 = np.array([])
    theta2 = np.array([])
    Rv = np.array([])
        # * voltage, too

    shrc.move(x_scan[0], 1)
    time.sleep(5)
    shrc.move(y_scan[0], 2)
    time.sleep(5)

    x_current, y_current, z_current = get_position_xyz()
    auto_focus(x_current, y_current, z_current)

    plt.ion()

    for j in range(len(y_scan)):
        # print(f"Y: {y_scan[j]}")
        shrc.move(y_scan[j], 2)
        time.sleep(wait_time)

        for i in range(len(x_scan)):
            # print(f"X: {x_scan[i]}")
            shrc.move(x_scan[i], 1)

            time.sleep(wait_time)
            x = np.append(x, x_scan[i])
            y = np.append(y, y_scan[j])

            voltage = np.abs(keithely.read()) # Measure voltage in Keithley
            v = np.append(v, voltage)

            r1_value, theta1_value, r2_value, theta2_value = read_moke() # Measure MOKE in the lock-in amplifier

            r1 = np.append(r1, r1_value)
            theta1 = np.append(theta1, theta1_value)
            r2 = np.append(r2, r2_value)
            theta2 = np.append(theta2, theta2_value)
            Rv= np.append(Rv, r2_value/voltage)
            theta_k = r1**2+r2**2+theta1+theta2 # TODO correct this equiation

            plt.clf()

            plt.subplot(121)
            plt.scatter(x, y, c=v)

            plt.title('Reflection')

            plt.subplot(122)
            plt.scatter(x, y, c=Rv) # TODO replace with theta_k
            plt.title('R/v')
            plt.pause(0.05)


    plt.subplot(121)
    plt.pcolormesh(x_scan,y_scan, v.reshape(len(y_scan), len(x_scan)),shading="auto")
    plt.colorbar()

    plt.subplot(122)
    plt.pcolormesh(x_scan,y_scan, Rv.reshape(len(y_scan), len(x_scan)), shading="auto") # TODO replace with theta_k
    plt.colorbar()

    plt.savefig(generate_filename(path_root_lockin,f"{myname}", "png"))

    df = pd.DataFrame({"x (um)":x, "y (um)":y, "v (V)":v, "r1 (V)":r1, "theta1 (deg)":theta1, "r2 (V)":r2, "theta2 (deg)":theta2}) # TODO add theta_k
    df.to_csv(generate_filename(path_root_lockin,f"{myname}", "csv"))

