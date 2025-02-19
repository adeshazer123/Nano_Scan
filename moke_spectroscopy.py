import matplotlib.pyplot as plt # type: ignore
import time
from pathlib import Path
from datetime import datetime
import pandas as pd # type: ignore
import logging

import numpy as np # type: ignore
from shrc203_VISADriver import (SHRC203VISADriver as SHRC203)

from keithley2100_VISADriver import Keithley2100VISADriver as KEITHLEY2100
from sr830_VISADriver import SR830VISADriver as SR830
from powermeter import CustomTLPM
from multizaber import ZaberMultiple
from ccsxxx import CCSXXX

path_root = Path(r"C:\Users\xxx\yyy\zzz")
path_root.mkdir(exist_ok=True)

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


com_zaber = "COM5"
index_zaber = 1

index_powermeter = 0

powermeter = CustomTLPM(index_powermeter)
powermeter.open_by_index(index_powermeter)

visa_ccs = 'USB0::0x1313::0x8087::M00934802::RAW'
ccs = CCSXXX(visa_ccs)
ccs.connect()

zaber = ZaberMultiple()
zaber.connect(com_zaber)

# Move to home of Axis 1, 2, and 3 (X, Y, Z, respectively)
shrc.home(1)
shrc.home(2)
shrc.home(3)
print("Waiting for 5 s")
time.sleep(5)


# Manual focus with Move relative
# shrc.move_relative(-1,3); keithley.read()

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

def read_power(wavelength=None):

    if wavelength is not None:
        powermeter.wavelength = wavelength
    return powermeter.get_power()

def wavelength2position(wavelength):
    position = -66.5 * wavelength + 63840
    return position*1e-3

def read_wavelength():
    ccs_wavelength = ccs.get_wavelength_data()
    ccs_intensity = ccs.get_scan_data()
    return ccs_wavelength[ccs_intensity.argmax()]

def set_wavelength(wavelength):
    position = wavelength2position(wavelength)
    zaber.move_abs(position, index_zaber)

def moke_spectrum(step = 5, myname="moke_spe", wait_time=1):
    """
    # wavelength from 695-970 nm
    step = 5 # nm
    """

    x,y,z = get_position_xyz()
    w = np.array([])
    p = np.array([])
    v = np.array([])
    r1 = np.array([])
    theta1 = np.array([])
    r2 = np.array([])
    theta2 = np.array([])
    moke = np.array([])

    # auto_focus(x,y,z)

    plt.ion()

    zaber.move_abs(0, 1)
    wavelength_current = read_wavelength()
    # for w_i in w_list:
    while wavelength_current > 700:
        zaber_increment = 13.3/(970-690)*step

        zaber.move_relative(zaber_increment, index_zaber)
        time.sleep(wait_time)
        wavelength_current = read_wavelength()
        power = read_power(wavelength_current)

        voltage = np.abs(keithely.read())
        v = np.append(v, voltage)
        w = np.append(w, wavelength_current)

        r1_value, theta1_value, r2_value, theta2_value = read_moke(wait_time)  # Measure MOKE in the lock-in amplifier

        r1 = np.append(r1, r1_value)
        theta1 = np.append(theta1, theta1_value)
        r2 = np.append(r2, r2_value)
        theta2 = np.append(theta2, theta2_value)
        moke = np.append(moke, r2_value/voltage/power)  # TODO correct this equiation

        p = np.append(p, power)

        res = {"wavelength (nm)": wavelength_current, "ref power (W)": power, "v (V)": voltage, "moke": moke,}
        print(res)

        plt.clf()

        plt.subplot(121)
        plt.plot(w, v/p, "o")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Reflection (a.u.)")
        plt.title('Reflection')

        plt.subplot(122)
        plt.plot(w, moke, "oC1")  # TODO replace with theta_k
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Kerr rotation (a.u.)")
        plt.title('Kerr rotation')

        plt.pause(0.05)

    plt.savefig(generate_filename(path_root,f"{myname}", "png"))

    dict = {"x (um)": x, "y (um)": y, "z (um)": z, "wavelength (nm)": w, "ref power (W)": p, "v (V)": v, "reflection (a.u,)":v/p, "r1 (V)": r1,
     "theta1 (deg)": theta1, "r2 (V)": r2, "theta2 (deg)": theta2, "r2/v/p": moke}
    df = pd.DataFrame(dict) # TODO add theta_k
    df.to_csv(generate_filename(path_root,f"{myname}", "csv"))
