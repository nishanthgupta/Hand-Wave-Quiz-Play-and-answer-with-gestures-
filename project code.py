import cv2
import numpy as np
import mediapipe as mp
import time
import tkinter as tk
from tkinter import messagebox

# Initialize MediaPipeN
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(model_complexity=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
face_detection = mp_face.FaceDetection(min_detection_confidence=0.8)

# Global variables
user_name = ""
roll_number = ""
current_question = 0
score = 0
quiz_running = True
selected_option = -1
last_selection_time = 0

# Questions dataset
questions = [
    {"question": "Which keyword is used to create a class in Python?", "options": ["class", "define", "type", "struct"], "answer": 0},
    {"question": "What is the output of: bool('False')?", "options": ["False", "True", "None", "Error"], "answer": 1},
    {"question": "Which function is used to get the type of a variable?", "options": ["typeof()", "type()", "getType()", "varType()"], "answer": 1},
    {"question": "Which one is a Python immutable data type?", "options": ["list", "dict", "set", "tuple"], "answer": 3},
    {"question": "What does the 'break' keyword do in loops?", "options": ["Skips next line", "Stops the loop", "Repeats loop", "Breaks variable"], "answer": 1},
    {"question": "Which module in Python is used for regular expressions?", "options": ["regex", "re", "pyregex", "pattern"], "answer": 1},
    {"question": "Which method is used to add an item to a list?", "options": ["add()", "insert()", "append()", "push()"], "answer": 2},
    {"question": "What does the 'is' operator check in Python?", "options": ["Value equality", "Type equality", "Object identity", "None"], "answer": 2},
    {"question": "Which keyword is used to handle exceptions?", "options": ["exception", "try", "raise", "catch"], "answer": 1},
    {"question": "What will '5 // 2' return?", "options": ["2", "2.5", "2.0", "3"], "answer": 0}
]

# Login Page
def login_page():
    login_window = tk.Tk()
    login_window.title("User Login")
    login_window.geometry("600x400")
    login_window.configure(bg="#d1c4e9")
    login_window.resizable(False, False)

    tk.Label(login_window, text="Quiz Game Login", font=("Arial", 20, "bold"), bg="#d1c4e9").pack(pady=20)
    tk.Label(login_window, text="Enter Name:", font=("Arial", 14), bg="#d1c4e9").pack()
    name_entry = tk.Entry(login_window, font=("Arial", 14), width=30)
    name_entry.pack(pady=10)
    tk.Label(login_window, text="Enter Roll Number:", font=("Arial", 14), bg="#d1c4e9").pack()
    roll_entry = tk.Entry(login_window, font=("Arial", 14), width=30)
    roll_entry.pack(pady=10)

    def validate_login():
        global user_name, roll_number
        user_name = name_entry.get().strip()
        roll_number = roll_entry.get().strip()
        if any(char.isdigit() for char in user_name) or not roll_number.isdigit():
            messagebox.showerror("Invalid Input", "Please enter valid name and roll number.")
        else:
            login_window.destroy()

    tk.Button(login_window, text="Start Quiz", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", command=validate_login).pack(pady=20)
    login_window.mainloop()

login_page()

# Quiz settings
width, height = 1920, 1080
option_height = 140
option_spacing = 160
smoothing_factor = 0.7
prev_x, prev_y = 0, 0
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

cv2.namedWindow("Quiz Game", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Quiz Game", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

def draw_ui(frame, question, options, selected_option):
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = 2.0
    thickness = 4
    text_color = (0, 0, 0)

    (w, h), _ = cv2.getTextSize(question, font, text_size, thickness)
    x = (frame.shape[1] - w) // 2
    y = 100
    max_width = frame.shape[1] - 40

    words = question.split()
    line = ''
    y_offset = y
    for word in words:
        test_line = line + ' ' + word if line else word
        (test_w, _), _ = cv2.getTextSize(test_line, font, text_size, thickness)
        if test_w <= max_width:
            line = test_line
        else:
            cv2.putText(frame, line, (x, y_offset), font, text_size, text_color, thickness)
            y_offset += h + 10
            line = word
    cv2.putText(frame, line, (x, y_offset), font, text_size, text_color, thickness)

    option_boxes = []
    for i, option in enumerate(options):
        y_pos = 250 + (i * option_spacing)
        x1 = width // 6
        x2 = width * 5 // 6
        option_box = (x1, y_pos, x2, y_pos + option_height)
        option_boxes.append(option_box)
        color = (200, 200, 200) if selected_option != i else (0, 255, 0)
        cv2.rectangle(frame, (x1, y_pos), (x2, y_pos + option_height), color, -1)
        text_size_opt = cv2.getTextSize(option, font, 2.0, 4)[0]
        x_text = (width - text_size_opt[0]) // 2
        cv2.putText(frame, option, (x_text, y_pos + 90), font, 2.0, (0, 0, 0), 4)
    return option_boxes

def check_selection(x, y, option_boxes):
    for idx, (x1, y1, x2, y2) in enumerate(option_boxes):
        if x1 < x < x2 and y1 < y < y2:
            return idx
    return -1

# Main loop
while cap.isOpened() and quiz_running:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (width, height))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_results = face_detection.process(rgb_frame)

    if not face_results.detections:
        cv2.putText(frame, "Face not detected!", (600, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
        cv2.imshow("Quiz Game", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    results = hands.process(rgb_frame)
    if current_question < len(questions):
        option_boxes = draw_ui(frame, questions[current_question]["question"], questions[current_question]["options"], selected_option)
    else:
        cap.release()
        cv2.destroyAllWindows()
        score_window = tk.Tk()
        score_window.title("Quiz Score")
        score_window.geometry("400x300")
        score_window.configure(bg="#e3f2fd")
        tk.Label(score_window, text=f"Quiz Over!\nName: {user_name}\nRoll No: {roll_number}\nScore: {score}/{len(questions)}", font=("Arial", 16, "bold"), bg="#e3f2fd").pack(pady=40)
        tk.Button(score_window, text="Exit", font=("Arial", 14, "bold"), bg="#FF5722", fg="white", command=score_window.destroy).pack(pady=20)
        score_window.mainloop()
        break

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x, y = int(index_tip.x * width), int(index_tip.y * height)
            x = int(prev_x * smoothing_factor + x * (1 - smoothing_factor))
            y = int(prev_y * smoothing_factor + y * (1 - smoothing_factor))
            prev_x, prev_y = x, y
            cv2.circle(frame, (x, y), 20, (0, 0, 255), -1)
            current_selection = check_selection(x, y, option_boxes)
            if current_selection != -1:
                if current_selection != selected_option:
                    selected_option = current_selection
                    last_selection_time = time.time()
                elif time.time() - last_selection_time > 2:
                    if selected_option == questions[current_question]["answer"]:
                        score += 1
                    time.sleep(1)
                    current_question += 1
                    selected_option = -1

    cv2.imshow("Quiz Game", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
