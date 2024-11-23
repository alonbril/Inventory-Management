import tkinter as tk
from tkinter import messagebox, simpledialog
from license_validator import LicenseValidator
import sys
import webbrowser
from threading import Thread
from app import app  # Import your Flask app
import time
import socket


def get_local_ip():
    """Get local machine IP"""
    try:
        # Get local machine IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"  # Fallback to localhost if can't get IP


def is_port_available(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = True
    try:
        sock.bind(("0.0.0.0", port))
    except:
        result = False
    sock.close()
    return result


def wait_for_flask():
    """Wait for Flask to be ready"""
    attempts = 0
    while is_port_available(5000) and attempts < 50:  # Wait up to 5 seconds
        time.sleep(0.1)
        attempts += 1
    return not is_port_available(5000)


def validate_license():
    validator = LicenseValidator()

    # Check if license is already validated
    if validator._check_stored_license():
        return True

    # Create root window for dialog boxes
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Get license information
    company_name = simpledialog.askstring("License Activation", "Enter Company Name:")
    if not company_name:
        return False

    serial_key = simpledialog.askstring("License Activation", "Enter Serial Key:")
    if not serial_key:
        return False

    # Validate license
    if validator.validate_key(serial_key, company_name):
        messagebox.showinfo("Success", "License activated successfully!")
        return True
    else:
        messagebox.showerror("Error", "Invalid license key!")
        return False


def start_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True)


def open_browser():
    if wait_for_flask():  # Wait for Flask to be ready
        local_ip = get_local_ip()
        webbrowser.open(f'http://{local_ip}:5000')
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "Failed to start the application. Please try again.")
        sys.exit(1)


def show_loading_window():
    loading_window = tk.Tk()
    loading_window.title("Loading")
    loading_window.geometry("300x150")

    # Center the window
    window_width = 300
    window_height = 150
    screen_width = loading_window.winfo_screenwidth()
    screen_height = loading_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Loading message
    label = tk.Label(loading_window, text="Starting application...\nPlease wait.", pady=20)
    label.pack()

    # IP Address display
    ip_label = tk.Label(loading_window, text=f"Server IP: {get_local_ip()}\nPort: 5000", pady=10)
    ip_label.pack()

    return loading_window


def main():
    if not validate_license():
        sys.exit()

    # Show loading window
    loading_window = show_loading_window()

    # Start Flask in a separate thread
    flask_thread = Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start browser opening in another thread
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Update loading window
    def check_server():
        if not is_port_available(5000):  # Server is running
            loading_window.destroy()
        else:
            loading_window.after(100, check_server)

    loading_window.after(100, check_server)
    loading_window.mainloop()

    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()