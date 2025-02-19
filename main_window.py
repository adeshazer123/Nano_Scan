from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import pyqtSlot
import sys
from scan_script_amelie import NanoScanner

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Scan Application")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_scan)
        self.layout.addWidget(self.scan_button)

        self.result_label = QLabel("Scan Results will be displayed here.")
        self.layout.addWidget(self.result_label)

        self.save_button = QPushButton("Save Results")
        self.save_button.clicked.connect(self.save_results)
        self.layout.addWidget(self.save_button)

        self.scanner = None

    @pyqtSlot()
    def start_scan(self):
        self.scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
        self.scanner.home(axis=3)
        self.scanner.focus(8.282 * 1e3, 3)
        df = self.scanner.scan2d(0, 30, 10, 0, 30, 10)
        self.result_label.setText(f"Scan completed. Data points: {len(df)}")

    @pyqtSlot()
    def save_results(self):
        if self.scanner:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;All Files (*)", options=options)
            if file_name:
                df.to_csv(file_name, index=False)
                self.result_label.setText(f"Results saved to {file_name}")

    def closeEvent(self, event):
        if self.scanner:
            self.scanner.close_connection()
        event.accept()