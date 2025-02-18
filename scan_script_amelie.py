import matplotlib.pyplot as plt
import time
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging
import argparse
import numpy as np
from shrc203_VISADriver import SHRC203VISADriver as SHRC203
from keithley2100_VISADriver import Keithley2100VISADriver as Keithley
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
    def __init__(self, com_shrc, com_keithley):
        self.path_root = Path(r"C:\Users\DK-microscope\Measurement Data\Astha\keithley") #?????? Fix this. Amelie does not understand why this is needed. We should not need to specify the path here.
        self.shrc = SHRC203(com_shrc)
        self.keithley = Keithley(com_keithley)
        self.shrc.open_connection()
        self.keithley.init_hardware()
    
    def home(self, axis): 
        for i in range(3): 
            self.shrc.home(axis)
            i+=1
            
    def focus(self, position, axis): 
        self.shrc.move(position, axis)

    # def set_units(self, unit: str):
    #     self.shrc.set_unit(unit)

    def generate_filename(self ,path_root, myname, extension="csv"):
        now = datetime.now()
        prefix = now.strftime("%Y%m%d_%H%M%S")

        filename = Path.joinpath(path_root,f"{prefix}_{myname}.{extension}")
        return filename
    
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
        scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR") # Replace with an actual visa resource.
        # scanner.set_units('um') #set the default unit

        for _ in range(args.num_scans): #In the terminal, input would be python scan_script-Amelie.py 5
            scanner.home(axis = 3) #change axis value
            scanner.focus(8.282*1e3, 3) #change to values that make sense
            df = scanner.scan2d(0, 30, 10, 0, 30, 10)
            scanner.generate_filename(path_root = default_path, myname = "scan", extension="csv")

        scanner.close_connection()


#############COMMENTS################
# *  from .... Keithley import ...
# parameters

# # initialize SHRC
# com = "ASRL3::INSTR"
# shrc = SHRC203(com)
# shrc.open_connection()

# * initialize Keithely
# ( 1) USB0::0x05E6::0x2100::1149087::INSTR -> KEITHLEY INSTRUMENTS INC.,MODEL 2100,1,01.08-01-01

# Move to home of Axis 1, 2, and 3 (X, Y, Z, respectively)
# shrc.home(1)
# shrc.home(2)
# shrc.home(3)

# Move relative
# shrc.move_relative(10,1)

# Focus (move absolute)
# shrc.move(8.282*1e3 ,3) # position (um), axis




#################END OF COMMENTS######