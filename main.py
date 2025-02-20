from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLineEdit
import sys
from PyQt5.QtCore import pyqtSlot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas 
import pandas as pd
from scan_script_amelie import NanoScanner


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

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)

        self.move_position_input = QLineEdit(self)
        self.move_position_input.setPlaceholderText("Enter move position")
        layout.addWidget(self.move_position_input)

        self.focus_position_input = QLineEdit(self)
        self.focus_position_input.setPlaceholderText("Enter focus position")
        layout.addWidget(self.focus_position_input)

        self.start_scan_button = QPushButton("Start Scan")
        self.start_scan_button.clicked.connect(self.start_scan)

        self.show_results_button = QPushButton("Show Results")
        self.show_results_button.clicked.connect(self.show_results)

        layout.addWidget(self.start_scan_button)
        layout.addWidget(self.show_results_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_scan(self):
        # Here you would implement the logic to start the scan using NanoScanner
        try:
            move_position = float(self.move_position_input.text())
            focus_position = float(self.focus_position_input.text())
            scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
            scanner.home(axis = 3)
            scanner.focus(focus_position,3)
            scanner.move(move_position,3)
            # Example scan parameters
            df = scanner.scan2d(0, 30, 10, 0, 30, 10)
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
        scatter = self.canvas.axes.scatter(df["x (um)"], df["y (um)"], c=df["v (V)"], cmap="viridis")
        self.canvas.axes.set_xlabel("Position (um)")
        self.canvas.axes.set_ylabel("Voltage (V)")
        self.canvas.figure.colorbar(scatter, ax=self.canvas.axes)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())