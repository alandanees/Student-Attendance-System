import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# CSV Files
STUDENTS_FILE = "students.csv"
ATTENDANCE_FILE = "attendance.csv"

class Student:
    def __init__(self, student_id, name, stage, department, dob, modules):
        self.student_id = student_id
        self.name = name
        self.stage = stage
        self.department = department
        self.dob = dob
        self.modules = modules
        
    def to_dict(self):
        return {
            "ID": self.student_id,
            "Name": self.name,
            "Stage": self.stage,
            "Department": self.department,
            "DOB": self.dob,
            "Modules": self.modules
        }

#CSV functions 
   
def load_students():
    students = []
    try:
        with open(STUDENTS_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append(row)
    except FileNotFoundError:
        pass
    return students

def add_student(student):
    students = load_students()
    # Check duplicates with safe key access
    for s in students:
        try:
            # Check for duplicate ID
            if s.get('ID') == student.student_id:
                return False
            # Check for duplicate by name, DOB, and department
            if (s.get('Name') == student.name and 
                s.get('DOB') == student.dob and 
                s.get('Department') == student.department):
                return False
        except (KeyError, TypeError):
            continue
    
    # Append student
    with open(STUDENTS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=student.to_dict().keys(), quoting=csv.QUOTE_MINIMAL)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(student.to_dict())
    return True

def record_attendance(student_id, module, lecture_number, status="Present"):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(ATTENDANCE_FILE, 'a', newline='') as f:
                fieldnames = ["StudentID", "Module", "LectureNumber", "Date", "Status"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerow({
                    "StudentID": student_id,
                    "Module": module,
                    "LectureNumber": lecture_number,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Status": status
                })
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5)  # Wait half a second and retry
            else:
                return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

def check_duplicate_attendance(student_id, module, lecture_number):
    """Check if attendance already recorded for this student, module, and lecture"""
    try:
        with open(ATTENDANCE_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get('StudentID') == student_id and 
                    row.get('Module') == module and 
                    row.get('LectureNumber') == str(lecture_number)):
                    return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error checking duplicate: {e}")
        return False
    return False

def get_student_modules(student_id):
    """Get the modules for a specific student"""
    students = load_students()
    print(f"DEBUG: Looking for student ID: {student_id}")
    print(f"DEBUG: Total students loaded: {len(students)}")
    
    for s in students:
        print(f"DEBUG: Checking student: {s}")
        if s.get('ID') == student_id:
            modules = s.get('Modules', '')
            # Remove quotes if they exist
            modules = modules.strip('"').strip("'").strip()
            print(f"DEBUG: Found student! Modules value: '{modules}'")
            print(f"DEBUG: Modules type: {type(modules)}")
            return modules
    
    print(f"DEBUG: Student {student_id} not found!")
    return None

def reset_attendance_file():
    """Reset attendance.csv file - remove all data but keep headers"""
    try:
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            fieldnames = ["StudentID", "Module", "LectureNumber", "Date", "Status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return True
    except Exception as e:
        print(f"Error resetting file: {e}")
        return False