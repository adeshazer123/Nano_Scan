from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
import sys
from scan_script_amelie import NanoScanner

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Scan Application")
        self.setGeometry(100, 100, 400, 300)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

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
            scanner = NanoScanner("COM3", "USB0::0x05E6::0x2100::1149087::INSTR")
            # Example scan parameters
            df = scanner.scan2d(0, 30, 10, 0, 30, 10)
            QMessageBox.information(self, "Scan Complete", "Scan completed successfully!")
            scanner.close_connection()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def show_results(self):
        # Implement logic to display scan results
        QMessageBox.information(self, "Results", "Displaying scan results...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())