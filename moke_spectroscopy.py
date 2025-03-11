import matplotlib.pyplot as plt
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging
import numpy as np
from shrc203_VISADriver import SHRC203VISADriver as SHRC203
from keithley2100_VISADriver import Keithley2100VISADriver as KEITHLEY2100
from sr830_VISADriver import SR830VISADriver as SR830
from powermeter import CustomTLPM
from multizaber import ZaberMultiple
from ccsxxx import CCSXXX

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MokeSpectro:
    def __init__(self, path_root, com_shrc, com_keithley, com_sr830, com_zaber, index_zaber, index_powermeter, visa_ccs):
        self.path_root = Path(path_root)
        self.path_root.mkdir(exist_ok=True)

        self.shrc = SHRC203(com_shrc)
        self.shrc.open_connection()

        self.keithley = KEITHLEY2100(com_keithley)
        self.keithley.init_hardware()

        self.sr830 = SR830(com_sr830)
        self.zaber = ZaberMultiple()
        self.zaber.connect(com_zaber)
        self.index_zaber = index_zaber

        self.powermeter = CustomTLPM(index_powermeter)
        self.powermeter.open_by_index(index_powermeter)

        self.ccs = CCSXXX(visa_ccs)
        self.ccs.connect()

        self.shrc.home(1)
        self.shrc.home(2)
        self.shrc.home(3)
        logger.info("Waiting for 5 seconds")
        time.sleep(5)

        self.shrc.move(8.282 * 1e3, 3)

    def read_moke(self, wait_time):
        self.sr830.set_harmonics(1)
        self.sr830.read_x_theta()
        time.sleep(wait_time)
        x1, theta1 = self.sr830.read_x_theta()

        self.sr830.set_harmonics(2)
        self.sr830.read_x_theta()
        time.sleep(wait_time)
        x2, theta2 = self.sr830.read_x_theta()
        return x1, theta1, x2, theta2

    def scan1d(self, x_start, x_stop, x_step, axis=1, myname="scan1d", wait_time=0.2):
        axis_name = ["x", "y", "z"]
        x_scan = np.arange(x_start, x_stop, x_step)

        x = np.array([])
        v = np.array([])

        self.shrc.move(x_scan[0], axis)
        time.sleep(5)

        plt.ion()

        for i in range(len(x_scan)):
            self.shrc.move(x_scan[i], axis)
            time.sleep(wait_time)
            x = np.append(x, x_scan[i])

            voltage = np.abs(self.keithley.read())
            v = np.append(v, voltage)

            plt.clf()
            plt.plot(x, v, "o")
            plt.pause(0.05)

        df = pd.DataFrame({f"{axis_name[axis-1]} (um)": x, "v (V)": v})
        df.to_csv(self.generate_filename(myname, "csv"))
        plt.savefig(self.generate_filename(myname, "png"))
        return x, v

    def auto_focus(self, x, y, z):
        logger.info(f"Moving to ({x},{y})")
        self.shrc.move(x, 1)
        time.sleep(2)
        self.shrc.move(y, 2)
        time.sleep(2)
        z_array, v_array = self.scan1d(z-20, z+20, 0.5, axis=3, myname="scan1d_focus", wait_time=0.2)
        z_max = z_array[np.argmax(v_array)]

        logger.info(f"Moving to z={z_max}")
        self.shrc.move(z_max, 3)
        time.sleep(1)

    def generate_filename(self, myname, extension="csv"):
        now = datetime.now()
        prefix = now.strftime("%Y%m%d_%H%M%S")
        filename = Path.joinpath(self.path_root, f"{prefix}_{myname}.{extension}")
        return filename

    def get_position_xyz(self):
        x = self.shrc.get_position(1)
        y = self.shrc.get_position(2)
        z = self.shrc.get_position(3)
        return x, y, z

    def read_power(self, wavelength=None):
        if wavelength is not None:
            self.powermeter.wavelength = wavelength
        return self.powermeter.get_power()

    def wavelength2position(self, wavelength):
        position = -66.5 * wavelength + 63840
        return position * 1e-3

    def read_wavelength(self):
        ccs_wavelength = self.ccs.get_wavelength_data()
        ccs_intensity = self.ccs.get_scan_data()
        return ccs_wavelength[ccs_intensity.argmax()]

    def set_wavelength(self, wavelength):
        position = self.wavelength2position(wavelength)
        self.zaber.move_abs(position, self.index_zaber)

    def moke_spectrum(self, step=5, myname="moke_spe", wait_time=1):
        x, y, z = self.get_position_xyz()
        w = np.array([])
        p = np.array([])
        v = np.array([])
        x1 = np.array([])
        theta1 = np.array([])
        x2 = np.array([])
        theta2 = np.array([])
        moke = np.array([])

        plt.ion()

        self.zaber.move_abs(0, 1)
        wavelength_current = self.read_wavelength()

        while wavelength_current > 700:
            zaber_increment = 13.3 / (970 - 690) * step
            self.zaber.move_relative(zaber_increment, self.index_zaber)
            time.sleep(wait_time)
            wavelength_current = self.read_wavelength()
            logger.info(f"Current wavelength: {wavelength_current}")
            power = self.read_power(wavelength_current)

            voltage = np.abs(self.keithley.read())
            v = np.append(v, voltage) # -> tab2
            w = np.append(w, wavelength_current)

            x1_value, theta1_value, x2_value, theta2_value = self.read_moke(wait_time)
            x1 = np.append(x1, x1_value)
            theta1 = np.append(theta1, theta1_value)
            x2 = np.append(x2, x2_value)
            theta2 = np.append(theta2, theta2_value)
            moke = np.append(moke, x2_value / voltage / power) # -> tab3
            # similarly moke1 = ... x1_value / voltage / power # -> tab4

            p = np.append(p, power)

            res = {"wavelength (nm)": wavelength_current, "ref power (W)": power, "v (V)": voltage, "moke": moke}
            logger.info(res)

            # tab1 -> mapping

            plt.clf()
            plt.subplot(131) # tab2
            plt.plot(w, v / p, "o")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Reflection (a.u.)")
            plt.title('Reflection')

            plt.subplot(132) # tab3
            plt.plot(w, moke, "oC1") 
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Kerr rotation (a.u.)")
            plt.title('Kerr rotation')

            plt.subplot(133) # tab4
            # plt.plot(...)


            plt.pause(0.05)

        plt.savefig(self.generate_filename(myname, "png"))

        data = {
            "x (um)": x, "y (um)": y, "z (um)": z, "wavelength (nm)": w, "ref power (W)": p, "v (V)": v,
            "reflection (a.u,)": v / p, "x1 (V)": x1, "theta1 (deg)": theta1, "x2 (V)": x2, "theta2 (deg)": theta2,
            "x2/v/p": moke
        }
        df = pd.DataFrame(data)
        df.to_csv(self.generate_filename(myname, "csv"))

if __name__ == "__main__":
    path_root = Path(r"C:\Users\DK-microscope\Measurement Data\Daichi\test")
    com_shrc = "ASRL3::INSTR"
    com_keithley = "USB0::0x05E6::0x2100::1149087::INSTR"
    com_sr830 = "GPIB0::1::INSTR"
    com_zaber = "COM5"
    index_zaber = 1
    index_powermeter = 0
    visa_ccs = 'USB0::0x1313::0x8087::M00934802::RAW'

    moke_spectro = MokeSpectro(path_root, com_shrc, com_keithley, com_sr830, com_zaber, index_zaber, index_powermeter, visa_ccs)
    moke_spectro.moke_spectrum()