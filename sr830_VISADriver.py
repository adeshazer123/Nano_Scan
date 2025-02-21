from pymeasure.instruments.srs.sr830 import SR830

class SR830VISADriver:

    def __init__(self, com: str):
        self.com = com
        self.controller = SR830(self.com)

    def read_r_theta(self):
        self.controller.snap('R', 'Theta')
        return self.controller.snap('R', 'Theta')
    
    def set_harmonics(self, harmonic):
        self.controller.harmonic = harmonic

    def get_harmonics(self):
        self.controller.harmonic
        return self.controller.harmonic