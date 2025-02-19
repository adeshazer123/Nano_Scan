import matplotlib.pyplot as plt
import time
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging
import numpy as np
from shrc203_VISADriver import SHRC203VISADriver as SHRC203
from keithley2100_VISADriver import Keithley2100VISADriver as Keithley

logname = 'scan_logger.log' 
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger('scanTest')

class NanoScanner: 
    def __init__(self, com_shrc, com_keithley):
        self.path_root = Path(r"C:\Users\DK-microscope\Measurement Data\Astha\keithley")
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

        plt.ion()

        for j in range(len(y_scan)):
            for i in range(len(x_scan)):
                x = np.append(x, x_scan[i])
                y = np.append(y, y_scan[j])

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