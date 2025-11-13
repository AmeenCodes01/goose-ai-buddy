# 🎤 Voice Chat Setup Guide

## Voice Chat MVP for Productivity Buddy

This guide will help you set up and test the new voice chat functionality that transforms your productivity buddy into a conversational AI assistant.

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
cd python-service
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

**Windows:**
```cmd
set OPENAI_API_KEY=your_api_key_here
```

**Or create a `.env` file:**
```
OPENAI_API_KEY=your_api_key_here
```

### 3. Test Voice Chat

```bash
python test_voice_chat.py
```

This will test just the voice functionality without the full system.

### 4. Run Full System with Voice

```bash
python main.py
```

## 🎯 How It Works

### Voice Input
- **Always listening** for your voice
- **3-second silence** automatically ends your message and sends it to AI
- **Whisper STT** converts your speech to text

### AI Processing
- **GPT-4** generates supportive, buddy-like responses
- **Context aware** of time, your energy, tasks mentioned
- **Memory** of your conversation and patterns

### Voice Output
- **Text-to-speech** speaks the AI response
- **Natural pacing** and personality

## 🎛️ API Endpoints

The voice chat adds these new endpoints to your productivity buddy:

- `POST /voice/start` - Start voice listening
- `POST /voice/stop` - Stop voice listening  
- `GET /voice/status` - Get conversation status
- `POST /voice/check-in` - Trigger proactive check-in

## 💬 Example Conversation Flow

**You:** "Hey, how's it going?"

**AI Buddy:** "Hey! Good to hear from you. How are you feeling today? Got anything on your mind?"

**You:** "I'm feeling pretty tired, and I have this assignment I've been putting off"

**AI Buddy:** "I hear you on the tiredness. That assignment sounds like it's weighing on you a bit. Want to break it down into something small we can tackle together?"

**You:** "Yeah, I guess I should start with just reading the requirements"

**AI Buddy:** "Perfect! Reading the requirements is a great first step. How about giving that 10 minutes and then we'll check in? Sometimes just starting makes everything feel less overwhelming."

## 🎨 Features Included

### ✅ MVP Features (Built)
- [x] Voice input with 3-second silence detection
- [x] OpenAI Whisper speech-to-text
- [x] GPT-4 conversational AI with buddy personality
- [x] Text-to-speech output
- [x] Basic conversation memory
- [x] Context extraction (tasks, mood, energy)
- [x] Integration with existing productivity system

### 🔮 Next Phase Ideas
- [ ] Proactive check-ins based on time/patterns
- [ ] Better voice interruption handling
- [ ] Emotion detection from voice tone
- [ ] Persistent memory across sessions
- [ ] Smart scheduling suggestions
- [ ] Integration with calendar/todo apps

## 🛠️ Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'sounddevice'"**
```bash
pip install sounddevice
```

**2. "OpenAI API key not set"**
- Make sure `OPENAI_API_KEY` environment variable is set
- Or create a `.env` file with your key

**3. "Audio device not found"**
- Check your microphone is connected and working
- Try running the test script first

**4. "Permission denied for microphone"**
- Allow microphone access in your system settings
- On Windows: Settings > Privacy > Microphone

### Audio Issues

**Low audio detection:**
- Adjust `silence_threshold` in `voice_chat.py` (line 27)
- Speak closer to microphone

**Voice cuts off too early:**
- Increase `silence_duration` in `voice_chat.py` (line 28)

## 🎯 Usage Tips

1. **Speak naturally** - no need to be formal
2. **Mention tasks/goals** - the AI will remember and check in
3. **Share your energy level** - helps AI adapt its suggestions
4. **Be honest about struggles** - AI provides better support
5. **Use it throughout your day** - not just for work sessions

## 🚀 Integration with Existing Features

The voice chat works alongside your existing productivity buddy features:

- **Gesture recognition** still works (wave to start focus, etc.)
- **Browser extension** still blocks distracting sites
- **Session management** is enhanced with voice updates
- **Content analysis** can be discussed with AI

Your productivity buddy is now a **conversational companion** that remembers your patterns and helps you stay accountable through natural conversation!

## 🎉 What You've Built

You now have an AI buddy that:
- **Listens** to you throughout the day
- **Remembers** what you mention (tasks, feelings, goals)
- **Checks in** organically about your progress
- **Adapts** its support based on your energy and responses
- **Takes action** when needed (blocking sites, starting sessions)

It's like having a supportive friend who's always there to help you stay on track! 🤖✨
