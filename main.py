import sys
import subprocess
import json
import re
import time
import os
import uuid
from pathlib import Path
import ffmpeg


from faster_whisper import WhisperModel

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QMessageBox,
    QFileDialog
)

TASK_FILE = "tasks.json"

# Load Whisper model once (faster)
whisper_model = WhisperModel("base", compute_type="int8")


# ---------------------------
# OLLAMA CALL
# ---------------------------
def ollama_generate(prompt, model="mistral:latest"):
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    return result.stdout.strip()


# ---------------------------
# STORAGE
# ---------------------------
def load_tasks():
    if os.path.exists(TASK_FILE):
        try:
            with open(TASK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_tasks(tasks):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


# ---------------------------
# TRANSCRIPTION
# ---------------------------
def extract_audio_from_video(video_path):
    # Convert to absolute path and use forward slashes
    video_path = str(Path(video_path).resolve())
    audio_path = str(Path("temp_audio.wav").resolve())

    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, format="wav", acodec="pcm_s16le", ac=1, ar="16000")
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}") from e

    return audio_path


def transcribe_audio(file_path):
    segments, _ = whisper_model.transcribe(file_path)
    text = ""
    for segment in segments:
        text += segment.text + " "
    return text.strip()


# ---------------------------
# AI TASK EXTRACTION
# ---------------------------
def extract_tasks_from_text(text):
    prompt = f"""
Extract tasks from the text below.

Return ONLY a valid JSON array of strings.
No explanations.
No markdown.
No extra text.

Text:
{text}
"""
    response = ollama_generate(prompt)

    match = re.search(r'\[.*?\]', response, re.DOTALL)
    if not match:
        return []

    try:
        return json.loads(match.group(0))
    except:
        return []


# ---------------------------
# TASK LOGIC
# ---------------------------
def add_tasks(tasks, new_texts, source="manual"):
    for text in new_texts:
        task = {
            "id": str(uuid.uuid4()),
            "text": text,
            "completed": False,
            "timestamp": int(time.time()),
            "priority_score": 0,
            "source": source
        }
        tasks.append(task)

    rank_tasks(tasks)


def rank_tasks(tasks):
        incomplete_tasks = [t for t in tasks if not t["completed"]]

        if not incomplete_tasks:
            return

        # Build clean prompt
        task_list_text = "\n".join(
            [f"{i+1}. ID: {t['id']} | Task: {t['text']}" 
            for i, t in enumerate(incomplete_tasks)]
        )

        prompt = f"""
    You are a productivity AI.

    Rank the following tasks from MOST important to LEAST important.

    Consider:
    - Urgency
    - Practical importance
    - Likely deadlines
    - Real-world impact

    Return ONLY a JSON array of task IDs in ranked order.
    No explanations.
    No markdown.
    No extra text.

    Tasks:
    {task_list_text}
    """

        response = ollama_generate(prompt)

        # Extract JSON array
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if not match:
            return

        try:
            ranked_ids = json.loads(match.group(0))
        except:
            return

        # Assign priority scores based on ranking
        id_to_score = {
            task_id: len(ranked_ids) - i
            for i, task_id in enumerate(ranked_ids)
        }

        for task in tasks:
            if task["id"] in id_to_score:
                task["priority_score"] = id_to_score[task["id"]]
            else:
                task["priority_score"] = 0

        # Sort descending
        tasks.sort(key=lambda x: x["priority_score"], reverse=True)



# ---------------------------
# GUI
# ---------------------------
class TaskTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskTracker")
        self.setGeometry(200, 200, 600, 500)

        self.tasks = load_tasks()

        self.layout = QVBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter a task or dump thoughts...")
        self.layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Manual Task")
        self.add_button.clicked.connect(self.add_manual)
        self.ai_button = QPushButton("Extract from Text")
        self.ai_button.clicked.connect(self.extract_text_ai)

        self.upload_button = QPushButton("Upload MP3")
        self.upload_button.clicked.connect(self.upload_media)

        self.complete_button = QPushButton("Complete Selected")
        self.complete_button.clicked.connect(self.complete_selected)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.ai_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.complete_button)

        self.layout.addLayout(button_layout)

        self.task_list = QListWidget()
        self.layout.addWidget(self.task_list)

        self.setLayout(self.layout)

        self.refresh_list()

    def refresh_list(self):
        self.task_list.clear()
        for task in self.tasks:
            display = f"{task['text']}  (score: {task['priority_score']})"
            self.task_list.addItem(display)

    def add_manual(self):
        text = self.input_field.text().strip()
        if not text:
            return
        add_tasks(self.tasks, [text], source="manual")
        save_tasks(self.tasks)
        rank_tasks(self.tasks)
        self.refresh_list()
        self.input_field.clear()

    def extract_text_ai(self):
        text = self.input_field.text().strip()
        if not text:
            return
        extracted = extract_tasks_from_text(text)
        if not extracted:
            QMessageBox.warning(self, "AI Error", "No tasks extracted.")
            return
        add_tasks(self.tasks, extracted, source="ai")
        rank_tasks(self.tasks)
        save_tasks(self.tasks)
        self.refresh_list()
        self.input_field.clear()

    def upload_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            "Media Files (*.mp3 *.mp4)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith(".mp4"):
                print("Uploading file:", file_path)
                print("Exists?", Path(file_path).exists())
                file_path = extract_audio_from_video(file_path)

            transcript = transcribe_audio(file_path)

            if not transcript:
                QMessageBox.warning(self, "Transcription Error", "Could not transcribe audio.")
                return

            extracted = extract_tasks_from_text(transcript)

            if not extracted:
                QMessageBox.warning(self, "AI Error", "No tasks extracted.")
                return

            add_tasks(self.tasks, extracted, source="media")

            save_tasks(self.tasks)
            self.refresh_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def complete_selected(self):
        selected = self.task_list.currentRow()
        if selected >= 0:
            self.tasks.pop(selected)
            save_tasks(self.tasks)
            self.task_list.takeItem(selected)  


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskTracker()
    window.show()
    sys.exit(app.exec()) 