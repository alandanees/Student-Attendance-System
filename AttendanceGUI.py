import tkinter as tk
from tkinter import ttk, messagebox
from Logic import (Student, add_student, load_students, record_attendance, 
                   check_duplicate_attendance, get_student_modules, reset_attendance_file, 
                   remove_attendance, get_all_modules, normalize_module_name, 
                   validate_module_exists, initialize_modules_file, ATTENDANCE_FILE)
import matplotlib.pyplot as plt
import pandas as pd


def plot_attendance(module):
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
    except FileNotFoundError:
        messagebox.showerror("Error", "No attendance data found.")
        return
    except pd.errors.ParserError as e:
        messagebox.showerror("Error", f"Corrupted data in attendance.csv.\n\nError: {str(e)[:100]}")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Error reading attendance file: {str(e)}")
        return

    module_df = df[(df['Module'] == module) & (df['Status'] == "Present")]
    if module_df.empty:
        messagebox.showinfo("Info", "No attendance records for this module.")
        return

    attendance_count = module_df.groupby('LectureNumber')['StudentID'].count()

    plt.plot(attendance_count.index, attendance_count.values, marker='o', linestyle='-', 
             color='blue', markersize=8, linewidth=2)
    plt.xlabel("Lecture Number")
    plt.ylabel("Number of Students Present")
    plt.title(f"Attendance for {module}")
    plt.grid(True, alpha=0.3)
    plt.xticks(range(int(attendance_count.index.min()), int(attendance_count.index.max()) + 1))
    plt.show()

    
class AttendanceApp:
    def __init__(self, root, selected_module=None, selected_department=None):
        self.root = root
        self.root.title("Student Attendance System")
        self.root.geometry("700x600")

        initialize_modules_file()
        
        # Session data from startup window
        self.selected_department = selected_department
        self.selected_module = selected_module

        self.tabControl = ttk.Notebook(root)

        self.tab_add = ttk.Frame(self.tabControl)
        self.tab_attendance = ttk.Frame(self.tabControl)
        self.tab_remove = ttk.Frame(self.tabControl)
        self.tab_report = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab_add, text='Add Student')
        self.tabControl.add(self.tab_attendance, text='Record Attendance')
        self.tabControl.add(self.tab_remove, text='Remove Attendance')
        self.tabControl.add(self.tab_report, text='Attendance Report')
        self.tabControl.pack(expand=1, fill="both")

        self.create_add_tab()
        self.create_attendance_tab()
        self.create_remove_tab()
        self.create_report_tab()

    def create_add_tab(self):
        tk.Label(self.tab_add, text="Student ID:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.id_entry = tk.Entry(self.tab_add)
        self.id_entry.grid(row=0, column=1)

        tk.Label(self.tab_add, text="Name:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = tk.Entry(self.tab_add)
        self.name_entry.grid(row=1, column=1)

        tk.Label(self.tab_add, text="Stage:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.stage_entry = tk.Entry(self.tab_add)
        self.stage_entry.grid(row=2, column=1)

        tk.Label(self.tab_add, text="Department:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        # Change from Entry to Combobox for department selection
        from Logic import get_all_departments
        self.add_dept_combobox = ttk.Combobox(self.tab_add, width=27, state='readonly')
        self.add_dept_combobox.grid(row=3, column=1, sticky="w")
        departments = get_all_departments()
        if departments:
            self.add_dept_combobox['values'] = departments
        # Bind department selection to update modules
        self.add_dept_combobox.bind('<<ComboboxSelected>>', self.on_add_department_selected)

        tk.Label(self.tab_add, text="Date of Birth (YYYY-MM-DD):").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.dob_entry = tk.Entry(self.tab_add)
        self.dob_entry.grid(row=4, column=1)

        tk.Label(self.tab_add, text="Modules:").grid(row=5, column=0, padx=10, pady=10, sticky="nw")
        
        modules_frame = tk.Frame(self.tab_add)
        modules_frame.grid(row=5, column=1, sticky="w")
        
        scrollbar = tk.Scrollbar(modules_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.modules_listbox = tk.Listbox(modules_frame, selectmode=tk.MULTIPLE, height=5, 
                                          width=30, yscrollcommand=scrollbar.set)
        self.modules_listbox.pack(side=tk.LEFT)
        scrollbar.config(command=self.modules_listbox.yview)
        
        # Initially empty - will be populated when department is selected
        tk.Label(self.tab_add, text="(Select department first)", 
                fg='gray', font=('Arial', 9, 'italic')).grid(row=5, column=2, padx=5, sticky="w")

        tk.Button(self.tab_add, text="Add Student", command=self.add_student_gui).grid(
            row=6, column=0, columnspan=2, pady=20)
        tk.Button(self.tab_add, text="View All Students", command=self.view_students, 
                 bg='lightblue').grid(row=7, column=0, columnspan=2, pady=5)

    def on_add_department_selected(self, event):
        """When department is selected in Add Student tab, filter modules"""
        from Logic import get_modules_by_department
        
        selected_dept = self.add_dept_combobox.get()
        self.modules_listbox.delete(0, tk.END)
        
        if not selected_dept:
            return
        
        modules = get_modules_by_department(selected_dept)
        
        if modules:
            for m in modules:
                display = f"{m['code']} - {m['module']}"
                self.modules_listbox.insert(tk.END, display)
        else:
            messagebox.showinfo("Info", f"No modules found for {selected_dept}")

    def view_students(self):
        students = load_students()
        if not students:
            messagebox.showinfo("Students", "No students found!")
            return
        
        info = "All Students:\n" + "="*50 + "\n\n"
        for s in students:
            info += f"ID: {s.get('ID', 'N/A')}\n"
            info += f"Name: {s.get('Name', 'N/A')}\n"
            info += f"Modules: {s.get('Modules', 'NONE')}\n"
            info += "-"*50 + "\n\n"
        
        window = tk.Toplevel(self.root)
        window.title("All Students")
        window.geometry("500x400")
        
        text = tk.Text(window, wrap=tk.WORD)
        text.pack(expand=True, fill='both', padx=10, pady=10)
        text.insert('1.0', info)
        text.config(state='disabled')

    def add_student_gui(self):
        # Check if department is selected
        if not self.add_dept_combobox.get():
            messagebox.showerror("Error", "Please select a department first!")
            return
            
        selected_indices = self.modules_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select at least one module!")
            return
        
        selected_displays = [self.modules_listbox.get(i) for i in selected_indices]
        selected_codes = [display.split(' - ')[0] for display in selected_displays]
        
        validated_modules = []
        for code in selected_codes:
            validated = validate_module_exists(code)
            if validated:
                validated_modules.append(validated)
            else:
                messagebox.showerror("Error", f"Module '{code}' not found!")
                return
        
        modules_str = ';'.join(validated_modules)
        
        student = Student(
            self.id_entry.get().strip(),
            self.name_entry.get().strip(),
            self.stage_entry.get().strip(),
            self.add_dept_combobox.get().strip(),  # Get from combobox instead of entry
            self.dob_entry.get().strip(),
            modules_str
        )

        if add_student(student):
            messagebox.showinfo("Success", f"Student added!\n\nModules: {', '.join(validated_modules)}")
            self.id_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.stage_entry.delete(0, tk.END)
            self.add_dept_combobox.set('')  # Clear combobox
            self.dob_entry.delete(0, tk.END)
            self.modules_listbox.delete(0, tk.END)  # Clear modules list
        else:
            messagebox.showerror("Error", "Duplicate student detected!")

    def create_attendance_tab(self):
        if self.selected_module and self.selected_department:
            session_text = f"Current Session: {self.selected_module} ({self.selected_department})"
            session_color = 'green'
        else:
            session_text = "No active session"
            session_color = 'red'
            
        self.att_session_label = tk.Label(
            self.tab_attendance, text=session_text,
            font=('Arial', 11, 'bold'), fg=session_color
        )
        self.att_session_label.grid(row=0, column=0, columnspan=2, pady=15)
        
        tk.Label(self.tab_attendance, text="Student ID:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.att_id_entry = tk.Entry(self.tab_attendance)
        self.att_id_entry.grid(row=1, column=1)

        tk.Label(self.tab_attendance, text="Lecture Number:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.lecture_entry = tk.Entry(self.tab_attendance)
        self.lecture_entry.grid(row=2, column=1)

        tk.Button(self.tab_attendance, text="Record Attendance", 
                 command=self.record_attendance_gui).grid(row=3, column=0, columnspan=2, pady=20)

    def record_attendance_gui(self):
        if not self.selected_module or not self.selected_department:
            messagebox.showerror("Error", "No active session! Please restart the application.")
            return
        
        student_id = self.att_id_entry.get().strip()
        lecture_number = self.lecture_entry.get().strip()
        module = self.selected_module

        if not student_id or not lecture_number:
            messagebox.showerror("Error", "Student ID and Lecture Number are required!")
            return

        students = load_students()
        if not students:
            messagebox.showerror("Error", "No students found!")
            return
        
        student_ids = [s.get('ID', '') for s in students]
        if student_id not in student_ids:
            messagebox.showerror("Error", "Student ID not found!")
            return

        student_modules = get_student_modules(student_id)
        if not student_modules or student_modules.strip() == '':
            messagebox.showerror("Error", f"Student {student_id} has no modules enrolled!")
            return
        
        enrolled_modules = [m.strip() for m in student_modules.replace(';', ',').split(',') if m.strip()]
        
        module_match = None
        for enrolled_module in enrolled_modules:
            if normalize_module_name(enrolled_module) == normalize_module_name(module):
                module_match = enrolled_module
                break
        
        if not module_match:
            messagebox.showerror("Error", 
                f"Student {student_id} is not enrolled in {module}!\n\nEnrolled: {', '.join(enrolled_modules)}")
            return

        if check_duplicate_attendance(student_id, module, lecture_number):
            messagebox.showwarning("Duplicate", 
                f"Attendance already recorded for {student_id} in {module}, Lecture {lecture_number}!")
            return

        if not record_attendance(student_id, module, lecture_number):
            messagebox.showerror("Error", "Could not record attendance.")
            return
            
        messagebox.showinfo("Success", 
            f"Attendance recorded!\n\nStudent: {student_id}\nModule: {module}\nLecture: {lecture_number}")

        self.att_id_entry.delete(0, tk.END)
        self.lecture_entry.delete(0, tk.END)
        self.att_id_entry.focus()

    def create_remove_tab(self):
        tk.Label(self.tab_remove, text="Remove Attendance Record", 
                font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        tk.Label(self.tab_remove, text="Student ID:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.remove_id_entry = tk.Entry(self.tab_remove)
        self.remove_id_entry.grid(row=1, column=1)

        tk.Label(self.tab_remove, text="Module:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        remove_module_frame = tk.Frame(self.tab_remove)
        remove_module_frame.grid(row=2, column=1, sticky="w")
        
        self.remove_module_combobox = ttk.Combobox(remove_module_frame, width=27, state='readonly')
        self.remove_module_combobox.pack(side=tk.LEFT)
        
        tk.Button(remove_module_frame, text="↻", command=self.refresh_remove_modules, 
                 width=2).pack(side=tk.LEFT, padx=5)
        
        self.refresh_remove_modules()

        tk.Label(self.tab_remove, text="Lecture Number:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.remove_lecture_entry = tk.Entry(self.tab_remove)
        self.remove_lecture_entry.grid(row=3, column=1)

        tk.Button(self.tab_remove, text="Remove Attendance", command=self.remove_attendance_gui, 
                 bg='#FF6B6B', fg='white').grid(row=4, column=0, columnspan=2, pady=20)
        
        tk.Label(self.tab_remove, text="⚠️ This will permanently delete the attendance record", 
                fg='red', font=('Arial', 9)).grid(row=5, column=0, columnspan=2)

    def refresh_remove_modules(self):
        modules = get_all_modules()
        if modules:
            module_display = [f"{m['code']} - {m['module']}" for m in modules]
            self.remove_module_combobox['values'] = module_display
            if len(module_display) > 0:
                self.remove_module_combobox.current(0)
        else:
            self.remove_module_combobox['values'] = []

    def remove_attendance_gui(self):
        student_id = self.remove_id_entry.get().strip()
        module_display = self.remove_module_combobox.get().strip()
        lecture_number = self.remove_lecture_entry.get().strip()

        if not student_id or not module_display or not lecture_number:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        module = module_display.split(' - ')[0]

        if not check_duplicate_attendance(student_id, module, lecture_number):
            messagebox.showerror("Error", 
                f"No attendance record found for:\n\nStudent: {student_id}\nModule: {module}\nLecture: {lecture_number}")
            return

        response = messagebox.askyesno("Confirm Removal",
            f"Remove this record?\n\nStudent: {student_id}\nModule: {module}\nLecture: {lecture_number}\n\nCannot be undone!")
        
        if not response:
            return

        if remove_attendance(student_id, module, lecture_number):
            messagebox.showinfo("Success", "Attendance record removed!")
            self.remove_id_entry.delete(0, tk.END)
            self.remove_lecture_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Could not remove record.")

    def create_report_tab(self):
        tk.Label(self.tab_report, text="Module:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.report_module_entry = tk.Entry(self.tab_report)
        self.report_module_entry.grid(row=0, column=1)

        tk.Button(self.tab_report, text="Show Attendance Graph", 
                 command=self.plot_report_gui).grid(row=1, column=0, columnspan=2, pady=20)
        
        tk.Button(self.tab_report, text="Reset All Attendance Records", 
                 command=self.reset_attendance_gui, bg='#FF6B6B', fg='white').grid(
                     row=2, column=0, columnspan=2, pady=10)

    def reset_attendance_gui(self):
        response = messagebox.askyesno("Confirm Reset", 
            "⚠️ WARNING ⚠️\n\nDelete ALL attendance records?\n\nCannot be undone!")
        if not response:
            return
        
        response2 = messagebox.askyesno("Final Confirmation",
            "Last chance! Click YES to permanently delete all records.")
        if not response2:
            return
        
        if reset_attendance_file():
            messagebox.showinfo("Success", "All attendance records deleted!")
        else:
            messagebox.showerror("Error", "Could not reset file.")

    def plot_report_gui(self):
        module = self.report_module_entry.get()
        if not module:
            messagebox.showerror("Error", "Module field is required!")
            return
        plot_attendance(module)