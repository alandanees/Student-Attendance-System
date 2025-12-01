"""
GUI module for Student Attendance System
Main application interface using Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import csv
import threading
import time
import traceback

# Import our custom modules
import Logic as db
import face_recognition as fr


class AttendanceSystemGUI:
    """Main GUI application for the attendance system."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance System")
        self.root.geometry("950x620")
        self.root.configure(bg='#f0f0f0')

        # Initialize directories and database
        fr.ensure_dirs()
        db.init_db()
        db.upgrade_db()

        # Camera and recognition state
        self.camera_active = False
        self.camera_thread = None
        self.recognizer = None

        # Create UI
        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Top Title Bar
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="Student Attendance System",
            font=('Arial', 20, 'bold'),
            bg='#2c3e50',
            fg='white'
        ).pack(pady=12)

        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # LEFT SIDE - Button Panel
        self._create_button_panel(main_frame)

        # RIGHT SIDE - Display Panel
        self._create_display_panel(main_frame)

    def _create_button_panel(self, parent):
        """Create left side button panel."""
        left_frame = tk.Frame(parent, bg='#f0f0f0')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        button_style = {
            'font': ('Arial', 11),
            'width': 25,
            'height': 2,
            'bg': '#3498db',
            'fg': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }

        # Register Student
        tk.Button(
            left_frame,
            text="Register New Student",
            command=self.register_student_window,
            **button_style
        ).pack(pady=5)

        # Train Model
        train_style = button_style.copy()
        train_style['bg'] = '#2ecc71'
        tk.Button(
            left_frame,
            text="Train Model",
            command=self.train_model,
            **train_style
        ).pack(pady=5)

        # Start Recognition
        recog_style = button_style.copy()
        recog_style['bg'] = '#e74c3c'
        tk.Button(
            left_frame,
            text="Start Attendance (Camera)",
            command=self.toggle_recognition,
            **recog_style
        ).pack(pady=5)

        # Manual Attendance
        manual_style = button_style.copy()
        manual_style['bg'] = '#f39c12'
        tk.Button(
            left_frame,
            text="Manual Attendance",
            command=self.manual_attendance_window,
            **manual_style
        ).pack(pady=5)

        # View Students
        view_style = button_style.copy()
        view_style['bg'] = '#9b59b6'
        tk.Button(
            left_frame,
            text="View Students",
            command=self.view_students,
            **view_style
        ).pack(pady=5)

        # View Attendance
        attendance_style = button_style.copy()
        attendance_style['bg'] = '#1abc9c'
        tk.Button(
            left_frame,
            text="View Attendance",
            command=self.view_attendance,
            **attendance_style
        ).pack(pady=5)

        # Export CSV
        export_style = button_style.copy()
        export_style['bg'] = '#34495e'
        tk.Button(
            left_frame,
            text="Export to CSV",
            command=self.export_csv,
            **export_style
        ).pack(pady=5)

        # Analytics
        analytics_style = button_style.copy()
        analytics_style['bg'] = '#e67e22'
        tk.Button(
            left_frame,
            text="View Analytics (Console)",
            command=self.show_analytics,
            **analytics_style
        ).pack(pady=5)

    def _create_display_panel(self, parent):
        """Create right side display panel."""
        right_frame = tk.Frame(parent, bg='white', relief=tk.RIDGE, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Welcome label
        self.display_label = tk.Label(
            right_frame,
            text="Welcome to Attendance System\n\nSelect an option to begin",
            font=('Arial', 14),
            bg='white',
            fg='#7f8c8d',
            justify=tk.CENTER
        )
        self.display_label.pack(fill=tk.BOTH, expand=True)

        # Preview frame (hidden initially)
        self.preview_frame = tk.Frame(right_frame, bg='black')
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_frame.pack_forget()

        self.preview_label = tk.Label(self.preview_frame, bg='black')
        self.preview_label.pack(fill=tk.BOTH, expand=True)

    # ==================== Registration ====================

    def register_student_window(self):
        """Open student registration window."""
        window = tk.Toplevel(self.root)
        window.title("Register Student")
        window.geometry("420x280")
        window.configure(bg='#ecf0f1')

        tk.Label(
            window,
            text="Register New Student",
            font=('Arial', 16, 'bold'),
            bg='#ecf0f1'
        ).pack(pady=16)

        frame = tk.Frame(window, bg='#ecf0f1')
        frame.pack(pady=10)

        tk.Label(
            frame,
            text="Student Code:",
            font=('Arial', 11),
            bg='#ecf0f1'
        ).grid(row=0, column=0, sticky='e', padx=5, pady=10)
        
        code_entry = tk.Entry(frame, font=('Arial', 11), width=22)
        code_entry.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(
            frame,
            text="Student Name:",
            font=('Arial', 11),
            bg='#ecf0f1'
        ).grid(row=1, column=0, sticky='e', padx=5, pady=10)
        
        name_entry = tk.Entry(frame, font=('Arial', 11), width=22)
        name_entry.grid(row=1, column=1, padx=5, pady=10)

        def start_capture():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            if not code or not name:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            # Add student to database
            success, message = db.add_student(code, name)
            if not success:
                messagebox.showerror("Error", message)
                return
            
            window.destroy()
            # Start face capture in thread
            threading.Thread(
                target=self.capture_faces,
                args=(code, name),
                daemon=True
            ).start()

        tk.Button(
            window,
            text="Start Face Capture",
            command=start_capture,
            font=('Arial', 12),
            bg='#3498db',
            fg='white',
            width=20,
            height=2
        ).pack(pady=14)

    def capture_faces(self, student_code, name):
        """Capture face images for a student."""
        # Show preview frame
        self.display_label.pack_forget()
        self.preview_frame.pack(fill=tk.BOTH, expand=True)

        def preview_callback(frame):
            self._update_preview(frame)

        success, message, count = fr.capture_student_faces(
            student_code, 
            name, 
            callback=preview_callback
        )

        # Hide preview frame
        self.preview_frame.pack_forget()
        self.display_label.pack(fill=tk.BOTH, expand=True)

        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showwarning("Warning", message)

    # ==================== Training ====================

    def train_model(self):
        """Train the face recognition model."""
        def train():
            try:
                success, message, recognizer = fr.train_model(db.get_student_by_code)
                if success:
                    self.recognizer = recognizer
                    messagebox.showinfo("Success", message)
                else:
                    messagebox.showerror("Error", message)
            except Exception as e:
                traceback.print_exc()
                messagebox.showerror("Error", f"Training failed: {str(e)}")

        threading.Thread(target=train, daemon=True).start()

    # ==================== Recognition ====================

    def toggle_recognition(self):
        """Start or stop face recognition."""
        if self.camera_active:
            self.camera_active = False
            self.preview_frame.pack_forget()
            self.display_label.pack(fill=tk.BOTH, expand=True)
        else:
            # Load model
            success, message, recognizer = fr.load_trained_model()
            if not success:
                messagebox.showerror("Error", message)
                return
            
            self.recognizer = recognizer
            self.camera_active = True
            
            # Show preview
            self.display_label.pack_forget()
            self.preview_frame.pack(fill=tk.BOTH, expand=True)
            
            # Start recognition thread
            self.camera_thread = threading.Thread(
                target=self._camera_loop,
                daemon=True
            )
            self.camera_thread.start()

    def _camera_loop(self):
        """Main camera loop for face recognition."""
        cam = cv2.VideoCapture(fr.CAMERA_ID)
        if not cam.isOpened():
            messagebox.showerror("Error", "Failed to open camera")
            self.camera_active = False
            return

        students = db.get_students_dict()

        try:
            while self.camera_active:
                ret, frame = cam.read()
                if not ret:
                    break

                # Recognize faces
                results = fr.recognize_faces(self.recognizer, frame)

                # Mark attendance and draw results
                for (x, y, w, h, student_id, confidence) in results:
                    if student_id and student_id in students:
                        info = students[student_id]
                        success, msg = db.mark_attendance(
                            student_id,
                            info['code'],
                            info['name'],
                            'recognition'
                        )
                        color = (0, 255, 0) if success else (0, 165, 255)
                        label = f"{info['name']} ({confidence})"
                    else:
                        color = (0, 0, 255)
                        label = 'Unknown'

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(frame, label, (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                cv2.putText(frame, "Press Q to stop", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                self._update_preview(frame)
                time.sleep(0.03)

        except Exception as e:
            traceback.print_exc()
        finally:
            cam.release()
            cv2.destroyAllWindows()
            self.camera_active = False

    def _update_preview(self, bgr_image):
        """Update preview label with OpenCV image."""
        try:
            rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(rgb)
            img_pil = img_pil.resize((640, 360))
            imgtk = ImageTk.PhotoImage(image=img_pil)
            self.preview_label.imgtk = imgtk
            self.preview_label.configure(image=imgtk)
        except Exception:
            pass

    # ==================== Manual Attendance ====================

    def manual_attendance_window(self):
        """Open manual attendance entry window."""
        window = tk.Toplevel(self.root)
        window.title("Manual Attendance")
        window.geometry("420x220")
        window.configure(bg='#ecf0f1')

        tk.Label(
            window,
            text="Manual Attendance Entry",
            font=('Arial', 16, 'bold'),
            bg='#ecf0f1'
        ).pack(pady=16)

        frame = tk.Frame(window, bg='#ecf0f1')
        frame.pack(pady=10)

        tk.Label(
            frame,
            text="Student Code:",
            font=('Arial', 11),
            bg='#ecf0f1'
        ).grid(row=0, column=0, sticky='e', padx=5, pady=10)
        
        code_entry = tk.Entry(frame, font=('Arial', 11), width=24)
        code_entry.grid(row=0, column=1, padx=5, pady=10)

        def submit():
            code = code_entry.get().strip()
            if not code:
                messagebox.showerror("Error", "Please enter student code")
                return

            student = db.get_student_by_code(code)
            if not student:
                messagebox.showerror("Error", "Student code not found")
                return

            student_id, student_code, name = student
            success, msg = db.mark_attendance(student_id, student_code, name, 'manual')
            
            if success:
                messagebox.showinfo("Success", msg)
                window.destroy()
            else:
                messagebox.showwarning("Warning", msg)

        tk.Button(
            window,
            text="Mark Attendance",
            command=submit,
            font=('Arial', 12),
            bg='#f39c12',
            fg='white',
            width=22,
            height=2
        ).pack(pady=12)

    # ==================== Views ====================

    def view_students(self):
        """Display all registered students."""
        window = tk.Toplevel(self.root)
        window.title("View Students")
        window.geometry("700x420")

        frame = tk.Frame(window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            frame,
            columns=('Code', 'Name', 'Registered'),
            show='headings'
        )
        tree.heading('Code', text='Student Code')
        tree.heading('Name', text='Name')
        tree.heading('Registered', text='Registered Date')

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        students = db.get_all_students()
        for row in students:
            tree.insert('', tk.END, values=row)

    def view_attendance(self):
        """Display attendance records."""
        window = tk.Toplevel(self.root)
        window.title("View Attendance")
        window.geometry("900x420")

        frame = tk.Frame(window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            frame,
            columns=('Code', 'Name', 'Date', 'Time', 'Method'),
            show='headings'
        )
        tree.heading('Code', text='Student Code')
        tree.heading('Name', text='Name')
        tree.heading('Date', text='Date')
        tree.heading('Time', text='Time')
        tree.heading('Method', text='Method')

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        attendance = db.get_all_attendance()
        for row in attendance:
            tree.insert('', tk.END, values=row)

    # ==================== Export & Analytics ====================

    def export_csv(self):
        """Export attendance records to CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filename:
            return

        attendance = db.get_all_attendance()

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Student Code', 'Name', 'Date', 'Time', 'Method'])
            writer.writerows(attendance)

        messagebox.showinfo("Success", f"Exported {len(attendance)} records to {filename}")

    def show_analytics(self):
        """Display analytics plot."""
        fr.show_attendance_plot(db.get_attendance_by_date, db.get_total_students)


# ==================== Main Entry Point ====================

def main():
    """Main entry point for the application."""
    fr.ensure_dirs()
    db.init_db()
    db.upgrade_db()

    root = tk.Tk()
    app = AttendanceSystemGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()