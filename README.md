# ANSNEW_TECH_Image2Text

A modern, user-friendly desktop application to extract text from images using Tesseract OCR, with automatic Tesseract setup and update checking.

## Features
- **Image to Text Conversion**: Extracts text from images (PNG, JPG, BMP, TIFF, etc.) using Tesseract OCR.
- **Automatic Tesseract Setup**: Downloads and installs Tesseract OCR if not found on your system.
- **Multi-language Support**: Easily extendable to support multiple OCR languages.
- **Update Checker**: Check for new versions directly from the app.
- **Debug Log Window**: View detailed logs for update checks and debugging.
- **Modern GUI**: Clean, responsive interface built with Tkinter.
- **Easy Issue Reporting**: Submit issues directly to GitHub from the Help menu.

## Installation
1. **Clone or Download** this repository:
   ```sh
   git clone https://github.com/needyamin/ANSNEW_TECH_Image2Text.git
   cd ANSNEW_TECH_Image2Text
   ```
2. **Install Python dependencies**:
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the Application**:
   ```sh
   python ocr_gui.py
   ```
   The app will automatically download and install Tesseract OCR if it is not already installed.

## Usage
- **Open Image**: Use the File menu or the "Choose Image" button to select an image file.
- **Extract Text**: Click "Extract Text" to perform OCR and view the result in the output area.
- **Copy/Clear Output**: Use the Edit menu to copy the extracted text or clear the output area.
- **Update Check**: Use the Help menu > "Update Check" to view a detailed log of the update system.
- **Check for Updates**: Use the Help menu > "Check for Updates" to see if a new version is available (popup shown only if an update exists).
- **Submit Issue on GitHub**: Use the Help menu > "Submit Issue on GitHub" to open the issues page in your browser.

## Screenshots
![Image](https://github.com/user-attachments/assets/24e1c7fb-fffa-4a08-9990-78f0b75f2adf)

## License
This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.

## Links
- [GitHub Repository](https://github.com/needyamin/ANSNEW_TECH_Image2Text)
- [Submit an Issue](https://github.com/needyamin/ANSNEW_TECH_Image2Text/issues)
