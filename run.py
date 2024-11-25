import tkinter as tk
from tkinter import messagebox, simpledialog
from license_validator import LicenseValidator
import sys
import webbrowser
from threading import Thread
from app import app
import time
import socket


def get_local_ip():
    """Get local machine IP with improved fallback options"""
    try:
        # First attempt: Get IP by connecting to public DNS
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        try:
            # Second attempt: Get hostname-based IP
            host_name = socket.gethostname()
            local_ip = socket.gethostbyname(host_name)
            return local_ip
        except:
            # Final fallback: Use localhost
            return "127.0.0.1"


def find_available_port(start_port=5000, max_attempts=100):
    """Find first available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None


def is_port_available(port):
    """Check if port is available with improved error handling"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except OSError:
        result = False
    finally:
        sock.close()
    return result


def wait_for_flask(port):
    """Wait for Flask to be ready with timeout"""
    start_time = time.time()
    timeout = 30  # 30 seconds timeout

    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return True
            time.sleep(0.1)
        except:
            time.sleep(0.1)
    return False


def validate_license():
    validator = LicenseValidator()

    if validator._check_stored_license():
        return True

    root = tk.Tk()
    root.withdraw()

    company_name = simpledialog.askstring("License Activation", "Enter Company Name:")
    if not company_name:
        return False

    serial_key = simpledialog.askstring("License Activation", "Enter Serial Key:")
    if not serial_key:
        return False

    if validator.validate_key(serial_key, company_name):
        messagebox.showinfo("Success", "License activated successfully!")
        return True
    else:
        messagebox.showerror("Error", "Invalid license key!")
        return False


def start_flask(port):
    try:
        app.run(host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"Error starting Flask: {e}")
        sys.exit(1)


def open_browser(ip, port):
    if wait_for_flask(port):
        try:
            webbrowser.open(f'http://{ip}:{port}')
        except Exception as e:
            print(f"Error opening browser: {e}")
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Manual Access Required",
                                f"Please open your browser and go to:\nhttp://{ip}:{port}")
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "Failed to start the application. Please try again.")
        sys.exit(1)


def show_loading_window(ip, port):
    loading_window = tk.Tk()
    loading_window.title("Application Startup")
    loading_window.geometry("400x200")

    # Center the window
    window_width = 400
    window_height = 200
    screen_width = loading_window.winfo_screenwidth()
    screen_height = loading_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Loading message
    label = tk.Label(loading_window,
                     text="Starting application...\nPlease wait.",
                     pady=20,
                     font=("Arial", 12))
    label.pack()

    # IP Address display
    ip_text = f"Server Address:\nLocal: http://localhost:{port}\nNetwork: http://{ip}:{port}"
    ip_label = tk.Label(loading_window,
                        text=ip_text,
                        pady=10,
                        font=("Arial", 10))
    ip_label.pack()

    # Add copy button
    def copy_to_clipboard():
        loading_window.clipboard_clear()
        loading_window.clipboard_append(f"http://{ip}:{port}")
        loading_window.update()

    copy_button = tk.Button(loading_window,
                            text="Copy Address",
                            command=copy_to_clipboard)
    copy_button.pack(pady=10)

    return loading_window


def main():
    if not validate_license():
        sys.exit()

    # Find available port
    port = find_available_port()
    if port is None:
        messagebox.showerror("Error", "No available ports found. Please check your system.")
        sys.exit(1)

    # Get IP address
    ip = get_local_ip()

    # Show loading window
    loading_window = show_loading_window(ip, port)

    # Start Flask in a separate thread
    flask_thread = Thread(target=start_flask, args=(port,))
    flask_thread.daemon = True
    flask_thread.start()

    # Start browser opening in another thread
    browser_thread = Thread(target=open_browser, args=(ip, port))
    browser_thread.daemon = True
    browser_thread.start()

    # Update loading window
    def check_server():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                loading_window.destroy()
            else:
                loading_window.after(100, check_server)
        except:
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