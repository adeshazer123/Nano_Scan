from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot
import sys
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
from scan_script_amelie import NanoScanner

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Scan Application")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)

        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_scan)
        self.layout.addWidget(self.scan_button)

        self.result_label = QLabel("Scan Results will be displayed here.")
        self.layout.addWidget(self.result_label)

        self.save_button = QPushButton("Save Results")
        self.save_button.clicked.connect(self.save_results)
        self.layout.addWidget(self.save_button)

        self.scanner = None
        self.df = None

    @pyqtSlot()
    def start_scan(self):
        try:
            self.scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
            self.scanner.home(axis=3)
            self.scanner.focus(8.282 * 1e3, 3)
            self.df = self.scanner.scan2d(0, 30, 10, 0, 30, 10)
            self.result_label.setText(f"Scan completed. Data points: {len(self.df)}")
            self.plot_scan_results(self.df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    @pyqtSlot()
    def save_results(self):
        if self.scanner:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;HDF5 Files (*.h5);;All Files (*)", options=options)

            if file_name:
                if file_name.endswith(".h5"):
                    self.df.to_hdf(file_name, key='df', mode='w')
                    self.result_label.setText(f"Results saved to {file_name}")
                elif file_name.endswith(".csv"):
                    self.df.to_csv(file_name, index=False)
                    self.result_label.setText(f"Results saved to {file_name}")
                else: 
                    self.df.to_csv(file_name + ".csv", index=False)
                    self.df.to_hdf(file_name + ".h5", key='df', mode='w')
                    self.result_label.setText(f"Results saved to {file_name}.csv and {file_name}.h5")

    def plot_scan_results(self, df): 
        self.canvas.axes.clear()
        # Assuming df has columns "x (um)", "y (um)", and "v (V)"
        x = df["x (um)"].values
        y = df["y (um)"].values
        v = df["v (V)"].values

        # Reshape the data for imshow
        x_unique = np.unique(x)
        y_unique = np.unique(y)
        v_reshaped = v.reshape(len(y_unique), len(x_unique))

        # Display the image
        img = self.canvas.axes.imshow(v_reshaped, extent=[x.min(), x.max(), y.min(), y.max()], origin='lower', cmap='viridis')
        self.canvas.axes.set_xlabel("Position (um)")
        self.canvas.axes.set_ylabel("Voltage (V)")
        self.canvas.figure.colorbar(img, ax=self.canvas.axes)
        self.canvas.draw()

    def closeEvent(self, event):
        if self.scanner:
            self.scanner.close_connection()
        event.accept()