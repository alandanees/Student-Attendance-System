# Student Attendance System

A Python-based GUI application for managing student attendance records with visualization capabilities.

## Features

- **Student Management**: Add students with their details (ID, Name, Stage, Department, DOB, Modules)
- **Attendance Recording**: Record student attendance for specific modules and lectures
- **Duplicate Prevention**: Prevents recording duplicate attendance for the same student, module, and lecture
- **Module Validation**: Ensures students can only be marked present for modules they're enrolled in
- **Attendance Visualization**: Generate line graphs showing attendance trends per module
- **Data Reset**: Reset all attendance records while preserving file structure

## Requirements

- Python 3.x
- tkinter (usually comes with Python)
- pandas
- matplotlib

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/student-attendance-system.git
cd student-attendance-system
```

2. Install required packages:
```bash
pip install pandas matplotlib
```

## Usage

Run the application:
```bash
python main.py
```

### Adding Students

1. Go to the "Add Student" tab
2. Fill in all required fields:
   - Student ID
   - Name
   - Stage
   - Department
   - Date of Birth (YYYY-MM-DD format)
   - Modules (comma-separated, e.g., "Python, Network, Database")
3. Click "Add Student"
4. Use "View All Students" button to verify student details

### Recording Attendance

1. Go to the "Record Attendance" tab
2. Enter:
   - Student ID
   - Module name (must match exactly with enrolled modules)
   - Lecture Number
3. Click "Record Attendance"
4. The system will validate:
   - Student exists
   - Module is in student's enrolled modules
   - Attendance hasn't been recorded already for this combination

### Viewing Reports

1. Go to the "Attendance Report" tab
2. Enter the module name
3. Click "Show Attendance Graph"
4. A line graph will display showing the number of students present per lecture

### Resetting Attendance Data

1. Go to the "Attendance Report" tab
2. Click "Reset All Attendance Records" (red button)
3. Confirm twice (this action cannot be undone)

## File Structure

```
student-attendance-system/
│
├── main.py              # Application entry point
├── AttendanceGUI.py     # GUI components and interface
├── Logic.py             # Core business logic and CSV operations
├── students.csv         # Student records (created automatically)
├── attendance.csv       # Attendance records (created automatically)
└── README.md           # This file
```

## CSV File Formats

### students.csv
```csv
ID,Name,Stage,Department,DOB,Modules
B02042205,John Doe,4,Software Engineering,2000-01-15,Python;Network;Database
```

### attendance.csv
```csv
StudentID,Module,LectureNumber,Date,Status
B02042205,Python,1,2024-11-30,Present
```

## Known Issues

- Module names must match exactly (case-sensitive)
- CSV files must be closed in Excel/editors before recording attendance
- Ensure no extra spaces in CSV headers

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## Future Enhancements

- [ ] Export reports to PDF
- [ ] Add absence tracking
- [ ] Implement user authentication
- [ ] Add date range filtering for reports
- [ ] Support for multiple semesters
- [ ] Email notifications for low attendance

## License

This project is open source and available under the MIT License.

## Authors

- Your Name - Initial work

## Acknowledgments

- Built with Python Tkinter
- Visualizations powered by Matplotlib
- Data handling with Pandas