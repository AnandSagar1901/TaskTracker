# TaskTracker
TaskTracker AI Media Edition
Overview

TaskTracker AI Media Edition is a Python-based desktop application that uses artificial intelligence to extract, manage, and prioritize tasks from multiple sources including manual input, text, audio, and video.

The application combines AI-powered task extraction, audio transcription, and automated ranking into a user-friendly graphical interface built with PyQt6.

Features

✅ Manual task entry

✅ AI task extraction from text

✅ Audio and video transcription to text

✅ AI-powered task prioritization

✅ Persistent task storage using JSON

✅ Graphical User Interface (GUI) built with PyQt6

How It Works

Manual Input
Users can type tasks directly into the input box.

Text Extraction
The system uses AI to extract actionable tasks from large blocks of text.

Audio/Video Transcription
Audio or video files are transcribed into text using a speech recognition model.

Task Ranking
Tasks are automatically ranked based on urgency, importance, and deadlines.

Persistent Storage
All tasks are stored in tasks.json so data is saved between sessions.

Project Structure
tasktracker.py      # Main Python application
tasks.json          # Stores task data
README.md           # Project documentation
Core Functions

add_tasks() – Adds new tasks to the system

rank_tasks() – Assigns priority scores using AI

extract_tasks_from_text() – Extracts tasks from text input

transcribe_audio() – Converts audio/video into text

Technologies Used

Python

PyQt6 (GUI Framework)

JSON (Data Storage)

Regular Expressions (re)

Faster-Whisper (Speech-to-Text)

AI model integration (via Ollama or similar)

Installation

Install Python (3.9+ recommended)

Install required packages:

pip install PyQt6 faster-whisper ffmpeg-python

Run the application:

python tasktracker.py
Future Improvements

Deadline-based automatic urgency detection

Cloud synchronization

Mobile version

Advanced filtering and sorting

Author

Your Name
Science Fair Project – 2026