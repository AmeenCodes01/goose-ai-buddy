# 🎤 Simple Voice Chat Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd C:\Users\User\productivity-buddy\python-service
pip install -r requirements_simple.txt
```

### 2. Set API Key
Create `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

### 3. Run Simple Voice Chat
```bash
python simple_voice_chat.py
```

## 🎯 How It Works

**Super Simple Flow:**
1. **Speak** - Say whatever you want
2. **Wait 2 seconds** - Let silence trigger processing
3. **AI responds** - Hears and replies via speech
4. **Repeat** - Keep the conversation going!

## ✨ Features

- **No threads** - Simple, clean code
- **2-second silence detection** - Natural conversation flow
- **Continuous loop** - Keeps going until you stop (Ctrl+C)
- **Memory** - Remembers your conversation
- **AI buddy personality** - Supportive and encouraging

## 🎛️ Settings You Can Adjust

In `simple_voice_chat.py`:

```python
# Line 24 - Voice sensitivity (higher = less sensitive to noise)
self.silence_threshold = 0.02  # Try 0.03 for less sensitivity

# Line 25 - Silence wait time 
self.silence_duration = 2.0    # How long to wait before processing
```

## 📝 Example Conversation

```
🎧 Listening for voice input...
🗣️  Voice detected, starting recording...
🎵 Processing recorded audio (3.2s)...
👤 User said: Hi, how are you doing today?
🤖 AI says: Hey there! I'm doing great, thanks for asking. How's your day going so far?
🔊 Finished speaking
💬 Conversation turn: 1

🎧 Listening for voice input...
🗣️  Voice detected, starting recording...
🎵 Processing recorded audio (2.8s)...
👤 User said: I have a lot of work to do and feeling overwhelmed
🤖 AI says: I hear you on feeling overwhelmed. What's the biggest thing on your plate right now? Sometimes breaking it down helps.
🔊 Finished speaking
💬 Conversation turn: 2
```

## 🔧 Troubleshooting

### **Not detecting voice:**
- Speak louder or closer to microphone
- Lower `silence_threshold` to `0.015`
- Check Windows microphone settings

### **Too sensitive (picks up noise):**
- Increase `silence_threshold` to `0.03` or `0.04`
- Make sure room is relatively quiet

### **Takes too long to process:**
- Reduce `silence_duration` to `1.5` seconds
- But don't go below 1 second

### **API errors:**
- Check your OpenAI API key is correct
- Ensure you have credits in your OpenAI account

## 🎉 That's It!

This simplified version removes all the complexity while keeping the core functionality:
- **Clean voice detection** 
- **Natural conversation flow**
- **AI buddy personality**
- **No threading complications**

Just run it and start talking! 🗣️➡️🤖➡️🗣️➡️🤖
