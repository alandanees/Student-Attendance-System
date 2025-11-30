import tkinter as tk
from tkinter import ttk, messagebox
from Logic import initialize_modules_file, get_all_departments, get_all_modules, get_modules_by_department

class SessionWindow:
    """Separate window for starting a teaching session"""
    def __init__(self, root):
        self.root = root
        self.root.title("Start Teaching Session")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Session data
        self.selected_department = None
        self.selected_module = None
        self.session_started = False
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.create_widgets()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#2196F3', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame, 
            text="Student Attendance System",
            font=('Arial', 18, 'bold'),
            bg='#2196F3',
            fg='white'
        ).pack(pady=25)
        
        # Main content frame
        content_frame = tk.Frame(self.root, padx=40, pady=30)
        content_frame.pack(fill='both', expand=True)
        
        tk.Label(
            content_frame,
            text="Start Teaching Session",
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Department selection
        tk.Label(
            content_frame,
            text="Select Department:",
            font=('Arial', 11)
        ).grid(row=1, column=0, sticky='w', pady=10)
        
        self.dept_combobox = ttk.Combobox(
            content_frame,
            width=28,
            state='readonly',
            font=('Arial', 10)
        )
        self.dept_combobox.grid(row=1, column=1, pady=10, sticky='ew')
        self.dept_combobox.bind('<<ComboboxSelected>>', self.on_department_selected)
        
        # Module selection
        tk.Label(
            content_frame,
            text="Select Module:",
            font=('Arial', 11)
        ).grid(row=2, column=0, sticky='w', pady=10)
        
        self.module_combobox = ttk.Combobox(
            content_frame,
            width=28,
            state='readonly',
            font=('Arial', 10)
        )
        self.module_combobox.grid(row=2, column=1, pady=10, sticky='ew')
        
        # Button frame
        button_frame = tk.Frame(content_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=30)
        
        tk.Button(
            button_frame,
            text="Start Session",
            command=self.start_session,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=30,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text="Exit",
            command=self.on_closing,
            bg='#f44336',
            fg='white',
            font=('Arial', 12),
            padx=30,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Load departments
        self.load_departments()
        
    def load_departments(self):
        """Load departments into dropdown"""
        departments = get_all_departments()
        if departments:
            self.dept_combobox['values'] = departments
        else:
            messagebox.showerror(
                "Error",
                "No departments found in modules.csv!\n\nPlease create the file with format:\nCode,Module,Department"
            )
            self.root.destroy()

    def on_department_selected(self, event):
        """When department is selected, filter modules"""
        selected_dept = self.dept_combobox.get()
        modules = get_modules_by_department(selected_dept)
        
        if modules:
            # Display as "Code - Module Name"
            module_display = [f"{m['code']} - {m['module']}" for m in modules]
            self.module_combobox['values'] = module_display
            if module_display:
                self.module_combobox.current(0)
        else:
            self.module_combobox['values'] = []
            messagebox.showinfo("Info", f"No modules found for {selected_dept}")

    def start_session(self):
        """Start a teaching session"""
        department = self.dept_combobox.get()
        module_display = self.module_combobox.get()
        
        if not department or not module_display:
            messagebox.showerror("Error", "Please select both department and module!")
            return
        
        # Extract module code from display (before the " - ")
        module_code = module_display.split(' - ')[0]
        
        self.selected_department = department
        self.selected_module = module_code
        self.session_started = True
        
        messagebox.showinfo(
            "Session Started",
            f"Teaching session started!\n\nModule: {module_display}\nDepartment: {department}\n\nOpening main application..."
        )
        
        self.root.destroy()
    
    def on_closing(self):
        """Handle window closing"""
        self.session_started = False
        self.root.destroy()


if __name__ == "__main__":
    # Initialize modules file
    initialize_modules_file()
    
    # Check if modules exist
    departments = get_all_departments()
    if not departments:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Setup Required",
            "No modules found!\n\nPlease create a 'modules.csv' file with columns:\nCode,Module,Department\n\nExample:\nCS101,Programming Basics,Computer Science"
        )
        root.destroy()
        exit()
    
    # Show session window first
    session_root = tk.Tk()
    session_window = SessionWindow(session_root)
    session_root.mainloop()
    
    # After session window closes, check if session was started
    if session_window.session_started:
        # Import here to avoid circular import
        from AttendanceGUI import AttendanceApp
        
        # Start main application with session data
        root = tk.Tk()
        app = AttendanceApp(
            root, 
            session_window.selected_module,
            session_window.selected_department
        )
        root.mainloop()