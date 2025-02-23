# This file will focus on Moke and use this to scan and calculate the harmonics 
from sr830_VISADriver import SR830
from shrc203_VISADriver import SHRC203
from keithley2100_VISADriver import Keithley2100
from multizaber import ZaberMultiple
from ccsxxx import CCSXXX

class Moke: 
    def __init__(self, com_shrc, com_sr830, com_keithley, com_zaber, com_ccsx):
        """Connects to the devices and initializes the Moke class"""
        self.shrc = SHRC203(com_shrc) 
        self.shrc.open_connection()

        self.keithley = Keithley2100(com_keithley)
        self.keithley.init_hardware()

        self.zaber = ZaberMultiple()
        self.zaber.connect(com_zaber)

        self.sr830 = SR830(com_sr830)
        self.ccssx = CCSXXX(com_ccsx)
        self.ccssx.connect()
    
