from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QLineEdit, QGridLayout, QLabel, QFileDialog, QComboBox, QTabWidget, QGroupBox, QTextEdit
import sys
import numpy as np
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
import pandas as pd
from scan_script_amelie import NanoScanner
import logging

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = parent
        self.widget.setReadOnly(True)
    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)
        
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  
logger.addHandler(logging.StreamHandler())

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
        self.second_window = None
    def initUI(self):
        layout = QVBoxLayout()
        grid_layout = QGridLayout()

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics1_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics2_canvas = MplCanvas(self, width=5, height=4, dpi=100)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics1_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.harmonics2_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.tabs.addTab(self.canvas, "2D Scan")
        self.tabs.addTab(self.harmonics1_canvas, "Harmonics 1D")
        self.tabs.addTab(self.harmonics2_canvas, "Harmonics 2D")
        layout.addWidget(self.tabs)  

        self.open_wavelength_window_button = QPushButton("Open Wavelength Window")
        self.open_wavelength_window_button.clicked.connect(self.open_wavelength_window)
        self.open_wavelength_window_button.setFixedWidth(200)
        layout.addWidget(self.open_wavelength_window_button)      

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
        
        position_group = QGroupBox("Position Display")
        position_layout = QVBoxLayout() 

        self.query_position_label = QLabel(f"Position: ")
        position_layout.addWidget(self.query_position_label)

        self.query_position_button = QPushButton("Query Position")
        self.query_position_button.setFixedWidth(200) 
        self.query_position_button.clicked.connect(self.query_position)
        position_layout.addWidget(self.query_position_button)

        position_group.setLayout(position_layout)
        layout.addWidget(position_group)
        layout.addLayout(grid_layout)

        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText("Enter file path")
        self.file_path_input.setFixedWidth(200)
        layout.addWidget(self.file_path_input)

        self.browse_buttom = QPushButton("Browse")
        self.browse_buttom.setFixedWidth(200)
        self.browse_buttom.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_buttom)

        self.file_name_input = QLineEdit(self)
        self.file_name_input.setPlaceholderText("Enter file name")
        self.file_name_input.setFixedWidth(200)
        layout.addWidget(self.file_name_input)

        layout.addWidget(QLabel("Select File Format"))
        self.file_format_combo = QComboBox(self)
        self.file_format_combo.addItems(["CSV", "HDF5"])
        self.file_format_combo.setFixedWidth(200)   
        layout.addWidget(self.file_format_combo)

        self.move_position_input = QLineEdit(self)
        self.move_position_input.setPlaceholderText("Enter move position")
        self.move_position_input.setFixedWidth(200)
        layout.addWidget(self.move_position_input)

        self.move_stage_button = QPushButton("Move Stage")
        self.move_stage_button.clicked.connect(self.move_stage)
        self.move_stage_button.setFixedWidth(200)
        layout.addWidget(self.move_stage_button)

        self.move_relative_input = QLineEdit(self)
        self.move_relative_input.setPlaceholderText("Enter relative move")
        self.move_relative_input.setFixedWidth(200)
        layout.addWidget(self.move_relative_input)

        self.move_relative_button = QPushButton("Move Relative")
        self.move_relative_button.clicked.connect(self.move_stage)
        self.move_relative_button.setFixedWidth(200)
        layout.addWidget(self.move_relative_button)

        layout.addWidget(QLabel("Select Axis"))
        self.set_axis_input = QComboBox(self)
        self.set_axis_input.addItems(["1", "2", "3"])  
        self.set_axis_input.setFixedWidth(200)
        self.set_axis_input.currentIndexChanged.connect(self.query_position)
        layout.addWidget(self.set_axis_input)

        self.focus_position_input = QLineEdit(self)
        self.focus_position_input.setPlaceholderText("Enter focus center")
        self.focus_position_input.setFixedWidth(200)
        layout.addWidget(self.focus_position_input)

        self.focus_stage_button = QPushButton("Auto Focus")
        self.focus_stage_button.clicked.connect(self.focus_stage)
        self.focus_stage_button.setFixedWidth(200)
        layout.addWidget(self.focus_stage_button)

        initialize_container = QVBoxLayout()

        initalize_layout = QHBoxLayout()
        self.initialize_button = QPushButton("Initialize")
        self.initialize_button.clicked.connect(self.initalize)
        self.initialize_button.setFixedWidth(200)
        initalize_layout.addWidget(self.initialize_button)

        self.green_laser_button = QPushButton()
        self.green_laser_button.setFixedWidth(20)
        self.green_laser_button.setFixedHeight(20)
        self.green_laser_button.setStyleSheet("background-color: red; border-radius: 10px;")
        initalize_layout.addWidget(self.green_laser_button)

        initalize_layout.setAlignment(Qt.AlignLeft)

        initialize_container.addLayout( initalize_layout)
        layout.addLayout(initialize_container)

        self.start_scan_button = QPushButton("Start Scan")
        self.start_scan_button.clicked.connect(self.start_scan)
        self.start_scan_button.setFixedWidth(200)

        layout.addWidget(self.start_scan_button)

        log_text_edit = QTextEdit()
        self.log_text = QTextEditLogger(log_text_edit)
        layout.addWidget(log_text_edit)
        logger.addHandler(self.log_text)
        
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
            self.scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR", "GPIB0::1::INSTR", com_zaber="COM5", com_ccsx='USB0::0x1313::0x8087::M00934802::RAW', com_pem="ASRL6::INSTR")
            self.green_laser_button.setStyleSheet("background-color: green; border-radius: 10px;")
            logger.info("Initialized NanoScanner")
        else: 
            self.scanner.close_connection()
            self.green_laser_button.setStyleSheet("background-color: red; border-radius: 10px;")
            logger.info("Closed NanoScanner connection")
    @pyqtSlot()
    def query_position(self): 
        try: 
            axis = int(self.set_axis_input.currentText())
            self.scanner.set_axis(axis)
            position = self.scanner.query_position(axis) 
            logging.debug(f"position {position}")
            self.query_position_label.setText(f"Position: {position}")
            
            return position
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return None
        
    @pyqtSlot()
    def browse_file(self):
        file_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if file_path:
            self.file_path_input.setText(file_path)
    
    def open_wavelength_window(self):
        if self.second_window is None: 
            self.second_window = WavelengthWindow(self.scanner, self.file_path_input.text(), self.file_format_combo.currentText())
        self.second_window.show()

    @pyqtSlot()
    def move_stage(self): 
        try: 
            sender = self.sender()
            if sender == self.move_relative_button:
                move_relative = float(self.move_relative_input.text())
                self.scanner.move_relative(move_relative)
                self.query_position()
                logger.debug(f"Moved stage to relative position {move_relative}")
            elif sender == self.move_stage_button:
                move_position = float(self.move_position_input.text())
                self.scanner.move(move_position)
                self.query_position()
                logger.debug(f"Moved stage to position {move_position}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    
    @pyqtSlot() 
    def focus_stage(self):
        try: 
            rough_focus = float(self.focus_position_input.text())
            # x_start = float(self.x_start_input.text())
            # y_start = float(self.y_start_input.text())
            self.scanner.auto_focus(rough_focus)
            logger.debug(f"Focused stage at position {rough_focus}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    @pyqtSlot()
    def start_scan(self):
        # Here you would implement the logic to start the scan using NanoScanner
        try:
            step = float(self.x_step_input.text())
            index_zaber = 1 # int(self.set_axis_input.currentText()) # DK - this is zaber's axis index, which should be independent of SHRC's set_axis_input
            x_start = float(self.x_start_input.text())
            logging.debug(type(x_start), self.x_start_input.text())
            x_stop = float(self.x_stop_input.text())
            logging.debug(type(x_stop))
            x_step = float(self.x_step_input.text())
            logging.debug(type(x_step))
            y_start = float(self.y_start_input.text())
            logging.debug(type(y_start))
            y_stop = float(self.y_stop_input.text())
            logging.debug(type(y_stop))
            y_step = float(self.y_step_input.text())
            logging.debug(type(y_step))

            # Example scan parameters
            self.scan_data = []
            # self.scan_timer.start(1000)
            df = self.scanner.scan2d_moke(x_start, x_stop, x_step, y_start, y_stop, y_step)
            # df_t = self.scanner.moke_spectroscopy(step, index_zaber)

            # self.scanner.generate_filename(self ,path_root, myname, extension="csv")
            directory_path = self.file_path_input.text()
            directory_path = Path(directory_path)
            file_name = self.file_name_input.text()
            logging.debug(f"file_name after create file-name {file_name}")
            if directory_path:
                file_format = self.file_format_combo.currentText()
                if file_format == "HDF5":
                    file_name = self.scanner.generate_filename(directory_path, file_name, extension="h5")
                    logger.info(f"Saving scan data to {file_name}")
                    df.to_hdf(file_name, key='df', mode='w')
                    # df_t.to_hdf(file_name, key='df_t', mode='a')
                elif file_format == "CSV":
                    logging.debug("This is file_format == 'CSV'")
                    file_name = self.scanner.generate_filename(directory_path, file_name, extension="csv")
                    logger.info(f"Saving scan data to {file_name}")
                    df.to_csv(file_name, index=False)
                    logging.debug(f"file_name after to_csv {file_name}")
                QMessageBox.information(self, "Scan Complete", "Scan completed successfully!")
            else: 
                QMessageBox.critical(self, "Error", "Please select a directory to save the scan results.")

            self.plot_scan_results(df)
            # self.plot_scan_results(df_t) # Can you create a separate button to start lock-in spectroscopy?
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
        x1 = df["x1 (V)"].values
        x2 = df["x2 (V)"].values

        x_min = np.unique(x)
        y_min = np.unique(y)
        v_reshaped = v.reshape(len(y_min), len(x_min))
        x1_v = (x1 / v).reshape(len(y_min), len(x_min))
        x2_v = (x2 / v).reshape(len(y_min), len(x_min))

        # x1/v, x2/v

        img = self.canvas.axes.pcolormesh(x_min, y_min, v_reshaped, shading="auto", cmap="viridis")
        if self.canvas.colorbar is None: 
            self.canvas.colorbar = self.canvas.figure.colorbar(img, ax=self.canvas.axes)
        else:
            self.canvas.colorbar.update_normal(img) 
        # if self.canvas.colorbar is not None:
        #     self.canvas.colorbar.remove()
        #     self.canvas.colorbar = None

        self.canvas.axes.set_xlabel("Position X (um)")
        self.canvas.axes.set_ylabel("Position Y (um)")
        self.canvas.draw()

        # harmonics1_data = self.scanner.harmonics_one()DK - we should use the values in df, not taking data here
        # harmonics2_data = self.scanner.harmonics_two()
        img1 = self.harmonics1_canvas.axes.pcolormesh(x_min, y_min, x1_v, shading="auto", cmap="viridis")
        if self.harmonics1_canvas.colorbar is None:
            self.harmonics1_canvas.colorbar = self.harmonics1_canvas.figure.colorbar(img1, ax=self.harmonics1_canvas.axes)
        else:
            self.harmonics1_canvas.colorbar.update_normal(img1)

        self.harmonics1_canvas.axes.set_xlabel("Position X (um)")
        self.harmonics1_canvas.axes.set_ylabel("Position Y (um)")
        self.harmonics1_canvas.draw()

        img2 = self.harmonics2_canvas.axes.pcolormesh(x_min, y_min, x2_v, shading="auto", cmap="viridis")
        if self.harmonics2_canvas.colorbar is None:
            self.harmonics2_canvas.colorbar = self.harmonics2_canvas.figure.colorbar(img2, ax=self.harmonics2_canvas.axes)
        else:
            self.harmonics2_canvas.colorbar.update_normal(img2)
        
        self.harmonics2_canvas.axes.set_xlabel("Position X (um)")
        self.harmonics2_canvas.axes.set_ylabel("Position Y (um)")
        self.harmonics2_canvas.draw()

class WavelengthWindow(QMainWindow): 
    def __init__(self, scanner=None, file_path_input=None, file_format_combo=None):
        super().__init__()
        self.setWindowTitle("Second Experiment of Wavelength")
        self.setGeometry(150,150,600,400)
        self.scanner = scanner
        self.file_path_input = file_path_input
        self.file_format_combo = file_format_combo
        self.initUI()
    def initUI(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.wavelength1_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.wavelength2_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.wavelength3_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.tabs.addTab(self.wavelength1_canvas, "Reflection")
        self.tabs.addTab(self.wavelength2_canvas, "Kerr")
        self.tabs.addTab(self.wavelength3_canvas, "Ellipticity")
        layout.addWidget(self.tabs)

        self.set_step_input = QLineEdit(self)
        self.set_step_input.setPlaceholderText("Enter wavelength step (nm)")
        layout.addWidget(self.set_step_input)

        self.add_zaber_index = QComboBox(self)
        self.add_zaber_index.addItems(["Linear", "Rotary"])
        layout.addWidget(self.add_zaber_index)

        self.start_scan_button = QPushButton("Start Scan")
        self.start_scan_button.clicked.connect(self.start_scan)
        self.start_scan_button.setFixedWidth(200)
        layout.addWidget(self.start_scan_button)

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

    @pyqtSlot()
    def start_scan(self): 
        try: 
            step = float(self.set_step_input.text())
            zaber_index = self.add_zaber_index.currentText()
            if zaber_index == "Linear": 
                zaber_index = 1 
            else: 
                zaber_index = 2
            df = self.scanner.moke_spectroscopy(step)
            directory_path = self.file_path_input
            directory_path = Path(directory_path)
            if directory_path:
                file_format = self.file_format_combo
                if file_format == "HDF5":
                    file_name = self.scanner.generate_filename(directory_path, "SPE", extension="h5")
                    logger.info(f"Saving scan data to {file_name}")
                    df.to_hdf(file_name, key='df', mode='w')
                    # df_t.to_hdf(file_name, key='df_t', mode='a')
                elif file_format == "CSV":
                    logging.debug("This is file_format == 'CSV'")
                    file_name = self.scanner.generate_filename(directory_path, "SPE", extension="csv")
                    logging.debug(f"file_name after create file-name {file_name}")
                    logger.info(f"Saving scan data to {file_name}")
                    df.to_csv(file_name, index=False)
                    # df_t.to_csv(file_name, index=False)
                    logging.debug(f"file_name after to_csv {file_name}")
                QMessageBox.information(self, "Scan Complete", "Scan completed successfully!")
            else: 
                QMessageBox.critical(self, "Error", "Please select a directory to save the scan results.")

            self.plot_scan_results(df)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    
    def plot_scan_results(self, df): 
        self.wavelength1_canvas.axes.clear()
        self.wavelength2_canvas.axes.clear()
        self.wavelength3_canvas.axes.clear()

        x = df["x (um)"].values
        y = df["y (um)"].values
        wavelength = df["wavelength (nm)"].values
        reflection = df["reflection (a.u,)"].values
        kerr = df["kerr"].values
        ellip = df["ellip"].values
        power = df["ref power (W)"].values

        # x_min = np.unique(x)
        # y_min = np.unique(y)
        # x1/v, x2/v

        # Replace pcolormesh with other plot types to show a spectrum
        self.wavelength1_canvas.axes.plot(wavelength, reflection, "o")
        # if self.canvas.colorbar is not None:
        #     self.canvas.colorbar.remove()
        #     self.canvas.colorbar = None

        self.wavelength1_canvas.axes.set_xlabel("Wavelength (nm)")
        self.wavelength1_canvas.axes.set_ylabel("Reflection")
        self.wavelength1_canvas.draw()
       
        self.wavelength2_canvas.axes.plot(wavelength, kerr, "o")
        self.wavelength2_canvas.axes.set_xlabel("Wavelength (nm)")
        self.wavelength2_canvas.axes.set_ylabel("Kerr")
        self.wavelength2_canvas.draw()

        self.wavelength3_canvas.axes.plot(wavelength, ellip, "o")
        self.wavelength3_canvas.axes.set_xlabel("Wavelength (nm)")
        self.wavelength3_canvas.axes.set_ylabel("Elliptec")
        self.wavelength3_canvas.draw()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())