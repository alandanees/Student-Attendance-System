import tkinter as tk
from tkinter import ttk, messagebox
from Logic import (Student, add_student, load_students, record_attendance, 
                   check_duplicate_attendance, get_student_modules, reset_attendance_file, 
                   ATTENDANCE_FILE)
import matplotlib.pyplot as plt
import pandas as pd
import csv
import os


def plot_attendance(module):
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
    except FileNotFoundError:
        messagebox.showerror("Error", "No attendance data found.")
        return
    except pd.errors.ParserError as e:
        messagebox.showerror("Error", f"Corrupted data in attendance.csv.\n\nPlease check the file for:\n- Extra commas in data\n- Inconsistent number of columns\n\nError details: {str(e)[:100]}")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Error reading attendance file: {str(e)}")
        return

    module_df = df[(df['Module'] == module) & (df['Status'] == "Present")]
    if module_df.empty:
        messagebox.showinfo("Info", "No attendance records for this module.")
        return

    attendance_count = module_df.groupby('LectureNumber')['StudentID'].count()

    plt.plot(attendance_count.index, attendance_count.values, marker='o', linestyle='-', color='blue', markersize=8, linewidth=2)
    plt.xlabel("Lecture Number")
    plt.ylabel("Number of Students Present")
    plt.title(f"Attendance for {module}")
    plt.grid(True, alpha=0.3)
    
    # Set x-axis to display only integers
    plt.xticks(range(int(attendance_count.index.min()), int(attendance_count.index.max()) + 1))
    
    plt.show()
    
    
class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance System")
        self.root.geometry("650x520")

        self.tabControl = ttk.Notebook(root)

        self.tab_add = ttk.Frame(self.tabControl)
        self.tab_attendance = ttk.Frame(self.tabControl)
        self.tab_report = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab_add, text='Add Student')
        self.tabControl.add(self.tab_attendance, text='Record Attendance')
        self.tabControl.add(self.tab_report, text='Attendance Report')
        self.tabControl.pack(expand=1, fill="both")

        self.create_add_tab()
        self.create_attendance_tab()
        self.create_report_tab()

    # --------------- Add Student Tab ---------------
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
        self.dept_entry = tk.Entry(self.tab_add)
        self.dept_entry.grid(row=3, column=1)

        tk.Label(self.tab_add, text="Date of Birth (YYYY-MM-DD):").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.dob_entry = tk.Entry(self.tab_add)
        self.dob_entry.grid(row=4, column=1)

        tk.Label(self.tab_add, text="Modules (comma-separated):").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.modules_entry = tk.Entry(self.tab_add, width=30)
        self.modules_entry.grid(row=5, column=1)

        tk.Button(self.tab_add, text="Add Student", command=self.add_student_gui).grid(row=6, column=0, columnspan=2, pady=20)

    def add_student_gui(self):
        # Get and clean module input
        modules_input = self.modules_entry.get().strip()
        # Convert comma-separated to semicolon-separated for CSV safety
        modules_cleaned = ';'.join([m.strip() for m in modules_input.split(',') if m.strip()])
        
        student = Student(
            self.id_entry.get().strip(),
            self.name_entry.get().strip(),
            self.stage_entry.get().strip(),
            self.dept_entry.get().strip(),
            self.dob_entry.get().strip(),
            modules_cleaned
        )

        if add_student(student):
            messagebox.showinfo("Success", f"Student added successfully!\n\nModules saved: {modules_cleaned.replace(';', ', ')}")
            self.id_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.stage_entry.delete(0, tk.END)
            self.dept_entry.delete(0, tk.END)
            self.dob_entry.delete(0, tk.END)
            self.modules_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Duplicate student detected!")

    # --------------- Attendance Tab ---------------
    def create_attendance_tab(self):
        tk.Label(self.tab_attendance, text="Student ID:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.att_id_entry = tk.Entry(self.tab_attendance)
        self.att_id_entry.grid(row=0, column=1)

        tk.Label(self.tab_attendance, text="Module:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.module_entry = tk.Entry(self.tab_attendance)
        self.module_entry.grid(row=1, column=1)

        tk.Label(self.tab_attendance, text="Lecture Number:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.lecture_entry = tk.Entry(self.tab_attendance)
        self.lecture_entry.grid(row=2, column=1)

        tk.Button(self.tab_attendance, text="Record Attendance", command=self.record_attendance_gui).grid(row=3, column=0, columnspan=2, pady=20)

    def record_attendance_gui(self):
        student_id = self.att_id_entry.get()
        module = self.module_entry.get()
        lecture_number = self.lecture_entry.get()

        if not student_id or not module or not lecture_number:
            messagebox.showerror("Error", "All fields are required!")
            return

        students = load_students()
        
        # Handle both empty list and check for student ID
        if not students:
            messagebox.showerror("Error", "No students found! Please add students first.")
            return
        
        # Safe check for student ID with error handling
        try:
            student_ids = [s.get('ID', '') for s in students]
            if student_id not in student_ids:
                messagebox.showerror("Error", "Student ID not found!")
                return
        except (KeyError, TypeError) as e:
            messagebox.showerror("Error", f"Data format error. Please check students.csv file.\nError: {e}")
            return

        # Get student's modules
        student_modules = get_student_modules(student_id)
        if student_modules is None:
            messagebox.showerror("Error", "Could not retrieve student modules!")
            return
        
        # Check if student has any modules enrolled
        if not student_modules or student_modules.strip() == '':
            messagebox.showerror("Error", f"Student {student_id} has no modules enrolled!\n\nPlease update the student record with modules first.")
            return
        
        # Parse modules - support both semicolon and comma separated
        if ';' in student_modules:
            enrolled_modules = [m.strip() for m in student_modules.split(';') if m.strip()]
        else:
            enrolled_modules = [m.strip() for m in student_modules.split(',') if m.strip()]
        
        if not enrolled_modules:
            messagebox.showerror("Error", f"Student {student_id} has no valid modules enrolled!")
            return
            
        if module not in enrolled_modules:
            messagebox.showerror("Error", f"Module '{module}' not found in student's enrolled modules!\n\nEnrolled modules:\n" + '\n'.join(f"• {m}" for m in enrolled_modules))
            return

        # Check for duplicate attendance
        if check_duplicate_attendance(student_id, module, lecture_number):
            messagebox.showwarning("Duplicate", f"Attendance already recorded for Student {student_id} in {module}, Lecture {lecture_number}!")
            return

        if not record_attendance(student_id, module, lecture_number):
            messagebox.showerror("Error", "Could not record attendance. Please close attendance.csv if it's open in another program.")
            return
            
        messagebox.showinfo("Success", "Attendance recorded successfully!")

        self.att_id_entry.delete(0, tk.END)
        self.module_entry.delete(0, tk.END)
        self.lecture_entry.delete(0, tk.END)

    # --------------- Attendance Report Tab ---------------
    def create_report_tab(self):
        tk.Label(self.tab_report, text="Module:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.report_module_entry = tk.Entry(self.tab_report)
        self.report_module_entry.grid(row=0, column=1)

        tk.Button(self.tab_report, text="Show Attendance Graph", command=self.plot_report_gui).grid(row=1, column=0, columnspan=2, pady=20)
        
        # Add reset attendance button
        tk.Button(self.tab_report, text="Reset All Attendance Records", command=self.reset_attendance_gui, bg='#FF6B6B', fg='white').grid(row=2, column=0, columnspan=2, pady=10)

    def reset_attendance_gui(self):
        """Reset all attendance records"""
        response = messagebox.askyesno(
            "Confirm Reset", 
            "⚠️ WARNING ⚠️\n\nThis will permanently delete ALL attendance records!\n\nThe file structure will be preserved (headers only).\n\nAre you absolutely sure?"
        )
        if not response:
            return
        
        # Double confirmation
        response2 = messagebox.askyesno(
            "Final Confirmation",
            "This action CANNOT be undone!\n\nClick YES to permanently delete all attendance records."
        )
        if not response2:
            return
        
        if reset_attendance_file():
            messagebox.showinfo("Success", "All attendance records have been deleted!\n\nThe file is now reset with headers only.")
        else:
            messagebox.showerror("Error", "Could not reset attendance file. Please make sure it's not open in another program.")

    def plot_report_gui(self):
        module = self.report_module_entry.get()
        if not module:
            messagebox.showerror("Error", "Module field is required!")
            return
        plot_attendance(module)