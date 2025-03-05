from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLineEdit, QGridLayout, QLabel, QFileDialog, QComboBox, QTabWidget
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
        self.colorbar = None  

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Scan Application")
        self.setGeometry(100, 100, 400, 300)

        self.initUI()
        self.scanner = None
        self.set_axis_input.setText("1")

    def initUI(self):
        layout = QVBoxLayout()
        grid_layout = QGridLayout() 

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics1_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics2_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        # grid_layout.addWidget(self.canvas, 2, 0)
        # grid_layout.addWidget(self.harmonics1_canvas, 2, 2)
        # grid_layout.addWidget(self.harmonics2_canvas, 2,4)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics1_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics2_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.tabs.addTab(self.canvas, "2D Scan")
        self.tabs.addTab(self.harmonics1_canvas, "Harmonics 1D")
        self.tabs.addTab(self.harmonics2_canvas, "Harmonics 2D")
        layout.addWidget(self.tabs)        

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

        self.query_position_button = QPushButton("Query Position")
        self.query_position_button.setFixedWidth(200) 
        self.query_position_button.clicked.connect(self.query_position)
        grid_layout.addWidget(self.query_position_button, 2, 0, 1, 6)
        self.query_position_label = QLabel(f"Position: {self.query_position()}")
        grid_layout.addWidget(self.query_position_label, 3, 0, 1, 6)


        layout.addLayout(grid_layout)

        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText("Enter file path")
        self.file_path_input.setFixedWidth(200)
        layout.addWidget(self.file_path_input)

        self.browse_buttom = QPushButton("Browse")
        self.browse_buttom.setFixedWidth(200)
        self.browse_buttom.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_buttom)

        self.file_format_combo = QComboBox(self)
        self.file_format_combo.addItems(["CSV", "HDF5"])
        layout.addWidget(self.file_format_combo)

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
   
        self.initialize_button = QPushButton("Initialize")
        self.initialize_button.clicked.connect(self.initalize)
        self.initialize_button.setFixedWidth(200)
        layout.addWidget(self.initialize_button)

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
        self.start_scan_button.setFixedWidth(200)

        self.show_results_button = QPushButton("Show Results")
        self.show_results_button.clicked.connect(self.show_results)
        self.show_results_button.setFixedWidth(200)

        layout.addWidget(self.start_scan_button)
        layout.addWidget(self.show_results_button)



        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setStyleSheet("""
            QWidget {
                background-color:rgb(4, 52, 99);
                color:rgb(148, 148, 152);
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #003366;
                color: #ffffff;
            }
            QPushButton {
                padding: 5px;
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QPushButton:pressed {
                background-color: #003f8a;
            }
        """)

    
    def __del__(self): 
        if self.scanner is not None:
            self.scanner.close_connection()
          
    @pyqtSlot()
    def initalize(self):
        if self.scanner is None:
            self.scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR", "GPIB0::1::INSTR")
        else: 
            self.scanner.close_connection()
    def query_position(self): 
        try: 
            axis = int(self.set_axis_input.text())
            self.scanner.set_axis(axis)
            position = self.scanner.query_position(axis) 
            print(f"position {position}")
            QMessageBox.information(self, "Position", f"Current position: {position}")
            return position
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return None
        
    @pyqtSlot()
    def browse_file(self):
        file_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if file_path:
            self.file_path_input.setText(file_path)

    @pyqtSlot()
    def set_axis(self): 
        try: 
            axis = int(self.set_axis_input.text())
            self.scanner.set_axis(axis)
            logger.info(f"NanoScanner initialized at {axis}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    @pyqtSlot()
    def move_stage(self): 
        try: 
            move_position = float(self.move_position_input.text())
            self.scanner.move(move_position)
            logger.info(f"Moved stage to position {move_position}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    
    @pyqtSlot() 
    def focus_stage(self):
        try: 
            focus_position = float(self.focus_position_input.text())
            self.scanner.focus(focus_position)
            logger.info(f"Focused stage at position {focus_position}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    @pyqtSlot()
    def start_scan(self):
        # Here you would implement the logic to start the scan using NanoScanner
        try:
            x_start = float(self.x_start_input.text())
            # print(type(x_start), self.x_start_input.text())
            x_stop = float(self.x_stop_input.text())
            # print(type(x_stop))
            x_step = float(self.x_step_input.text())
            # print(type(x_step))
            y_start = float(self.y_start_input.text())
            # print(type(y_start))
            y_stop = float(self.y_stop_input.text())
            # print(type(y_stop))
            y_step = float(self.y_step_input.text())
            # print(type(y_step))

            # Example scan parameters
            df = self.scanner.scan2d(x_start, x_stop, x_step, y_start, y_stop, y_step)

            # self.scanner.generate_filename(self ,path_root, myname, extension="csv")
            directory_path = self.file_path_input.text()
            directory_path = Path(directory_path)
            if directory_path:
                file_format = self.file_format_combo.currentText()
                if file_format == "HDF5":
                    file_name = self.scanner.generate_filename(directory_path, "Scan", extension="h5")
                    df.to_hdf(file_name, key='df', mode='w')
                elif file_format == "CSV":
                    print("This is file_format == 'CSV'")
                    file_name = self.scanner.generate_filename(directory_path, "Scan", extension="csv")
                    print(f"file_name after create file-name {file_name}")
                    df.to_csv(file_name, index=False)
                    print(f"file_name after to_csv {file_name}")
                QMessageBox.information(self, "Scan Complete", "Scan completed successfully!")
            else: 
                QMessageBox.critical(self, "Error", "Please select a directory to save the scan results.")

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

        img = self.canvas.axes.pcolormesh(x_min, y_min, v_reshaped, shading="auto", cmap="viridis")
        if self.canvas.colorbar is None: 
            self.canvas.colorbar = self.canvas.figure.colorbar(img, ax=self.canvas.axes)
        else:
            self.canvas.colorbar.update_normal(img) 
        # if self.canvas.colorbar is not None:
        #     self.canvas.colorbar.remove()
        #     self.canvas.colorbar = None

        self.canvas.axes.set_xlabel("Position X, Y (um)")
        self.canvas.axes.set_ylabel("Voltage (V)")
        self.canvas.draw()

        self.harmonics1_canvas.axes.plot(x, v, label="Harmonics 1d")
        self.harmonics1_canvas.axes.set_xlabel("Position (um)")
        self.harmonics1_canvas.axes.set_ylabel("Harmonics 1d")
        self.harmonics1_canvas.axes.legend()

        self.harmonics2_canvas.axes.plot(y, v, label="Harmonics 2d")
        self.harmonics2_canvas.axes.set_xlabel("Position (um)")
        self.harmonics2_canvas.axes.set_ylabel("Harmonics 2d")
        self.harmonics2_canvas.axes.legend()

        self.harmonics1_canvas.draw()
        self.harmonics2_canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())