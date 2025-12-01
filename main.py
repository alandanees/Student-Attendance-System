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

# At the top of your main file or wherever you're running it
from AttendanceGUI import AttendanceSystemGUI

# Then in your main function
def main():
    fr.ensure_dirs()
    db.init_db()
    db.upgrade_db()

    root = tk.Tk()
    app = AttendanceSystemGUI(root)  # Class name
    root.mainloop()


if __name__ == '__main__':
    main()