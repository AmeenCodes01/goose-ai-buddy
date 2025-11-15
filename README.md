# Productivity Buddy

Productivity Buddy is an intelligent agent designed to help you stay focused during work or study sessions. It actively monitors your digital environment, identifies potential distractions, and uses voice, gestures, and automated actions to gently guide you back on track.

I plan to build this properly till the end as a external product using goose. 

THE VISION:
((implementing very soon, got late :"))
Unlike typical productivity tools, Productivity Buddy is proactive. It doesn’t wait for you to ask for help — it checks in, sets timers, and holds you accountable in real time.
Imagine this:
You: “Hey, good morning Goose.”
Goose: “Good morning. Out of bed yet?”
You: “No.”
Goose: “Alright. You’ve got 5 minutes. I’ll check in.”
(5 minutes later…)
Goose (itself): “Time’s up. Are you up now, or do we need to reset?”

this can happen for literally any kind of task. A human checking on you often would be annoying, a tiny voice in ear ? not so.
This isn’t just a timer. It’s a dynamic scheduler, a voice-based accountability partner, and a daily reflection engine — all powered by Goose and built for real-world focus.



## ✨ Core Features

*   **Automated Distraction Analysis**: A browser extension monitors browsing activity. If you linger on a potentially distracting site, the URL is sent to a backend AI service for analysis.
*   **Gesture-Based Control**: Use simple hand gestures to enable or disable the distraction analysis on the fly.
    *   **Thumbs up**: Enables distraction analysis.
    *   **Peace sign**: Disables distraction analysis.
*   **Voice Interaction & Interventions**: The system can provide spoken feedback and interventions. If you're repeatedly distracted, it can initiate a conversation to help you refocus.
*   **Wake Word Activation**: Activate the voice interaction system by saying **"hello"**.
*   **Location-Aware Triggers**: The system can detect when you're in a specific environment (like a bus or train station) by scanning for known Wi-Fi SSIDs and trigger context-specific actions or reminders.

## 🏗️ System Architecture

The system is composed of two main components: a Python-based backend service and a browser extension.

```
+-----------------------+      HTTP POST      +------------------------+
|                       | (URL for analysis)  |                        |
|   Browser Extension   |--------------------▶|  Python Backend Service|
| (JavaScript)          |◀--------------------|      (Flask)           |
|                       |  (JSON response)    |                        |
+-----------------------+                     +------------------------+
        |                                               |
        | Monitors Tabs                                 | Manages...
        |                                               |
        ▼                                               ▼
+-----------------------+             +---------------------------------+
|      User's Web Browser             |  - Gesture Recognition (OpenCV) |
+-----------------------+             |  - Wake Word Detection          |
                                      |  - Voice Synthesis (pyttsx3)    |
                                      |  - Wi-Fi Scanning               |
                                      |  - AI Analysis (Goose)          |
                                      +---------------------------------+
```

### Backend Service (`python-service/`)

The core logic resides in the Python service, which runs locally. It's a Flask application that manages all the intelligent features.

*   `simple_main.py`: The main entry point. It starts the Flask web server and initializes all background threads for gesture, voice, and Wi-Fi monitoring.
*   `distraction_tracker.py`: Manages the state of distraction analysis (enabled/disabled) and logs distraction events.
*   `gesture_recognition.py`: Uses `mediapipe` and `opencv` to capture webcam feed and detect hand gestures ("open" and "closed" fist).
*   `wake_word_listener.py`: Listens continuously for the "hey goose" wake word using the microphone.
*   `voice_interaction.py`: Handles text-to-speech (TTS) to give voice feedback. ( & speech-to-text)
*   `wifi_scanner.py`: Periodically scans for Wi-Fi networks to detect location-based triggers. (train / bus stations)
*   `requirements.txt`: A list of all the Python dependencies.
*   `goose_integration.py`: Python wrapper for goose CLI (goose-generated, I only debugged and fixed commands I needed, will be testing others as well, hoping to contribute.)

### Browser Extension (`simple_bs_ext/`)

A simple browser extension that acts as the primary sensor for user activity.

*   `manifest.json`: Defines the extension's permissions and scripts.
*   `simple_background_new.js`: The service worker that contains the core logic. It listens for tab changes, starts a timer, and communicates with the backend service.
*   `simple_content.js`: A content script injected into pages (currently not used for major functionality).

## 🛠️ Setup & Installation

### Prerequisites

*   Python 3.9+
*   A working webcam and microphone.
*   Administrator/root privileges (for the Wi-Fi scanner).
*   You'll have to let apps access your location in settings for wifi-scanner to work. For windows, it's Settings> Privacy & security > Location
### 1. Backend Setup

1.  **Navigate to the project directory.**
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r python-service/requirements.txt
    ```

### 2. Browser Extension Setup

1.  Open your browser (e.g., Google Chrome).
2.  Navigate to the extensions page (`chrome://extensions`).
3.  Enable **"Developer mode"** (usually a toggle in the top-right corner).
4.  Click **"Load unpacked"**.
5.  Select the `simple_bs_ext` folder from the project directory.
6.  The "Simple Productivity Buddy" extension should now appear in your extensions list.

## ▶️ How to Run

1.  Open your terminal.
2.  Navigate to the project root directory.
3.  Run the main Python script:
    ```bash
    python python-service/simple_main.py
    ```
4.  The script will request administrator privileges (for Wi-Fi scanning). A new window may open.
5.  You should see logs indicating that the Flask server, gesture recognition, and wake word listener are all running.

## 📖 How to Use

*   **Distraction Analysis**: Simply browse the web. If you land on a site and stay there for more than 10 seconds (for demo purposes, should be 1m else might get rate limit error), the extension will ask the backend to analyze it. If it's deemed a distraction, the tab will be automatically redirected to a new tab page.
*   **Gesture Control**: Show your hand to the webcam.
    *   **Thumbs up**: Enables the analysis. You should hear "Distraction analysis enabled."
    *   **Peace sign**: Disables the analysis. You should hear "Distraction analysis disabled."  ( make sure your hand is parallel to screen when doing peace sign)
*   **Voice Commands**: Say **"hello"** to activate the listener, followed by your command. 


### Manual Testing

The `TESTING.md` file contains a detailed, step-by-step guide for verifying all major features:
*   API Health Check
*   Wake Word and Voice Interaction
*   Distraction Analysis Endpoint
*   Wi-Fi Station Detection


### Usage of goose / Stratedgy
(goose helped me grow def, debugging others code was a good \7 almost new experience)


My main prompts are in plan.md. Other messages were minor fixes/quering about plan. 

Before writing any code, I always asked Goose to explain how one file’s logic would connect to another. This helped me avoid messy code.

Subagent-Driven Build Process
Since I wasn’t 100% sure of the final shape of the product, I used subagents to build iteratively and modularly:
- Start with a single file
→ Ask a subagent to generate basic functionality
→ Manually test it
- Add features incrementally
→ Use subagents to extend functionality
→ Run example commands and debug manually (especially for listen and speak errors)
- Integrate across files
→ Once individual files were stable, I stitched them together
→ Asked Goose to help with glue logic and CLI orchestration
- Parallel subagent use
→ For independent modules, I used multiple subagents in parallel
→ This helped speed up development — though I had to be cautious due to rate limits

🧪 Testing & Debugging
- I manually ran and tested every generated command and script
- When Goose-generated examples failed, I debugged them line by line
- I used VS Code to live-preview changes and iterate quickly
This wasn’t “vibe coding.” It was AI-assisted engineering — structured, intentional, and deeply educational.

