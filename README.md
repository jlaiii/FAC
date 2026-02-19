# FAC (Find And Click)

FAC is a professional-grade, GUI-based automation tool designed to detect specific visual elements on a screen and interact with them automatically. Built with Python, it utilizes computer vision to identify targets and execute precise actions while maintaining user workflow.

## Features

- Dynamic Region Selection: Integrated screen-cropping tool to define click targets in real-time.
- Intelligent Persistence: Automatically saves target images and configuration settings for immediate use upon restart.
- Non-Intrusive Operation: Optional feature to restore mouse position instantly after a click is performed.
- Customizable Sensitivity: Adjustable confidence thresholds to ensure accurate matching across different environments.
- Versatile Timing: Scan delays ranging from milliseconds to minutes to suit various automation needs.
- Auto-Start Capability: Optional setting to begin the automation loop immediately after a target is defined.
- Stealth Mode: Designed to run without a background console window when saved as a .pyw file.

## Requirements

The application manages its own dependencies. Upon first run, it will verify and install the following:
- CustomTkinter (Modern UI)
- PyAutoGUI (Input Automation)
- OpenCV-Python (Computer Vision)
- Keyboard (Hotkey Management)
- Pillow (Image Processing)
- NumPy (Data Processing)

## Installation

1. Ensure Python 3.x is installed on your system.
2. Download the FAC.py script to a dedicated folder.
3. Run the script using the command:
   python FAC.py
4. To run without a background console, rename the file to FAC.pyw or use PyInstaller with the --noconsole flag.

## Usage

1. Launch the application.
2. Click on "SET TARGET AREA". The screen will dim, allowing you to drag a selection box around the button or area you wish to automate.
3. Once the target is set, the status will update to "IDLE".
4. Adjust Confidence Level and Scan Delay in the Settings menu if necessary.
5. Click "START BOT" to begin the automation.
6. Press the "ESC" key at any time to stop the automation loop.

## Configuration

Settings are stored locally in fac_settings.json. This includes:
- Confidence: The accuracy required to trigger a click (default 80%).
- Scan Delay: The frequency at which the software checks the screen.
- Restore Mouse: Whether the cursor should return to its original position after clicking.
- Auto-start: Automatically begins scanning after a new target area is captured.

## Technical Details

The core logic utilizes the CV2 matchTemplate function with the TM_CCOEFF_NORMED method. This allows for high-speed, grayscale-normalized matching that is resistant to minor lighting or rendering variations.

## License

This project is intended for personal use and automation efficiency. Use responsibly in accordance with the terms of service of any third-party software being interacted with.
