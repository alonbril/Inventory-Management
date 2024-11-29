from cryptography.fernet import Fernet
import base64
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class KeyGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("License Key Generator")
        self.root.geometry("800x600")

        # Initialize encryption key
        self.secret_key = b'jJzteGTIlciymjoiAm-0oyJUrgAIT5gDesSq351l-1I='
        self.history_file = 'key_history.json'
        self.key_history = self.load_history()

        # Define license durations (days)
        self.durations = {
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180,
            "12 Months": 365,
            "Lifetime": -1
        }

        self.create_widgets()
        self.center_window()
        self.update_history_display()

        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View Full Key", command=self.view_full_key)
        self.context_menu.add_command(label="Copy Key", command=self.copy_selected_key)

    def create_widgets(self):
        # Left panel
        left_panel = ttk.Frame(self.root)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Company Name
        ttk.Label(left_panel, text="Company Name:").pack(pady=5)
        self.company_entry = ttk.Entry(left_panel, width=40)
        self.company_entry.pack(pady=5)

        # License Duration
        ttk.Label(left_panel, text="License Duration:").pack(pady=5)
        self.duration_var = tk.StringVar(value="1 Month")
        duration_dropdown = ttk.Combobox(
            left_panel,
            textvariable=self.duration_var,
            values=list(self.durations.keys()),
            state="readonly",
            width=37
        )
        duration_dropdown.pack(pady=5)

        # Generate Button
        ttk.Button(left_panel, text="Generate Key", command=self.generate_key).pack(pady=20)

        # Result field
        ttk.Label(left_panel, text="Generated Key:").pack(pady=5)
        self.result_text = tk.Text(left_panel, height=3, width=40)
        self.result_text.pack(pady=5)

        # Copy button
        ttk.Button(left_panel, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(pady=10)

        # Right panel (History)
        right_panel = ttk.Frame(self.root)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(right_panel, text="Key History", font=('Arial', 12, 'bold')).pack(pady=10)

        # Treeview for history
        columns = ('Date', 'Company', 'Duration', 'Expiry', 'Key')
        self.history_tree = ttk.Treeview(right_panel, columns=columns, show='headings')

        # Configure columns
        self.history_tree.heading('Date', text='Generated')
        self.history_tree.heading('Company', text='Company')
        self.history_tree.heading('Duration', text='Duration')
        self.history_tree.heading('Expiry', text='Expires')
        self.history_tree.heading('Key', text='License Key')

        self.history_tree.column('Date', width=100)
        self.history_tree.column('Company', width=120)
        self.history_tree.column('Duration', width=80)
        self.history_tree.column('Expiry', width=100)
        self.history_tree.column('Key', width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        # Bind events
        self.history_tree.bind("<Double-1>", lambda e: self.view_full_key())
        self.history_tree.bind("<Button-3>", self.show_context_menu)

        # Pack history widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def generate_key(self):
        try:
            company_name = self.company_entry.get().strip()
            if not company_name:
                messagebox.showerror("Error", "Please enter a company name")
                return

            # Get duration and calculate expiry
            duration_text = self.duration_var.get()
            duration_days = self.durations[duration_text]

            # Generate expiry date
            current_date = datetime.datetime.now()
            if duration_days == -1:
                expiry_date = "Never"
                expiry_timestamp = -1
            else:
                expiry_date = (current_date + datetime.timedelta(days=duration_days)).strftime("%Y-%m-%d")
                expiry_timestamp = int((current_date + datetime.timedelta(days=duration_days)).timestamp())

            # Create license data
            license_data = {
                "company": company_name,
                "created": int(current_date.timestamp()),
                "expires": expiry_timestamp
            }

            # Convert to JSON and encode
            json_data = json.dumps(license_data)
            data_bytes = json_data.encode()

            # Encrypt
            fernet = Fernet(self.secret_key)
            encrypted_data = fernet.encrypt(data_bytes)
            serial_key = base64.urlsafe_b64encode(encrypted_data).decode()

            # Update UI
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, serial_key)

            # Add to history
            self.add_to_history(company_name, serial_key, duration_text, expiry_date)

        except Exception as e:
            messagebox.showerror("Error", f"Error generating key: {str(e)}")

    def add_to_history(self, company_name, serial_key, duration, expiry_date):
        entry = {
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'company': company_name,
            'duration': duration,
            'expiry_date': expiry_date,
            'key': serial_key
        }

        self.key_history.append(entry)
        self.save_history()
        self.update_history_display()

    def view_full_key(self):
        selected_items = self.history_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a key from the history")
            return

        item = selected_items[0]
        values = self.history_tree.item(item)['values']
        date, company, duration, expiry, key = values

        # Create details window
        key_window = tk.Toplevel(self.root)
        key_window.title("License Key Details")
        key_window.geometry("500x350")
        self.center_window_on_parent(key_window)

        # Add details
        ttk.Label(key_window, text="Key Details", font=('Arial', 12, 'bold')).pack(pady=10)

        details_frame = ttk.Frame(key_window)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        ttk.Label(details_frame, text=f"Company: {company}").pack(anchor='w', pady=5)
        ttk.Label(details_frame, text=f"Generated: {date}").pack(anchor='w', pady=5)
        ttk.Label(details_frame, text=f"Duration: {duration}").pack(anchor='w', pady=5)
        ttk.Label(details_frame, text=f"Expires: {expiry}").pack(anchor='w', pady=5)

        ttk.Label(details_frame, text="License Key:").pack(anchor='w', pady=5)
        key_text = tk.Text(details_frame, height=4, wrap=tk.WORD)
        key_text.insert('1.0', key)
        key_text.config(state='disabled')
        key_text.pack(fill=tk.X, pady=5)

        ttk.Button(key_window, text="Copy Key",
                   command=lambda: self.copy_key_to_clipboard(key)).pack(pady=10)

    def center_window_on_parent(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def update_history_display(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for entry in reversed(self.key_history):
            self.history_tree.insert('', 'end', values=(
                entry['date'],
                entry['company'],
                entry['duration'],
                entry['expiry_date'],
                entry['key']
            ))

    def show_context_menu(self, event):
        try:
            item = self.history_tree.identify_row(event.y)
            if item:
                self.history_tree.selection_set(item)
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selected_key(self):
        selected_items = self.history_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a key from the history")
            return

        item = selected_items[0]
        key = self.history_tree.item(item)['values'][4]
        self.copy_key_to_clipboard(key)

    def copy_key_to_clipboard(self, key):
        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        messagebox.showinfo("Success", "Key copied to clipboard!")

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
        return []

    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.key_history, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving history: {str(e)}")

    def copy_to_clipboard(self):
        serial_key = self.result_text.get(1.0, tk.END).strip()
        if serial_key:
            self.copy_key_to_clipboard(serial_key)

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