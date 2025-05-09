# MAVLink View-Exporter
MAVLink View-Exporter Screenshot

<img src="https://github.com/SAMMYBOOOOM/mavlink-view-exporter/blob/master/image/image.png" width="500">

## Overview
MAVLink View-Exporter is a Python-based graphical tool for visualizing and exporting MAVLink telemetry data from `.tlog` files. The application provides:

- Interactive plotting of MAVLink message fields

- Multi-plot grid layouts with pagination

- XML export capabilities for selected data

- User-friendly interface with developer branding

## Features
- Log File Analysis: Load and parse MAVLink telemetry logs (`.tlog` format)

- Data Visualization:

  - Plot individual message fields

  - "Plot All" functionality for comprehensive data review

  - Customizable grid layouts (rows × columns)

- Data Export:

  - Export selected fields to XML format

  - Batch export of all data for a message type

- User Interface:

  - Message type, instance ID, and field selectors

  - Time cursor with real-time value display

  - Pagination for multi-plot views

## Installation
Prerequisites
Python 3

Required packages (install via pip):

```bash
pip install pymavlink matplotlib tkinter
```
Running the Application
Clone the repository:

```bash
git clone https://github.com/SAMMYBOOOOM/mavlink-view-exporter.git
cd mavlink-view-exporter
```
Run the main application:

```bash
python main.py
```
## Usage
1. Launch the application: Run `main.py` to start the MAVLink launcher.

2. Open Plotter: Click "Open Plotter" to load the visualization tool.

3. Load Log File: Use the "Load Log" button to select a `.tlog` file.

4. Select Data:

    - Choose a message type from the dropdown

    - Select an instance ID (if available)

    - Pick a field to visualize

5. Visualize Data:

    - Click "Plot" to view the selected field

    - Use "Plot All" to generate all available plots

    - Adjust grid layout with the rows/columns controls

6. Export Data:

    - Use the "Export" button to save selected data as XML

    - The standalone XML Exporter provides advanced field selection

## License
This project is licensed under the GNU General Public License v2.0 - see the LICENSE file for details.

## Developer
Developed by Sam

<img src="https://github.com/SAMMYBOOOOM/mavlink-view-exporter/blob/master/image/dev.png" width="100">

## Contributing
Contributions are welcome! Please fork the repository and submit pull requests. For major changes, please open an issue first to discuss proposed changes.

## Known Issues
- Large log files may take significant time to parse

- Some MAVLink message types may not be fully supported

- XML export of array fields may require manual field name cleanup

## Support
For support or feature requests, please open an issue in the GitHub repository.
