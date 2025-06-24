import PyInstaller.__main__
import os

# Path to your main script, icon, and tesseract installer
SCRIPT = 'ocr_gui.py'
ICON = 'needyamin.ico'  # Make sure this file exists in the same directory
TESSERACT_INSTALLER = 'tesseract-ocr-w64-setup-5.4.0.20240606.exe'  # Make sure this file exists in the same directory

# IMPORTANT: In your ocr_gui.py, use resource_path to load the icon for PyInstaller compatibility.
# Example:
# import sys, os
# def resource_path(relative_path):
#     try:
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)
# ...
# self.root.iconbitmap(resource_path('needyamin.ico'))

# Build command for PyInstaller
PyInstaller.__main__.run([
    SCRIPT,
    '--onefile',
    '--windowed',
    f'--icon={ICON}',
    '--name', 'ANSNEW_TECH_Image2Text',
    '--clean',
    '--add-data', f'{ICON};.',
    '--add-data', f'{TESSERACT_INSTALLER};.',
])

print('Build complete. Check the dist/ folder for your .exe file.') 