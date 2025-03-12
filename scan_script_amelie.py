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
from multizaber import ZaberMultiple
from shrc203_VISADriver import SHRC203VISADriver as SHRC203
from keithley2100_VISADriver import Keithley2100VISADriver as Keithley
from pymeasure.instruments.srs.sr830 import SR830
from ccsxxx import CCSXXX
from pem200_driver import PEM200Driver

# print(os.getcwd())
# # logger.debug('This message should go to the log file')
logname = 'scan_logger.log' 
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger('scanTest')


class NanoScanner: 
    def __init__(self, com_shrc, com_keithley, com_sr830, com_zaber, com_ccsx, com_pem, index_powermeter=0, index_zaber=1):
        # self.path_root = Path(r"C:\Users\DK-microscope\Measurement Data") #?????? Fix this. Amelie does not understand why this is needed. We should not need to specify the path here.
        self.shrc = SHRC203(com_shrc)
        self.keithley = Keithley(com_keithley)
        self.keithley.init_hardware()

        self.sr830 = SR830(com_sr830)
        
        self.pwmeter = CustomTLPM()
        self.pwmeter.open_by_index(index_powermeter)
        
        self.zaber = ZaberMultiple()
        
        self.pem = PEM200Driver(com_pem)
        self.pem.connect()
        self.pem.set_retardation(0.25)
        self.pem.set_pem_output(1)

        self.wavelength = CCSXXX(com_ccsx)
        self.wavelength.connect()
        self.zaber.connect(com_zaber)
        self.shrc.open_connection()

        self.axis = 1
        self.index_powermeter = index_powermeter
        self.index_zaber = index_zaber
    
    def home(self): 
        for i in range(3): 
            i+=1            
            self.shrc.home(i)
            
    def focus(self, position): 
        self.shrc.move(position, self.axis)

    def move(self, position): 
        self.shrc.move(position, self.axis)
    
    def move_relative(self, position): 
        self.shrc.move_relative(position, self.axis)
    
    def set_axis(self, axis): 
        self.axis = axis

    def query_position(self, axis):
        return self.shrc.query_position(axis)
    
    def get_position_xyz(self):
        x = self.shrc.query_position(1)
        y = self.shrc.query_position(2)
        z = self.shrc.query_position(3)
        return x, y, z
    def harmonics_one(self): 
        self.sr830.harmonic = 1
        time.sleep(self.sr830.time_constant*1.1)
        self.sr830.quick_range()
        x, theta = self.sr830.snap('X', 'Theta')
        return x, theta

    def harmonics_two(self): 
        """Reads the r and theta values for the second harmonic
        Args: 
            wait_time (float): Time to wait between measurements
            Returns:
            x2 (float): r value for the second harmonic
            theta2 (float): theta value for the second harmonic
            """
        self.sr830.harmonic = 2
        time.sleep(self.sr830.time_constant*1.1)
        self.sr830.quick_range()
        x, theta = self.sr830.snap('X', 'Theta')
        return x, theta
    
    def auto_focus(self, x, y, z):
        """Auto focus for the SHRC203 scanner 
        Args: 
            x (float): x position
            y (float): y position
            z (float): z position
            """
        self.shrc.move(x, 1)
        self.shrc.move(y, 2)
        z_array, v_array = self.scan1d(z-40, z+40, 1.0, axis = 3, myname = "auto_focus")
        z_max = z_array[np.argmax(v_array)]

        self.shrc.move(z_max, 3)


    def generate_filename(self ,path_root, myname, extension="csv"):
        now = datetime.now()
        prefix = now.strftime("%Y%m%d_%H%M%S")

        filename = Path.joinpath(path_root,f"{prefix}_{myname}.{extension}")
        return filename

    
    def get_wavelength(self): 
        wave = self.wavelength.get_wavelength_data()
        self.wavelength.start_scan()
        intensity = self.wavelength.get_scan_data()
        return wave[intensity.argmax()]

    def wavelength_to_position(self, wavelength): 
        position = -66.5 * wavelength + 63840
        return position * 1e-3
    
    def get_power(self, wavelength): 
        self.pwmeterwavelength = wavelength
        return self.pwmeter.get_power()

    def scan2d_moke(self, x_start, x_stop, x_step, y_start, y_stop, y_step, myname="scan_moke", wait_time = 0.3):
        x_scan = np.arange(x_start, x_stop, x_step)
        y_scan = np.arange(y_start, y_stop, y_step)

        x = np.array([])
        y = np.array([])
        v = np.array([])
        x1 = np.array([])
        theta1 = np.array([]) 
        x2 = np.array([]) 
        theta2 = np.array([]) 
        Rv = np.array([])

        self.shrc.move(x_scan[0], 1)
        # time.sleep(5)
        self.shrc.move(y_scan[0], 2)
        # time.sleep(5)

        x_current, y_current, z_current = self.get_position_xyz()
        # self.auto_focus(x_current, y_current, z_current)

        plt.ion()
        for j in range(len(y_scan)):
            self.shrc.move(y_scan[j], 2)
            # time.sleep(wait_time)

            for i in range(len(x_scan)):
                self.shrc.move(x_scan[i], 1)

                # time.sleep(wait_time)
                x = np.append(x, x_scan[i])
                y = np.append(y, y_scan[j])

                voltage_current = self.keithley.read() # Measure voltage in Keithley
                voltage = np.append(voltage, voltage_current)

                x1_value, theta1_value = self.harmonics_one(wait_time) # Measure first harmonic in the lock-in amplifier
                x2_value, theta2_value = self.harmonics_two(wait_time) # Measure second harmonic in the lock-in amplifier   

                # x1_value, theta1_value, x2_value, theta2_value = self.read_moke() # Measure MOKE in the lock-in amplifier

                x1 = np.append(x1, x1_value)
                theta1 = np.append(theta1, theta1_value)
                x2 = np.append(x2, x2_value)
                theta2 = np.append(theta2, theta2_value)
                plt.clf()

                plt.subplot(131)
                plt.scatter(x, y, c=voltage)
                plt.title('Reflection')

                plt.subplot(132)
                plt.scatter(x, y, c=x2/voltage) # TODO replace with theta_k
                plt.title('x2/v')
                plt.xlabel('Position (um)')
                plt.ylabel('x2/v')
                plt.pause(0.05)

                plt.subplot(133)
                plt.scatter(x, y, c=x1/voltage)
                plt.title('x1/v')
                plt.xlabel('Position (um)')
                plt.ylabel('x1/v')
                plt.pause(0.05)

                # also plot x,y,x2/v, x1/v
        df = pd.DataFrame({"x (um)":x, "y (um)":y, "v (V)":voltage, "x1 (V)":x1, "kerr": x2/voltage, "ellip": x1/voltage, "theta1 (deg)":theta1, "x2 (V)":x2, "theta2 (deg)":theta2})
        
        return df

    def moke_spectroscopy(self, step=5, myname="moke_spe"):
        step = 5
        x, y, z = self.get_position_xyz()
        voltage = np.array([])
        power = np.array([])
        wavelength = np.array([])
        x1 = np.array([])
        theta1 = np.array([])
        x2 = np.array([])
        theta2 = np.array([])
        position = np.array([])

        plt.ion() 

        self.zaber.move_abs(0, self.index_zaber)

        wavelength_read = self.get_wavelength()

        while wavelength_read > 700:
            zaber_shift = 13.3 / (970 - 690) * step
            self.zaber.move_relative(zaber_shift, self.index_zaber)

            # time.sleep(0.5)
            wavelength_read = self.get_wavelength()
            power_read = self.get_power(wavelength_read)
            self.pem.set_modulation_amplitude(wavelength_read)

            voltage_read = self.keithley.read()

            voltage = np.append(voltage, voltage_read)
            wavelength = np.append(wavelength, wavelength_read)

            x1_value, theta1_value = self.harmonics_one()
            x2_value, theta2_value = self.harmonics_two()

            x1 = np.append(x1, x1_value)
            theta1 = np.append(theta1, theta1_value)
            x2 = np.append(x2, x2_value)
            theta2 = np.append(theta2, theta2_value)
            power = np.append(power, power_read)

            plt.clf()
            plt.subplot(131)
            plt.plot(wavelength, voltage / power, "o")
            plt.title("Reflection")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Reflection (a.u.)")

            plt.subplot(132)
            plt.plot(wavelength, x2/voltage, "o")
            plt.title("Kerr")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Kerr (a.u.)")
            plt.pause(0.05)

            plt.subplot(133)
            plt.plot(wavelength, x1/voltage, "o")
            plt.title("Ellipticity")
            plt.xlabel("Wavelength (nm)")
            plt.ylabel("Ellipticity (a.u.)")
            plt.pause(0.05)

            plt.tight_layout()

        data = {
            "x (um)": x, "y (um)": y, "z (um)": z, "wavelength (nm)": wavelength, "ref power (W)": power, "v (V)": voltage,
            "reflection (a.u,)": voltage / power, "x1 (V)": x1, "theta1 (deg)": theta1, "x2 (V)": x2, "theta2 (deg)": theta2,
            "kerr": x2/voltage, "ellip": x1/voltage
        }
        
        df = pd.DataFrame(data)
        # df.to_csv(self.generate_filename(myname, "csv"))
        return df

    def scan1d(self, x_start, x_stop, x_step, axis =1, myname = "scan1d"):
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
        # time.sleep(5)

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

            # time.sleep(0.5)

        # plt.plot(x, v)
        # plt.savefig(self.generate_filename(self.path_root,"scan", "png"))

        # df = pd.DataFrame({"x (um)":x, "v (V)":v})
        return x, v

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

                # time.sleep(0.5)

        plt.pcolormesh(x_scan,y_scan,v.reshape(len(x_scan), len(y_scan)), shading="auto")
        plt.colorbar()
        # plt.savefig(self.generate_filename(self.path_root,"scan", "png"))

        df = pd.DataFrame({"x (um)":x, "y (um)":y, "v (V)":v})
        return df

    def close_connection(self): 
        self.shrc.close()
        self.keithley.close()
        self.pem.set_pem_output(0)
        self.pem.close()

if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Scan a 2D area with a SHRC203 and a Keithley 2100')
        parser.add_argument('num_scans', type = int, help = 'Number of scans to perform')
        args = parser.parse_args()

        scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR", "GPIB0::1::INSTR", com_zaber="COM5", com_ccsx='USB0::0x1313::0x8087::M00934802::RAW', com_pem="ASRL6::INSTR") # Replace with an actual visa resource.
        index_zaber = 1
        index_powermeter = 0

        for _ in range(args.num_scans): #In the terminal, input would be python scan_script-Amelie.py 5
            # scanner.home() #change axis value
            # scanner.focus(8.282*1e3, 3) #change to values that make sense
            # df = scanner.scan2d(0, 30, 10, 0, 30, 10)
            # scanner.generate_filename(path_root = default_path, myname = "scan", extension="csv")

            df = scanner.moke_spectroscopy(10,1)
            # scanner.generate_filename(path_root = default_path, myname = "moke_spe", extension="csv")

        scanner.close_connection()