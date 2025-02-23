from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLineEdit, QGridLayout, QLabel
import sys
import numpy as np
from PyQt5.QtCore import pyqtSlot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
import pandas as pd
from scan_script_amelie import NanoScanner
import logging
logger = logging.getLogger(__name__)
class MplCanvas(FigureCanvas):
    def __init__(self, parent = None, width = 5, height = 4, dpi = 100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Scan Application")
        self.setGeometry(100, 100, 400, 300)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        grid_layout = QGridLayout() 

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics1_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics2_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        grid_layout.addWidget(self.canvas, 2, 0)
        grid_layout.addWidget(self.harmonics1_canvas, 2, 2)
        grid_layout.addWidget(self.harmonics2_canvas, 2,4)

        self.x_start_input = QLineEdit(self)
        self.x_start_input.setPlaceholderText("Enter x start")
        grid_layout.addWidget(QLabel("X Start"), 0, 0) 
        grid_layout.addWidget(self.x_start_input, 0, 1)

        self.x_stop_input = QLineEdit(self)
        self.x_stop_input.setPlaceholderText("Enter x stop")
        grid_layout.addWidget(QLabel("X Stop"), 0, 2)
        grid_layout.addWidget(self.x_stop_input, 0, 3)

        self.x_step_input = QLineEdit(self)
        self.x_step_input.setPlaceholderText("Enter x step")
        grid_layout.addWidget(QLabel("X Step"), 0, 4)
        grid_layout.addWidget(self.x_step_input, 0, 5)

        self.y_start_input = QLineEdit(self)
        self.y_start_input.setPlaceholderText("Enter y start")
        grid_layout.addWidget(QLabel("Y Start"), 1, 0)
        grid_layout.addWidget(self.y_start_input, 1, 1)

        self.y_stop_input = QLineEdit(self)
        self.y_stop_input.setPlaceholderText("Enter y stop")
        grid_layout.addWidget(QLabel("Y Stop"), 1, 2)
        grid_layout.addWidget(self.y_stop_input, 1, 3)

        self.y_step_input = QLineEdit(self)
        self.y_step_input.setPlaceholderText("Enter y step")
        grid_layout.addWidget(QLabel("Y Step"), 1, 4)
        grid_layout.addWidget(self.y_step_input, 1, 5)

        layout.addLayout(grid_layout)

        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText("Enter file path")
        self.file_path_input.setFixedWidth(200)
        layout.addWidget(self.file_path_input)

        self.move_position_input = QLineEdit(self)
        self.move_position_input.setPlaceholderText("Enter move position")
        self.move_position_input.setFixedWidth(200)
        layout.addWidget(self.move_position_input)

        self.set_axis_input = QLineEdit(self)   
        self.set_axis_input.setPlaceholderText("Enter axis")
        self.set_axis_input.setFixedWidth(200)
        layout.addWidget(self.set_axis_input)

        self.focus_position_input = QLineEdit(self)
        self.focus_position_input.setPlaceholderText("Enter focus position")
        self.focus_position_input.setFixedWidth(200)
        layout.addWidget(self.focus_position_input)

        self.move_stage_button = QPushButton("Move Stage")
        self.move_stage_button.clicked.connect(self.move_stage)
        self.move_stage_button.setFixedWidth(200)
        layout.addWidget(self.move_stage_button)

        self.set_axis_button = QPushButton("Set Axis")
        self.set_axis_button.clicked.connect(self.set_axis)
        self.set_axis_button.setFixedWidth(200)
        layout.addWidget(self.set_axis_button)

        self.focus_stage_button = QPushButton("Focus Stage")
        self.focus_stage_button.clicked.connect(self.focus_stage)
        self.focus_stage_button.setFixedWidth(200)
        layout.addWidget(self.focus_stage_button)

        self.start_scan_button = QPushButton("Start Scan")
        self.start_scan_button.clicked.connect(self.start_scan)

        self.show_results_button = QPushButton("Show Results")
        self.show_results_button.clicked.connect(self.show_results)

        layout.addWidget(self.start_scan_button)
        layout.addWidget(self.show_results_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setStyleSheet("""QWidget { background-color: #001f3f;
                           color: #ffffff; 
                            }
                           QLineEdit {
                           padding: 5px;}
                           border: 1px solid #ccc;
                           border-radius: 5px;
                           }
                           QPushButton {
                           padding: 10px; 
                           background-color: #0078d7; 
                           color: black;
                           border: none;
                           border-radius: 5px;
                           }
                           QPushButton:hover {
                           background-color: #0056b3;
                           }
                           QPushButton:pressed {
                           background-color: #003f8a;
                           }
                           """)
    @pyqtSlot()
    def set_axis(self, axis): 
        try: 
            axis = int(self.set_axis_input.text())
            scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
            scanner.home(axis)
            scanner.close_connection()
            logger.info(f"Homed axis {axis}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    @pyqtSlot()
    def move_stage(self): 
        try: 
            move_position = float(self.move_position_input.text())
            scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
            scanner.move(move_position, 3)
            scanner.close_connection()
            logger.info(f"Moved stage to position {move_position}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    
    @pyqtSlot() 
    def focus_stage(self):
        try: 
            focus_position = float(self.focus_position_input.text())
            scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
            scanner.focus(focus_position, 3)
            scanner.close_connection()
            logger.info(f"Focused stage at position {focus_position}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    @pyqtSlot()
    def start_scan(self):
        # Here you would implement the logic to start the scan using NanoScanner
        try:
            x_start = float(self.x_start_input.text())
            x_stop = float(self.x_stop_input.text())
            x_step = float(self.x_step_input.text())
            y_start = float(self.y_start_input.text())
            y_stop = float(self.y_stop_input.text())
            y_step = float(self.y_step_input.text())

            scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR", "GPIB0::1::INSTR")
            # Example scan parameters
            df = scanner.scan2d(x_start, x_stop, x_step, y_start, y_stop, y_step)
            QMessageBox.information(self, "Scan Complete", "Scan completed successfully!")
            scanner.close_connection()
            self.plot_scan_results(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    @pyqtSlot()
    def show_results(self):
        # Implement logic to display scan results
        QMessageBox.information(self, "Results", "Displaying scan results...")
    def plot_scan_results(self, df): 
        self.canvas.axes.clear()
        self.harmonics1_canvas.axes.clear()
        self.harmonics2_canvas.axes.clear()
        x = df["x (um)"].values
        y = df["y (um)"].values
        v = df["v (V)"].values

        x_min = np.unique(x)
        y_min = np.unique(y)
        v_reshaped = v.reshape(len(y_min), len(x_min))

        img = self.canvas.axes.pcolormesh(x_min, y_min, v_reshaped, shading = "auto", cmap = "viridis")
        self.canvas.axes.set_xlabel("Position X, Y (um)")
        self.canvas.axes.set_ylabel("Voltage (V)")
        self.canvas.figure.colorbar(img, ax=self.canvas.axes)
        self.canvas.draw()

        self.harmonics1_canvas.axes.plot(x, v, )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())