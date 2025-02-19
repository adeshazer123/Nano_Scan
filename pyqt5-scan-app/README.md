# PyQt5 Scan Application

This project implements a scanning application using PyQt5, allowing users to perform 2D scans with a SHRC203 and a Keithley 2100. The application provides a graphical user interface (GUI) for easy interaction with the scanning hardware.

## Project Structure

```
pyqt5-scan-app
├── src
│   ├── main.py               # Entry point of the application
│   ├── gui
│   │   ├── main_window.py    # Main GUI layout and functionality
│   │   └── __init__.py       # Package marker for GUI
│   ├── scanner
│   │   ├── scan_script_amelie.py  # Scanning functionality
│   │   └── __init__.py       # Package marker for scanner
│   └── resources
│       └── __init__.py       # Package marker for resources
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Installation

To set up the project, follow these steps:

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies using pip:

   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:

```
python src/main.py
```

This will launch the GUI, where you can start scans and view results.

## Dependencies

The project requires the following Python packages:

- PyQt5
- numpy
- pandas
- matplotlib
- logging

Make sure to install these packages before running the application.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.