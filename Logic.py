import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# CSV Files
STUDENTS_FILE = "students.csv"
ATTENDANCE_FILE = "attendance.csv"
MODULES_FILE = "modules.csv"

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
                # Clean up keys and values - remove extra spaces
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                students.append(cleaned_row)
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
    
    for s in students:
        if s.get('ID') == student_id:
            modules = s.get('Modules', '')
            # Remove quotes if they exist
            modules = modules.strip('"').strip("'").strip()
            return modules
    
    return None

def get_all_modules():
    """Get a unique list of all modules from modules.csv"""
    modules = []
    try:
        with open(MODULES_FILE, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try different possible column names (case-insensitive)
                code = row.get('Code', row.get('code', row.get('CODE', ''))).strip()
                module = row.get('Module', row.get('module', row.get('MODULE', ''))).strip()
                department = row.get('Department', row.get('department', row.get('DEPARTMENT', ''))).strip()
                
                if code:  # Use code as the identifier
                    modules.append({
                        'code': code,
                        'module': module,
                        'department': department
                    })
            
    except FileNotFoundError:
        print("modules.csv not found")
    except Exception as e:
        print(f"Error reading modules.csv: {e}")
    
    return modules

def get_modules_by_department(department):
    """Get modules filtered by department"""
    all_modules = get_all_modules()
    if not department:
        return all_modules
    
    filtered = [m for m in all_modules if normalize_module_name(m['department']) == normalize_module_name(department)]
    return filtered

def get_all_departments():
    """Get unique list of departments from modules.csv"""
    modules = get_all_modules()
    departments = set()
    for m in modules:
        if m['department']:
            departments.add(m['department'])
    return sorted(list(departments))

def normalize_module_name(module):
    """Normalize module name for comparison (lowercase, strip spaces)"""
    if not module:
        return ""
    return str(module).strip().lower()

def validate_module_exists(module_code):
    """Check if module code exists in modules.csv (case-insensitive)
    Returns the properly cased module code if found, None otherwise"""
    all_modules = get_all_modules()
    normalized_input = normalize_module_name(module_code)
    
    for m in all_modules:
        # Compare the module CODE, not the entire dict
        if normalize_module_name(m['code']) == normalized_input:
            return m['code']  # Return the properly cased code
    return None

def load_modules():
    """Load all modules with full details"""
    modules = []
    try:
        with open(MODULES_FILE, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up keys and values
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                modules.append(cleaned_row)
    except FileNotFoundError:
        pass
    return modules

def initialize_modules_file():
    """Create modules.csv with proper headers if it doesn't exist"""
    try:
        with open(MODULES_FILE, 'x', newline='', encoding='utf-8') as f:
            fieldnames = ['Code', 'Module', 'Department']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return True
    except FileExistsError:
        return True
    except Exception as e:
        print(f"Error creating modules file: {e}")
        return False

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

def remove_attendance(student_id, module, lecture_number):
    """Remove a specific attendance record"""
    try:
        # Read all attendance records
        records = []
        with open(ATTENDANCE_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Keep all records except the one we want to remove
                if not (row.get('StudentID') == student_id and 
                       row.get('Module') == module and 
                       row.get('LectureNumber') == str(lecture_number)):
                    records.append(row)
        
        # Write back all records except the removed one
        with open(ATTENDANCE_FILE, 'w', newline='') as f:
            fieldnames = ["StudentID", "Module", "LectureNumber", "Date", "Status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error removing attendance: {e}")
        return False