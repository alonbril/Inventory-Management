from cryptography.fernet import Fernet
import base64
import datetime
import tkinter as tk
from tkinter import ttk, messagebox


class KeyGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("License Key Generator")
        self.root.geometry("400x300")

        # Use the exact same key as in license_validator.py
        self.secret_key = b'jJzteGTIlciymjoiAm-0oyJUrgAIT5gDesSq351l-1I='

        # Create GUI elements
        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        # Company Name
        tk.Label(self.root, text="Company Name:").pack(pady=10)
        self.company_entry = ttk.Entry(self.root, width=40)
        self.company_entry.pack(pady=5)

        # Generate Button
        ttk.Button(self.root, text="Generate Key",
                   command=self.generate_key).pack(pady=20)

        # Result
        tk.Label(self.root, text="Generated Key:").pack(pady=10)
        self.result_text = tk.Text(self.root, height=3, width=40)
        self.result_text.pack(pady=5)

        # Copy Button
        ttk.Button(self.root, text="Copy to Clipboard",
                   command=self.copy_to_clipboard).pack(pady=10)

    def generate_key(self):
        try:
            company_name = self.company_entry.get().strip()
            if not company_name:
                messagebox.showerror("Error", "Please enter a company name")
                return

            # Generate key using same format as validator expects
            current_date = datetime.datetime.now().strftime("%Y%m")
            data = f"{company_name}:{current_date}".encode()

            # Create Fernet instance
            fernet = Fernet(self.secret_key)

            # Encrypt the data
            encrypted_data = fernet.encrypt(data)

            # Convert to readable format - no padding removal
            serial_key = base64.urlsafe_b64encode(encrypted_data).decode()

            # Display result
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, serial_key)

            # Test validation immediately
            print(f"Generated key: {serial_key}")
            print(f"Original data: {data}")

        except Exception as e:
            messagebox.showerror("Error", f"Error generating key: {str(e)}")

    def copy_to_clipboard(self):
        serial_key = self.result_text.get(1.0, tk.END).strip()
        if serial_key:
            self.root.clipboard_clear()
            self.root.clipboard_append(serial_key)
            messagebox.showinfo("Success", "Key copied to clipboard!")

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyGeneratorApp(root)
    root.mainloop()
