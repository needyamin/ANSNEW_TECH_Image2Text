import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
import pytesseract
import os
import requests
import zipfile
from io import BytesIO
import threading
import subprocess
import sys
from tkinter import ttk
import json
import time
from pathlib import Path

DEST_DIR = "Tesseract-Portable"
GITHUB_API = "https://api.github.com/repos/UB-Mannheim/tesseract/releases"
FALLBACK_TESSERACT_ZIP = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-5.3.3-portable.zip"
INSTALLER_URL = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
INSTALLER_NAME = "tesseract-ocr-w64-setup-5.4.0.20240606.exe"
TESSDATA_DIR = os.path.join(os.environ.get('ProgramFiles', ''), 'Tesseract-OCR', 'tessdata')
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/{lang_code}.traineddata"
LANGS = {
    'English': 'eng',
    'Bangla': 'ben',
    'Hindi': 'hin',
    'Arabic': 'ara',
    'Chinese (Simplified)': 'chi_sim',
    'French': 'fra',
    'German': 'deu',
    'Spanish': 'spa',
    # Add more as needed
}

# --- Update Check Constants ---
REPO_OWNER = "needyamin"
REPO_NAME = "ANSNEW_TECH_Image2Text"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
CURRENT_VERSION = "1.0.0"  # Update as needed
UPDATE_CHECK_FILE = Path(".update_check")

def compare_versions(v1, v2):
    def parse(v):
        return [int(x) for x in v.split('.') if x.isdigit()]
    return parse(v1) > parse(v2)

def debug_update_check(log):
    """Debug function to check update system status"""
    try:
        log("\n=== DEBUG: Update System Status ===")
        log(f"\nRepository Configuration:")
        log(f"Owner: {REPO_OWNER}")
        log(f"Name: {REPO_NAME}")
        log(f"API URL: {GITHUB_API_URL}")
        log(f"Current Version: {CURRENT_VERSION}")
        log(f"\nUpdate Check File Status:")
        if UPDATE_CHECK_FILE.exists():
            with open(UPDATE_CHECK_FILE, 'r') as f:
                last_check = float(f.read().strip())
                time_since_last_check = time.time() - last_check
                log(f"Last check: {time.ctime(last_check)}")
                log(f"Time since last check: {time_since_last_check/3600:.2f} hours")
        else:
            log("Update check file not found")
        log(f"\nTesting GitHub API Connection:")
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'ANSNEW-Tech-Text2Image'
            }
            response = requests.get(GITHUB_API_URL, headers=headers)
            log(f"API Response Status: {response.status_code}")
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release.get('tag_name', '').lstrip('v')
                log(f"Latest Release: {latest_version}")
                log(f"Release Details: {json.dumps(latest_release, indent=2)}")
            else:
                log(f"API Error: {response.text}")
        except Exception as e:
            log(f"API Connection Error: {str(e)}")
        log(f"\nTesting Version Comparison:")
        test_versions = [
            ("1.0.15", "1.0.14")
        ]
        for v1, v2 in test_versions:
            result = compare_versions(v1, v2)
            log(f"Compare {v1} > {v2}: {result}")
        log("\n=== DEBUG COMPLETED ===\n")
    except Exception as e:
        log(f"Debug Error: {str(e)}")

# --- Tesseract Portable Auto-Update Functions ---
def get_latest_portable_url():
    resp = requests.get(GITHUB_API)
    resp.raise_for_status()
    releases = resp.json()
    for release in releases[:10]:  # Check the latest 10 releases
        for asset in release.get("assets", []):
            name = asset["name"].lower()
            if name.endswith(".zip") and "portable" in name:
                return asset["browser_download_url"]
    # Fallback to a known working version
    return FALLBACK_TESSERACT_ZIP

def download_and_extract_tesseract(url, dest_dir, log_callback=None):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    chunks = []
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            chunks.append(chunk)
            downloaded += len(chunk)
            if log_callback:
                percent = int(downloaded * 100 / total) if total else 0
                log_callback(f"Downloading Tesseract: {percent}% ({downloaded // 1024} KB)")
    if log_callback:
        log_callback("Extracting Tesseract...")
    with zipfile.ZipFile(BytesIO(b''.join(chunks))) as z:
        z.extractall(dest_dir)
    for root, dirs, files in os.walk(dest_dir):
        if "tesseract.exe" in files:
            exe_path = os.path.join(root, "tesseract.exe")
            if log_callback:
                log_callback(f"Tesseract ready at: {exe_path}")
            return exe_path
    raise Exception("tesseract.exe not found after extraction.")

def run_installer_with_elevation(installer_path, log_callback=None):
    try:
        # Use ShellExecuteEx to run installer as admin (silent mode)
        import ctypes
        params = f'/S'
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", installer_path, params, None, 1)
        if int(ret) <= 32:
            raise Exception(f"Failed to launch installer with elevation, code: {ret}")
        if log_callback:
            log_callback("Tesseract installer launched with admin rights (silent mode). Waiting for install to finish...")
        # Wait for tesseract.exe to appear (polling)
        import time
        for _ in range(60):  # Wait up to 60 seconds
            exe_path = find_installed_tesseract()
            if exe_path:
                return exe_path
            time.sleep(2)
        raise Exception("Tesseract installation did not complete in time.")
    except Exception as e:
        if log_callback:
            log_callback(f"Installer error: {e}")
        raise

def find_installed_tesseract():
    possible_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join('C:\\', 'Program Files', 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join('C:\\', 'Program Files (x86)', 'Tesseract-OCR', 'tesseract.exe'),
    ]
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    return None

def ensure_tesseract_exists(log_callback=None):
    # Check if tesseract.exe exists in PATH or common locations
    exe_path = find_installed_tesseract()
    if exe_path:
        if log_callback:
            log_callback(f"Tesseract found at: {exe_path}")
        return exe_path
    # Download installer if not present
    if log_callback:
        log_callback("Tesseract not found. Downloading installer...")
    installer_path = os.path.join(os.getcwd(), INSTALLER_NAME)
    if not os.path.isfile(installer_path):
        download_tesseract_installer(INSTALLER_URL, installer_path, log_callback)
    # Run installer with elevation and silent mode
    exe_path = run_installer_with_elevation(installer_path, log_callback)
    if exe_path:
        if log_callback:
            log_callback(f"Tesseract installed at: {exe_path}")
        return exe_path
    raise Exception("Tesseract installation failed.")

# --- Tesseract Installer Download Function ---
def download_tesseract_installer(url, dest_path, log_callback=None):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if log_callback:
                    percent = int(downloaded * 100 / total) if total else 0
                    log_callback(f"Downloading Tesseract installer: {percent}% ({downloaded // 1024} KB)")
    if log_callback:
        log_callback(f"Installer downloaded to: {dest_path}")
    return dest_path

# --- Language Data Download ---
def ensure_langdata(lang_code, log_callback=None, use_best=False):
    if not os.path.isdir(TESSDATA_DIR):
        return  # Tesseract not installed yet
    traineddata_path = os.path.join(TESSDATA_DIR, f"{lang_code}.traineddata")
    if os.path.isfile(traineddata_path):
        if log_callback:
            size = os.path.getsize(traineddata_path)
            log_callback(f"Language data '{lang_code}' present ({size // 1024} KB)")
        return
    url = TESSDATA_BEST_URL.format(lang_code=lang_code) if use_best else f"https://github.com/tesseract-ocr/tessdata/raw/main/{lang_code}.traineddata"
    try:
        if log_callback:
            log_callback(f"Downloading language data: {lang_code} ({'best' if use_best else 'standard'})...")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(traineddata_path, 'wb') as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        if log_callback:
            log_callback(f"Language data '{lang_code}' installed.")
    except Exception as e:
        if log_callback:
            log_callback(f"Failed to download language data '{lang_code}': {e}")

# --- Image Preprocessing ---
def preprocess_image(image_path):
    from PIL import ImageOps
    img = Image.open(image_path)
    img = img.convert('L')  # Grayscale
    img = ImageOps.autocontrast(img)
    # Simple thresholding
    img = img.point(lambda x: 0 if x < 128 else 255, '1')
    return img

# --- GUI ---
class LogPopup:
    def __init__(self, parent, title="Log Output"):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("540x340")
        self.top.transient(parent)
        self.top.grab_set()
        self.text = scrolledtext.ScrolledText(self.top, wrap=tk.WORD, width=64, height=16, state='disabled', font=('Consolas', 10))
        self.text.pack(padx=8, pady=8, fill='both', expand=True)
        self.close_btn = ttk.Button(self.top, text="Close", command=self.top.destroy)
        self.close_btn.pack(pady=(0, 8))
        self.top.protocol("WM_DELETE_WINDOW", self.top.destroy)
        self.top.focus_set()
        self.top.lift()
    def log(self, message):
        self.text.config(state='normal')
        self.text.insert(tk.END, message + '\n')
        self.text.see(tk.END)
        self.text.config(state='disabled')

# Add resource_path for PyInstaller compatibility
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ANSNEW TECH Image2Text V1.00")
        self.root.geometry("700x600")
        self.root.configure(bg="#f4f6fb")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Segoe UI', 11), padding=4, background="#4f8cff", foreground="#fff")
        style.configure('TLabel', font=('Segoe UI', 11), background="#f4f6fb")
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), background="#f4f6fb", foreground="#2d3a4b")
        style.configure('Section.TLabelframe', background="#e9eef6", borderwidth=1, relief='groove')
        style.configure('Section.TLabelframe.Label', font=('Segoe UI', 11, 'bold'), background="#e9eef6", foreground="#2d3a4b")

        self.tesseract_path = tk.StringVar()
        self.image_path = None
        self.selected_lang = tk.StringVar(value='English')
        self.use_best_model = tk.BooleanVar(value=True)

        # --- Title ---
        ttk.Label(root, text="ANSNEW TECH Image2Text V1.00", style='Header.TLabel').pack(pady=(8, 0))
        ttk.Label(root, text="Image to Text Converter", style='TLabel').pack(pady=(0, 8))

        # --- File Selection Section ---
        file_frame = ttk.Labelframe(root, text="Image Selection", style='Section.TLabelframe')
        file_frame.pack(fill='x', padx=18, pady=6)
        ttk.Button(file_frame, text="Choose Image", command=self.choose_file, width=16).pack(side=tk.LEFT, padx=6, pady=6)
        self.file_label = ttk.Label(file_frame, text="No file selected.", style='TLabel')
        self.file_label.pack(side=tk.LEFT, padx=6, pady=6)

        # --- Extract Button ---
        self.extract_btn = ttk.Button(root, text="Extract Text", command=self.extract_text, width=16, style='TButton')
        self.extract_btn.pack(pady=8)

        # --- Text Output Section ---
        output_frame = ttk.Labelframe(root, text="Extracted Text", style='Section.TLabelframe')
        output_frame.pack(fill='both', expand=True, padx=18, pady=6)
        self.text_area = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=70, height=14, font=("Nirmala UI", 11), bg="#fafdff", fg="#222")
        self.text_area.pack(padx=6, pady=6, fill='both', expand=True)

        # --- Log Area ---
        self.log_area = None  # No log area in main window

        # Modal for Tesseract setup
        self.setup_modal = None
        self.setup_modal_log = None

        # Footer
        footer_frame = tk.Frame(root, bg="#f4f6fb")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 4))
        footer_frame.grid_columnconfigure(0, weight=1)
        footer_frame.grid_columnconfigure(1, weight=0)
        footer_frame.grid_columnconfigure(2, weight=1)
        footer_text1 = tk.Label(footer_frame, text="© 2015-2025 ", font=("Segoe UI", 9), bg="#f4f6fb", fg="#888")
        footer_text1.grid(row=0, column=0, sticky="e")
        link = tk.Label(footer_frame, text="ANSNEW TECH.", font=("Segoe UI", 9, "underline"), fg="#4f8cff", bg="#f4f6fb", cursor="hand2")
        link.grid(row=0, column=1)
        footer_text2 = tk.Label(footer_frame, text=" | All Rights Reserved", font=("Segoe UI", 9), bg="#f4f6fb", fg="#888")
        footer_text2.grid(row=0, column=2, sticky="w")
        def open_link(event):
            import webbrowser
            webbrowser.open_new("https://inside.ansnew.com")
        link.bind("<Button-1>", open_link)

        # Top menubar
        menubar = tk.Menu(root)
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.choose_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        def copy_text():
            text = self.text_area.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        def clear_output():
            self.text_area.delete(1.0, tk.END)
        edit_menu.add_command(label="Copy Text", command=copy_text)
        edit_menu.add_command(label="Clear Output", command=clear_output)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        def show_about():
            tk.messagebox.showinfo("About", "ANSNEW TECH Image2Text V1.00\nDeveloped by ANSNEW TECH.\nhttps://inside.ansnew.com")
        help_menu.add_command(label="About", command=show_about)
        help_menu.add_command(label="Visit Website", command=lambda: open_link(None))
        # Add Submit Issue on GitHub
        def open_github_issues():
            import webbrowser
            webbrowser.open_new("https://github.com/needyamin/ANSNEW_TECH_Image2Text/issues")
        help_menu.add_command(label="Submit Issue on GitHub", command=open_github_issues)
        # Add Debug Update Check menu item
        def run_debug_update():
            popup = LogPopup(self.root, title="Update Check Log")
            def log_fn(msg):
                popup.log(msg)
            threading.Thread(target=lambda: debug_update_check(log_fn), daemon=True).start()
        help_menu.add_command(label="Update Check", command=run_debug_update)
        # Add Check for Updates menu item
        def run_check_for_update():
            popup = LogPopup(self.root, title="Check for Updates Log")
            def log_fn(msg):
                popup.log(msg)
            threading.Thread(target=lambda: check_for_update(log=log_fn, show_popup=True, parent=self.root), daemon=True).start()
        help_menu.add_command(label="Check for Updates", command=run_check_for_update)
        menubar.add_cascade(label="Help", menu=help_menu)
        root.config(menu=menubar)

        # Auto-detect or download Tesseract on startup
        self.root.after(100, self.auto_setup_tesseract)

        # Place an icon file named 'needyamin.ico' in the same directory as this script for the application icon.
        try:
            self.root.iconbitmap(resource_path('needyamin.ico'))
        except Exception:
            pass  # If icon not found, ignore

    def show_setup_modal(self):
        if self.setup_modal:
            return
        self.setup_modal = tk.Toplevel(self.root)
        self.setup_modal.title("Tesseract Setup Required")
        self.setup_modal.geometry("420x220")
        self.setup_modal.grab_set()
        self.setup_modal.transient(self.root)
        self.setup_modal.resizable(False, False)
        self.setup_modal.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        ttk.Label(self.setup_modal, text="Tesseract is not detected!", style='Header.TLabel').pack(pady=(10, 0))
        ttk.Label(self.setup_modal, text="The app will now download and install Tesseract automatically.\nPlease wait...", style='TLabel').pack(pady=(0, 6))
        self.setup_modal_log = scrolledtext.ScrolledText(self.setup_modal, wrap=tk.WORD, width=48, height=7, state='disabled', fg='#555', bg="#f7f9fa", font=('Consolas', 9))
        self.setup_modal_log.pack(padx=6, pady=6, fill='both', expand=True)
        self.extract_btn.config(state='disabled')
        self.root.attributes('-disabled', True)

    def hide_setup_modal(self):
        if self.setup_modal:
            self.setup_modal.destroy()
            self.setup_modal = None
            self.setup_modal_log = None
            self.extract_btn.config(state='normal')
            self.root.attributes('-disabled', False)

    def log(self, message):
        # Only log to modal if open and not destroyed
        pass
        # Also log to modal if open and not destroyed
        try:
            if self.setup_modal_log and self.setup_modal_log.winfo_exists():
                self.setup_modal_log.config(state='normal')
                self.setup_modal_log.insert(tk.END, message + '\n')
                self.setup_modal_log.see(tk.END)
                self.setup_modal_log.config(state='disabled')
                if self.setup_modal and self.setup_modal.winfo_exists():
                    self.setup_modal.update_idletasks()
        except Exception:
            pass

    def auto_setup_tesseract(self):
        def task():
            try:
                exe_path = ensure_tesseract_exists(self.log)
                self.tesseract_path.set(exe_path)
                self.log("Tesseract is ready.")
                self.hide_setup_modal()
            except Exception as e:
                self.log(f"Tesseract setup failed: {e}")
                # Retry after a short delay
                self.root.after(3000, self.auto_setup_tesseract)
        # Show the setup modal immediately before starting the thread
        self.show_setup_modal()
        threading.Thread(target=task, daemon=True).start()

    def choose_file(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select Image File", filetypes=filetypes)
        if path:
            self.image_path = path
            self.file_label.config(text=os.path.basename(path))
            self.log(f"Selected image: {path}")
        else:
            self.file_label.config(text="No file selected.")

    def extract_text(self):
        if not self.image_path:
            messagebox.showwarning("No File", "Please select an image file first.")
            return
        # Show loader/feedback
        self.extract_btn.config(state='disabled', text='Extracting...')
        self.root.update_idletasks()
        tesseract_cmd = self.tesseract_path.get().strip()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        # Always use English for OCR (or change to another default if needed)
        lang_code = 'eng'
        use_best = False
        ensure_langdata(lang_code, self.log, use_best=use_best)
        traineddata_path = os.path.join(TESSDATA_DIR, f"{lang_code}.traineddata")
        if os.path.isfile(traineddata_path):
            self.log(f"Using language data: {traineddata_path} ({os.path.getsize(traineddata_path)//1024} KB)")
        def ocr_task():
            try:
                img = preprocess_image(self.image_path)
                self.log(f"Running OCR (lang={lang_code})...")
                text = pytesseract.image_to_string(img, lang=lang_code)
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, text)
                self.log("OCR extraction complete.")
                # If no text detected, show popup
                if not text.strip():
                    self.root.after(0, lambda: messagebox.showinfo("No Text Detected", "No text was found in the selected image."))
            except Exception as e:
                self.log(f"Failed to extract text: {e}")
                messagebox.showerror("Error", f"Failed to extract text:\n{e}")
            finally:
                self.extract_btn.config(state='normal', text='Extract Text')
        threading.Thread(target=ocr_task, daemon=True).start()

def check_for_update(log=None, show_popup=True, parent=None):
    """Check for updates and show popup if available."""
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ANSNEW-Tech-Text2Image'
        }
        response = requests.get(GITHUB_API_URL, headers=headers)
        if log:
            log(f"API Response Status: {response.status_code}")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release.get('tag_name', '').lstrip('v')
            release_url = latest_release.get('html_url', 'https://github.com/needyamin/ANSNEW_TECH_Image2Text/releases')
            if compare_versions(latest_version, CURRENT_VERSION):
                if show_popup and parent:
                    def open_release():
                        import webbrowser
                        webbrowser.open_new(release_url)
                    tk.messagebox.showinfo(
                        "Update Available",
                        f"A new version ({latest_version}) is available!\n\nVisit the release page to download the latest version.",
                        parent=parent
                    )
                if log:
                    log(f"Update available: {latest_version}")
                return True
            else:
                if log:
                    log("No update available.")
                return False
        else:
            if log:
                log(f"API Error: {response.text}")
            return False
    except Exception as e:
        if log:
            log(f"Update check error: {str(e)}")
        return False

def main():
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 