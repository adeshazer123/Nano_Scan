import matplotlib.pyplot as plt
import time
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging
import argparse
import numpy as np
from powermeter import CustomTLPM
from ccsxxx import CCSXXX
from multizaber import ZaberMultiple
from shrc203_VISADriver import SHRC203VISADriver as SHRC203
from keithley2100_VISADriver import Keithley2100VISADriver as Keithley
from sr830_VISADriver import SR830VISADriver as SR830
# print(os.getcwd())
# # logger.debug('This message should go to the log file')
logname = 'scan_logger.log' 
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger('scanTest')

class NanoScanner: 
    def __init__(self, com_shrc, com_keithley, com_sr830, com_zaber, com_ccsx):
        self.path_root = Path(r"C:\Users\DK-microscope\Measurement Data\Astha\keithley") #?????? Fix this. Amelie does not understand why this is needed. We should not need to specify the path here.
        self.shrc = SHRC203(com_shrc)
        self.keithley = Keithley(com_keithley)
        self.sr830 = SR830(com_sr830)
        self.pwmeter = CustomTLPM()
        self.zaber = ZaberMultiple()
        self.wavelength = CCSXXX(com_ccsx)
        self.wavelength.connect()
        self.zaber.connect(com_zaber)
        self.shrc.open_connection()
        self.keithley.init_hardware()
        self.axis = 1
    
    def home(self): 
        for i in range(3): 
            self.shrc.home(self.axis)
            i+=1
            
    def focus(self, position): 
        self.shrc.move(position, self.axis)

    def move(self, position): 
        self.shrc.move(position, self.axis)
    
    def set_axis(self, axis): 
        self.axis = axis

    def query_position(self, axis):
        return self.shrc.query_position(axis)
    
    def get_position_xyz(self):
        x = self.shrc.get_position(1)
        y = self.shrc.get_position(2)
        z = self.shrc.get_position(3)
        return x, y, z
    def harmonics_one(self, wait_time): 
        self.sr830.set_harmonics(1)
        self.sr830.read_x_theta()
        time.sleep(wait_time)
        x1, theta1 = self.sr830.read_x_theta()
        return x1, theta1

    def harmonics_two(self, wait_time): 
        """Reads the r and theta values for the second harmonic
        Args: 
            wait_time (float): Time to wait between measurements
            Returns:
            x2 (float): r value for the second harmonic
            theta2 (float): theta value for the second harmonic
            """
        self.sr830.set_harmonics(2)
        self.sr830.read_x_theta()
        time.sleep(wait_time)
        x2, theta2 = self.sr830.read_x_theta()
        return x2, theta2
    def auto_focus(self, x, y, z):
        """Auto focus for the SHRC203 scanner 
        Args: 
            x (float): x position
            y (float): y position
            z (float): z position
            """
        self.shrc.move(x, 1)
        time.sleep(5)
        self.shrc.move(y, 2)
        time.sleep(5)
        z_array, v_array = self.scan1d(z-20, z+20, 0.5, axis = 3, myname = "auto_focus")
        z_max = z_array[np.argmax(v_array)]

        self.shrc.move(z_max, 3)


    def generate_filename(self ,path_root, myname, extension="csv"):
        now = datetime.now()
        prefix = now.strftime("%Y%m%d_%H%M%S")

        filename = Path.joinpath(path_root,f"{prefix}_{myname}.{extension}")
        return filename

    
    def get_wavelength(self): 
        wave = self.wavelength.get_wavelength_data()
        intensity = self.wavelength.get_scan_data()
        return wave[intensity.argmax()]

    def wavelength_to_position(self, wavelength): 
        position = -66.5 * wavelength + 63840
        return position * 1e-3
    
    def get_power(self): 
        return self.pwmeter.get_power()

    def scan2d_moke(self, x_start, x_stop, x_step, y_start, y_stop, y_step, myname="scan_moke", wait_time = 0.2):
        x_scan = np.arrange(x_start, x_stop, x_step)
        y_scan = np.arrange(y_start, y_stop, y_step)

        x = np.array([])
        y = np.array([])
        v = np.array([])
        x1 = np.array([])
        theta1 = np.array([]) 
        x2 = np.array([]) 
        theta2 = np.array([]) 
        Rv = np.array([])

        self.shrc.move(x_scan[0], 1)
        time.sleep(5)
        self.shrc.move(y_scan[0], 2)
        time.sleep(5)

        x_current, y_current, z_current = self.get_position_xyz()
        self.auto_focus(x_current, y_current, z_current)

        plt.ion()
        for j in range(len(y_scan)):
            self.shrc.move(y_scan[j], 2)
            time.sleep(wait_time)

            for i in range(len(x_scan)):
                self.shrc.move(x_scan[i], 1)

                time.sleep(wait_time)
                x = np.append(x, x_scan[i])
                y = np.append(y, y_scan[j])

                voltage = np.abs(self.keithely.read()) # Measure voltage in Keithley
                v = np.append(v, voltage)

                x1_value, theta1_value = self.harmonics_one(wait_time) # Measure first harmonic in the lock-in amplifier
                x2_value, theta2_value = self.harmonics_two(wait_time) # Measure second harmonic in the lock-in amplifier   

                # x1_value, theta1_value, x2_value, theta2_value = self.read_moke() # Measure MOKE in the lock-in amplifier

                x1 = np.append(x1, x1_value)
                theta1 = np.append(theta1, theta1_value)
                x2 = np.append(x2, x2_value)
                theta2 = np.append(theta2, theta2_value)
                plt.clf()

                plt.subplot(121)
                plt.scatter(x, y, c=v)
                plt.title('Reflection')

                plt.subplot(122)
                plt.scatter(x, y, c=x2/v) # TODO replace with theta_k
                plt.title('x2/v')
                plt.xlabel('Position (um)')
                plt.ylabel('x2/v')
                plt.pause(0.05)

                plt.subplot(111)
                plt.scatter(x, y, c=x1/v)
                plt.title('x1/v')
                plt.xlabel('Position (um)')
                plt.ylabel('x1/v')
                plt.pause(0.05)

                # also plot x,y,x2/v, x1/v
        df = pd.DataFrame({"x (um)":x, "y (um)":y, "v (V)":v})
        return df

    def moke_spectroscopy(self, step, index_zaber):
        step = 5
        x, y, z = self.get_position_xyz()
        voltage = np.array([])
        power = np.array([])
        moke = np.array([])
        wavelength = np.array([])
        r1 = np.array([])
        theta1 = np.array([])
        r2 = np.array([])
        theta2 = np.array([])
        position = np.array([])

        plt.ion() 

        self.zaber.home(1)
        wavelength = self.get_wavelength()

        while wavelength > 700:
            zaber_shift = 13.3 / (970 - 690) * step
            self.zaber.move_relative(zaber_shift, index_zaber)
            time.sleep(0.5)
            wavelength_read = self.get_wavelength()
            power = self.get_power()

            voltage = np.abs(self.keithley.read())
            v = np.append(voltage, v)
            wavelength = np.append(wavelength, wavelength_read)

            r1_value, theta1 = self.harmonics_one(0.5)
            r2_value, theta2 = self.harmonics_two(0.5)
            r1 = np.append(r1, r1_value)
            theta1 = np.append(theta1, theta1)
            r2 = np.append(r2, r2_value)
            theta2 = np.append(theta2, theta2)
            moke = np.append(moke, r2_value / voltage / power)
            power = np.append(power, power)

            #Plotting the wavelength vs MOKE values being read
            plt.clf()
            plt.subplot(121)
            plt.plot(wavelength, voltage / power, "-")
            plt.title("Reflection")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Reflection (a.u.)")

            plt.subplot(122)
            plt.plot(wavelength, moke, "o")
            plt.title("Wavelength vs MOKE")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("MOKE (a.u.)")
            plt.pause(0.05)

        df = pd.DataFrame({"wavelength (nm)":wavelength, "v (V)":v, "r1":r1, "theta1":theta1, "r2":r2, "theta2":theta2, "moke":moke})
        return df

    def scan1d(self, x_start, x_stop, x_step, axis =1, myname = "scan1d", wait_time = 0.2):
        """ Scan 1D area with SHRC203 and Keithley 2100
        Args:
            x_start (float): Start position
            x_stop (float): Stop position
            x_step (float): Step size
            axis (int): Axis to scan
            myname (str): Name of the scan
            wait_time (float): Wait time between measurements
            """
        x_scan = np.arange(x_start, x_stop, x_step)
        x = np.array([])
        v = np.array([])
        
        self.shrc.move(x_scan[0], axis)
        time.sleep(5)

        plt.ion()


        for i in range(len(x_scan)):
            x = np.append(x, x_scan[i])

            # voltage = np.random.rand() # * Replace with Keithley 
            voltage = self.keithley.read()

            v = np.append(v, voltage)

            plt.clf()
            plt.plot(x, v)
            plt.xlabel("Position (um)")
            plt.ylabel("Voltage (V)")

            plt.pause(0.05)

            time.sleep(0.5)

        plt.plot(x, v)
        plt.savefig(self.generate_filename(self.path_root,"scan", "png"))

        df = pd.DataFrame({"x (um)":x, "v (V)":v})
        return df
    
    def scan2d(self, x_start, x_stop, x_step, y_start, y_stop, y_step, myname="scan"):
        x_scan = np.arange(x_start, x_stop, x_step)
        y_scan = np.arange(y_start, y_stop, y_step)

        x = np.array([])
        y = np.array([])
        v = np.array([])
        # * voltage, too

        plt.ion()

        for j in range(len(y_scan)):
            # print(f"Y: {y_scan[j]}")
            # self.shrc.move(y_scan[j], 2)

            for i in range(len(x_scan)):
                # print(f"X: {x_scan[i]}")
                # self.shrc.move(x_scan[i], 1)
                x = np.append(x, x_scan[i])
                y = np.append(y, y_scan[j])

                # voltage = np.random.rand() # * Replace with Keithley 
                voltage = self.keithley.read()

                v = np.append(v, voltage)

                plt.clf()
                plt.scatter(x, y, c=v)
                plt.xlabel("Position (um)")
                plt.ylabel("Voltage (V)")

                plt.pause(0.05)

                time.sleep(0.5)

        plt.pcolormesh(x_scan,y_scan,v.reshape(len(x_scan), len(y_scan)), shading="auto")
        plt.colorbar()
        plt.savefig(self.generate_filename(self.path_root,"scan", "png"))

        df = pd.DataFrame({"x (um)":x, "y (um)":y, "v (V)":v})
        return df

    def close_connection(self): 
        self.shrc.close()
        self.keithley.close()

if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Scan a 2D area with a SHRC203 and a Keithley 2100')
        parser.add_argument('num_scans', type = int, help = 'Number of scans to perform')
        args = parser.parse_args()

        default_path = Path(r"C:\Users\DK-microscope\Measurement Data\Daichi")
        scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR", "GPIB0::1::INSTR") # Replace with an actual visa resource.
        # scanner.set_units('um') #set the default unit

        for _ in range(args.num_scans): #In the terminal, input would be python scan_script-Amelie.py 5
            scanner.home(axis = 3) #change axis value
            scanner.focus(8.282*1e3, 3) #change to values that make sense
            df = scanner.scan2d(0, 30, 10, 0, 30, 10)
            scanner.generate_filename(path_root = default_path, myname = "scan", extension="csv")

        scanner.close_connection()

