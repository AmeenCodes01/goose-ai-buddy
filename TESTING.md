# Testing the Productivity Buddy

This guide provides step-by-step instructions to set up and test the key features of the Productivity Buddy application.

## 1. Prerequisites

Before you begin, ensure you have the following:

- **Python 3.9+** and `pip` installed.
- A working **microphone** connected to your computer.
- A **Wi-Fi** adapter.
- **(Optional for Wi-Fi Test)** A smartphone capable of creating a Wi-Fi hotspot.
- A command-line tool like **cURL** or a GUI tool like **Postman** for testing API endpoints.

## 2. Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd productivity-buddy
    ```

2.  **Install Dependencies:**
    Install all required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r python-service/requirements.txt
    ```

## 3. Running the Application

All components (web server, wake word listener, Wi-Fi scanner) are managed by a single script.

1.  **Start the main script:**
    ```bash
    python python-service/simple_main.py
    ```

2.  **Check the output:**
    You should see log messages indicating that the server is running and the background threads have started:
    ```
    INFO:__main__:🤖 Starting Simple Productivity Buddy...
    INFO:__main__:👂 Always-listening for wake word ('hey goose')...
    INFO:__main__:Wi-Fi Scanner Agent thread started.
    INFO:__main__:🌐 API server running on http://localhost:5000
    INFO:werkzeug: * Running on http://localhost:5000
    ```

## 4. Verification Steps

### Test 1: API Health Check

Verify that the web server is running correctly.

-   **Action:** Open a new terminal and run the following `curl` command:
    ```bash
    curl http://localhost:5000/health
    ```
-   **Expected Result:** You should receive a JSON response confirming the service is running.
    ```json
    {
      "status": "running",
      "timestamp": "..."
    }
    ```

### Test 2: Wake Word and Voice Interaction

Verify that the application is listening and can respond.

-   **Action:**
    1.  Move close to your microphone.
    2.  Clearly say the wake word: **"hey goose"**.
-   **Expected Result:**
    -   You should see a log message in the application terminal: `INFO:wake_word_listener:Wake word 'hey goose' detected!`.
    -   You may hear a short sound indicating that the system is now actively listening for a command.
-   **Action:**
    1.  After the wake word is acknowledged, say: **"hello"**.
-   **Expected Result:**
    -   The application should respond with a synthesized voice, saying something like "Hello there!".

### Test 3: Distraction Analysis Endpoint

Verify that the application can analyze a URL for distraction potential.

-   **Action:** In a new terminal, send a `POST` request using `curl`.
    ```bash
    curl -X POST -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com\", \"title\":\"YouTube\"}" http://localhost:5000/analyze-distraction
    ```
-   **Expected Result:** You should receive a JSON response analyzing the URL. The `is_distraction` field will likely be `true`.
    ```json
    {
      "analysis": "YES",
      "is_distraction": true,
      "status": "analyzed",
      "timestamp": "...",
      "title": "YouTube",
      "url": "https://www.youtube.com"
    }
    ```

### Test 4: Wi-Fi Station Detection

Verify that the background scanner can identify transit-related Wi-Fi networks. This is the easiest way to test this feature.   (enable locations.)

-   **Action (Simulate a Network):**
    1.  On your smartphone, enable the **Wi-Fi hotspot** feature.
    2.  Configure your hotspot's name (SSID) to be **`MyTestBus`** or **`TrainStationWifi`**.
    3.  Ensure your computer is able to see this new Wi-Fi network (you don't need to connect to it).
-   **Expected Result:**
    -   Within 60 seconds, a log message should appear in the application's terminal, confirming the detection.
    ```
    INFO:__main__:🚉 EVENT: Transit station detected via Wi-Fi SSID: ... MyTestBus ...
    ```
-   **Cleanup:** Remember to turn off your mobile hotspot after the test.
