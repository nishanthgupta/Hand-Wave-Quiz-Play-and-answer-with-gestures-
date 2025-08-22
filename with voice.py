import cv2
import numpy as np
import mediapipe as mp
import time
import tkinter as tk
from tkinter import messagebox
import pyttsx3
import random

# Initialize Text-to-Speech engine
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# Initialize MediaPipe Hands and Face Detection
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(model_complexity=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
face_detection = mp_face.FaceDetection(min_detection_confidence=0.8)

# Global variables for quiz
user_name = ""
roll_number = ""
current_question = 0
score = 0
quiz_running = True
selected_option = -1
last_selection_time = 0

# Questions
questions = [
    {"question": "What is the keyword used to define a function in Python?", "options": ["def", "func", "function", "method"], "answer": 0},
    {"question": "Which of these is used to get input from the user in Python?", "options": ["input()", "read()", "scan()", "get()"], "answer": 0},
    {"question": "What will the following Python code print? print(3 * 2 + 1)", "options": ["6", "7", "8", "5"], "answer": 1},
    {"question": "What does the 'len()' function in Python do?", "options": ["Returns the length of an object", "Prints an object", "Adds two objects", "Returns the type of an object"], "answer": 0},
    {"question": "Which operator is used for exponentiation in Python?", "options": ["^", "**", "*", "//"], "answer": 1},
    {"question": "How do you start a comment in Python?", "options": ["//", "#", "/*", "--"], "answer": 1},
    {"question": "Which data type is used to store a whole number in Python?", "options": ["int", "float", "str", "list"], "answer": 0},
    {"question": "What does the Python function 'range(5)' generate?", "options": ["5", "0-5", "1-5", "0, 1, 2, 3, 4"], "answer": 3},
    {"question": "Which Python library is used for scientific computing?", "options": ["numpy", "math", "random", "os"], "answer": 0},
    {"question": "What is the correct syntax to create a tuple in Python?", "options": ["[]", "()", "{}", "<>"], "answer": 1}
]

# Randomize questions order
random.shuffle(questions)

def show_instructions():
    instruction_window = tk.Tk()
    instruction_window.title("Quiz Instructions")
    instruction_window.geometry("1920x1080")
    instruction_window.configure(bg="#f0f8ff")  # Light Blue Background
    instruction_window.resizable(False, False)
    title_frame = tk.Frame(instruction_window, bg="#4682b4")
    title_frame.pack(fill=tk.X)
    tk.Label(
        title_frame,
        text="📝 Welcome to the Handwave Quiz!",
        font=("Arial", 22, "bold"),bg="#4682b4",fg="white",pady=15).pack()
    content_frame = tk.Frame(instruction_window, bg="#f0f8ff")
    content_frame.pack(pady=20, padx=30)
    tk.Label(
        content_frame,
        text="📘 Please Read the Instructions Carefully",
        font=("Arial", 18, "bold"),bg="#f0f8ff",fg="#2f4f4f" ).pack(anchor="w", pady=(0, 20))
    instructions = [
        "✔ Ensure your face is visible to the webcam during the entire quiz.",
        "👉 Use your *index finger* to point and select an option.",
        "⏳ Hold your finger steady on the option for *2 seconds* to confirm selection.",
        "🎯 Each correct answer gives you *1 point*.",
        "🚪 Click the *Exit* button at the end of the quiz to close.",
    ]
    for point in instructions:
        tk.Label(
            content_frame,
            text=point,
            font=("Arial", 14),
            bg="#f0f8ff",
            fg="#333333",anchor="w",
            justify="left",wraplength=740).pack(fill="x", pady=5)
    tk.Label(
        instruction_window,
        text="Good Luck! 🍀",
        font=("Arial", 16, "bold"),
        bg="#f0f8ff",
        fg="#006400"
    ).pack(pady=20)
    tk.Button(
        instruction_window,
        text="Start Quiz",
        command=instruction_window.destroy,
        font=("Arial", 14, "bold"),
        bg="#4CAF50",
        fg="white",
        width=15,
        height=2
    ).pack(pady=10)
    instruction_window.mainloop()

# Login Page
def login_page():
    login_window = tk.Tk()
    login_window.title("User Login")
    login_window.geometry("1920x1080")
    login_window.configure(bg="#d1c4e9")
    login_window.resizable(False, False)
    tk.Label(login_window, text="Quiz Game Login", font=("Arial", 20, "bold"), bg="#d1c4e9").pack(pady=20)
    tk.Label(login_window, text="Enter Name (only alphabets):", font=("Arial", 14), bg="#d1c4e9").pack(pady=5)
    name_entry = tk.Entry(login_window, font=("Arial", 20), bd=2, relief="solid", width=30)
    name_entry.pack(pady=10)
    tk.Label(login_window, text="Enter Roll Number (only digits):", font=("Arial", 14), bg="#d1c4e9").pack(pady=5)
    roll_entry = tk.Entry(login_window, font=("Arial", 20), bd=2, relief="solid", width=30)
    roll_entry.pack(pady=10)
    def validate_login():
        global user_name, roll_number
        user_name = name_entry.get().strip()
        roll_number = roll_entry.get().strip()
        if any(char.isdigit() for char in user_name):
            messagebox.showerror("Invalid Input", "Username should contain only alphabets!")
        elif not roll_number.isdigit():
            messagebox.showerror("Invalid Input", "Roll Number should contain only digits!")
        else:
            login_window.destroy()
            show_instructions()
    tk.Button(login_window, text="Start Quiz", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", command=validate_login, width=15, height=2).pack(pady=20)
    login_window.mainloop()

login_page()

# Quiz UI Settings
width, height = 1920, 1080
option_height = 120
smoothing_factor = 0.7
prev_x, prev_y = 0, 0

cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

def draw_ui(frame, question, options, selected_option):
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = 1.5
    text_color = (0, 0, 0)
    thickness = 3
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
        y_pos = 200 + (i * 150)
        option_box = (100, y_pos, 900, y_pos + option_height)
        option_boxes.append(option_box)
        color = (200, 200, 200) if selected_option != i else (0, 255, 0)
        cv2.rectangle(frame, (option_box[0], option_box[1]), (option_box[2], option_box[3]), color, -1)
        cv2.putText(frame, option, (120, y_pos + 80), font, 1.5, (0, 0, 0), 3)
    return option_boxes

def check_selection(x, y, option_boxes):
    for idx, (x1, y1, x2, y2) in enumerate(option_boxes):
        if x1 < x < x2 and y1 < y < y2:
            return idx
    return -1

# Main Quiz Loop
while cap.isOpened() and quiz_running:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (width, height))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_results = face_detection.process(rgb_frame)
    if not face_results.detections:
        cv2.putText(frame, "⚠ Face not detected!", (600, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
        cv2.imshow("Quiz Game", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    results = hands.process(rgb_frame)

    if current_question < len(questions):
        # Speak the question only once when question loads
        if selected_option == -1:
            speak(questions[current_question]["question"])
        option_boxes = draw_ui(frame, questions[current_question]["question"], questions[current_question]["options"], selected_option)
    else:
        cap.release()
        cv2.destroyAllWindows()

        # Save score to CSV file
        with open("scores.csv", "a") as file:
            file.write(f"{user_name},{roll_number},{score},{time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        score_window = tk.Tk()
        score_window.title("Quiz Score")
        score_window.geometry("400x300")
        score_window.configure(bg="#e3f2fd")
        label = tk.Label(score_window, text=f"Quiz Over!\nName: {user_name}\nRoll No: {roll_number}\nYour Score: {score}/{len(questions)}", font=("Arial", 16, "bold"), bg="#e3f2fd")
        label.pack(pady=40)
        def exit_quiz():
            score_window.destroy()
        tk.Button(score_window, text="Exit", command=exit_quiz, font=("Arial", 14, "bold"), bg="#FF5722", fg="white", width=12, height=2).pack(pady=10)
        score_window.mainloop()
        break

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x, y = int(index_finger_tip.x * width), int(index_finger_tip.y * height)
            x = int(prev_x * smoothing_factor + x * (1 - smoothing_factor))
            y = int(prev_y * smoothing_factor + y * (1 - smoothing_factor))
            prev_x, prev_y = x, y
            cv2.circle(frame, (x, y), 15, (0, 0, 255), -1)
            current_selection = check_selection(x, y, option_boxes)
            if current_selection != -1:
                if current_selection != selected_option:
                    selected_option = current_selection
                    last_selection_time = time.time()
                elif time.time() - last_selection_time > 2:
                    if selected_option == questions[current_question]["answer"]:
                        score += 1
                        speak("Correct!")
                    else:
                        speak("Incorrect!")
                    time.sleep(1)
                    current_question += 1
                    selected_option = -1

    cv2.imshow("Quiz Game", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
