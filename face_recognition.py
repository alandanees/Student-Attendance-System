"""
Face recognition module for Student Attendance System
Handles face detection, data collection, model training, and recognition
"""

import os
import cv2
import numpy as np
import time
from typing import List, Tuple, Optional
import traceback

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
TRAINER_FILE = os.path.join(BASE_DIR, 'trainer.yml')
HAAR_CASCADE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
CAPTURE_COUNT = 30
CAMERA_ID = 0


def ensure_dirs():
    """Ensure required directories exist."""
    os.makedirs(DATASET_DIR, exist_ok=True)


def get_cascade_classifier():
    """Get Haar Cascade face detector."""
    return cv2.CascadeClassifier(HAAR_CASCADE)


def create_recognizer():
    """
    Create and return LBPH face recognizer.
    Raises RuntimeError if recognizer is not available.
    """
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        return recognizer
    except Exception:
        try:
            recognizer = cv2.face.LBPHFaceRecognizer.create()
            return recognizer
        except Exception as e:
            raise RuntimeError(
                'LBPH recognizer not available. Install opencv-contrib-python.'
            ) from e


# ==================== Face Capture ====================

def capture_student_faces(student_code: str, name: str, callback=None) -> Tuple[bool, str, int]:
    """
    Capture face images for a student using webcam.
    
    Args:
        student_code: Unique student identifier
        name: Student name
        callback: Optional function to call with each frame (for GUI preview)
    
    Returns:
        (success: bool, message: str, count: int)
    """
    ensure_dirs()
    student_dir = os.path.join(DATASET_DIR, student_code)
    os.makedirs(student_dir, exist_ok=True)

    cam = cv2.VideoCapture(CAMERA_ID)
    if not cam.isOpened():
        return False, "Failed to access camera", 0

    detector = get_cascade_classifier()
    count = 0
    start_time = time.time()
    timeout = 300  # 5 minutes

    try:
        while True:
            ret, img = cam.read()
            if not ret:
                return False, "Failed to read from camera", count

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

            # Process detected faces
            for (x, y, w, h) in faces:
                count += 1
                face_img = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_img, (200, 200))
                
                # Save face image
                file_path = os.path.join(student_dir, f"{student_code}_{count}.jpg")
                cv2.imwrite(file_path, face_resized)
                
                # Draw rectangle and text
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(img, f"Captured: {count}/{CAPTURE_COUNT}", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Display instructions
            cv2.putText(img, f"Capturing for {name} - Press ESC to abort", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Callback for GUI preview
            if callback:
                callback(img)

            # Check for exit conditions
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                return False, "Capture aborted by user", count
            
            if count >= CAPTURE_COUNT:
                return True, f"Successfully captured {count} images", count

            # Timeout safety
            if time.time() - start_time > timeout:
                return False, "Face capture timed out", count

    except Exception as e:
        traceback.print_exc()
        return False, f"Capture failed: {str(e)}", count
    finally:
        cam.release()
        cv2.destroyAllWindows()


# ==================== Training ====================

def get_images_and_labels(get_student_func, dataset_path: str = DATASET_DIR) -> Tuple[List, List]:
    """
    Load face images and corresponding labels from dataset directory.
    
    Args:
        get_student_func: Function that takes student_code and returns student ID
        dataset_path: Path to dataset directory
    
    Returns:
        (face_samples: List[np.ndarray], ids: List[int])
    """
    image_paths = []
    for root, dirs, files in os.walk(dataset_path):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_paths.append(os.path.join(root, f))

    face_samples = []
    ids = []
    detector = get_cascade_classifier()

    for image_path in image_paths:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        # Detect and crop face to consistent size
        faces = detector.detectMultiScale(img, scaleFactor=1.1, minNeighbors=4)
        if len(faces) == 0:
            # If no face found, use whole image
            face_img = cv2.resize(img, (200, 200))
        else:
            (x, y, w, h) = faces[0]
            face_img = cv2.resize(img[y:y+h, x:x+w], (200, 200))

        # Extract student code from filename
        filename = os.path.basename(image_path)
        student_code = filename.split('_')[0]
        
        # Get student ID using provided function
        student = get_student_func(student_code)
        if student:
            face_samples.append(face_img)
            ids.append(student[0])  # student[0] is the ID

    return face_samples, ids


def train_model(get_student_func) -> Tuple[bool, str, Optional[object]]:
    """
    Train the face recognition model.
    
    Args:
        get_student_func: Function to get student info by code
    
    Returns:
        (success: bool, message: str, recognizer: Optional[object])
    """
    try:
        recognizer = create_recognizer()
        faces, ids = get_images_and_labels(get_student_func)
        
        if len(faces) == 0:
            return False, "No training data found. Register students first.", None

        # Convert to numpy arrays
        faces_np = [np.array(f, dtype=np.uint8) for f in faces]
        recognizer.train(faces_np, np.array(ids))
        recognizer.write(TRAINER_FILE)
        
        return True, f"Model trained successfully with {len(faces)} samples", recognizer
    
    except Exception as e:
        traceback.print_exc()
        return False, f"Training failed: {str(e)}", None


def load_trained_model() -> Tuple[bool, str, Optional[object]]:
    """
    Load a previously trained model.
    
    Returns:
        (success: bool, message: str, recognizer: Optional[object])
    """
    if not os.path.exists(TRAINER_FILE):
        return False, "No trained model found. Train the model first.", None
    
    try:
        recognizer = create_recognizer()
        recognizer.read(TRAINER_FILE)
        return True, "Model loaded successfully", recognizer
    except Exception as e:
        return False, f"Failed to load model: {str(e)}", None


# ==================== Recognition ====================

def recognize_faces(recognizer, frame: np.ndarray, 
                   confidence_threshold: int = 100) -> List[Tuple[int, int, int, int, int, int]]:
    """
    Detect and recognize faces in a frame.
    
    Args:
        recognizer: Trained face recognizer
        frame: BGR image frame
        confidence_threshold: Maximum confidence value to accept recognition
    
    Returns:
        List of (x, y, w, h, student_id, confidence) for each face
    """
    detector = get_cascade_classifier()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    
    results = []
    for (x, y, w, h) in faces:
        face_img = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_img, (200, 200))
        
        try:
            student_id, confidence = recognizer.predict(face_resized)
            if confidence < confidence_threshold:
                results.append((x, y, w, h, student_id, int(confidence)))
            else:
                results.append((x, y, w, h, None, int(confidence)))
        except Exception:
            results.append((x, y, w, h, None, 999))
    
    return results


def draw_recognition_results(frame: np.ndarray, results: List[Tuple], 
                            student_info_func) -> np.ndarray:
    """
    Draw recognition results on frame.
    
    Args:
        frame: BGR image frame
        results: List of recognition results from recognize_faces()
        student_info_func: Function that takes student_id and returns student info dict
    
    Returns:
        Frame with annotations
    """
    for (x, y, w, h, student_id, confidence) in results:
        if student_id:
            info = student_info_func(student_id)
            if info:
                label = f"{info['name']} ({confidence})"
                color = (0, 255, 0)  # Green for recognized
            else:
                label = 'Unknown'
                color = (0, 0, 255)  # Red
        else:
            label = 'Unknown'
            color = (0, 0, 255)
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, label, (x, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame


# ==================== Analytics ====================

def show_attendance_plot(get_attendance_data_func, get_total_students_func):
    """
    Display attendance analytics plot.
    
    Args:
        get_attendance_data_func: Function that returns attendance by date
        get_total_students_func: Function that returns total student count
    """
    try:
        import matplotlib.pyplot as plt
        has_matplotlib = True
    except ImportError:
        has_matplotlib = False

    data = get_attendance_data_func()
    if not data:
        print("No attendance data available to plot.")
        return

    dates = [row[0] for row in data]
    counts = [row[1] for row in data]
    total_students = get_total_students_func()

    if not has_matplotlib:
        # Console output if matplotlib not available
        print('\n' + '='*60)
        print('ATTENDANCE STATISTICS')
        print('='*60)
        print(f'Total Registered Students: {total_students}')
        print(f'Total Lectures/Days Recorded: {len(dates)}')
        print(f'Average Attendance: {sum(counts)/len(counts):.1f} students')
        print(f'Highest Attendance: {max(counts)} students on {dates[counts.index(max(counts))]}')
        print(f'Lowest Attendance: {min(counts)} students on {dates[counts.index(min(counts))]}')
        print('='*60 + '\n')
        return

    # Plot with matplotlib
    plt.figure(figsize=(12, 6))
    
    # Scatter plot with points only (no lines)
    plt.scatter(range(len(dates)), counts, s=150, color='#3498db', 
               alpha=0.7, edgecolors='#2c3e50', linewidth=2, zorder=3)

    # Add value labels on top of each point
    for i, val in enumerate(counts):
        plt.text(i, val + max(counts) * 0.02, str(val), 
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add total students reference line
    if total_students > 0:
        plt.axhline(y=total_students, color='#2ecc71', linestyle='--', 
                   linewidth=2, label=f'Total Registered: {total_students}')

    # Styling
    plt.xlabel('Date / Lecture Session', fontsize=11, fontweight='bold')
    plt.ylabel('Number of Students Present', fontsize=11, fontweight='bold')
    plt.title('Student Attendance per Lecture/Day', fontsize=14, fontweight='bold', pad=20)
    
    # Set y-axis limits with padding
    max_val = max(max(counts), total_students) if total_students > 0 else max(counts)
    plt.ylim(0, max_val * 1.15)
    
    # X-axis labels
    step = max(1, len(dates) // 15)
    plt.xticks(range(0, len(dates), step), 
              [dates[i] for i in range(0, len(dates), step)], 
              rotation=45, ha='right')
    
    # Grid for better readability
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='best', fontsize=10)
    plt.tight_layout()
    plt.show()