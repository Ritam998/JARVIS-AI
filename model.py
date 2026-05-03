

import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import random
import time
import requests
import json
import re
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


engine = pyttsx3.init()
voices = engine.getProperty('voices')
# Prefer a cleaner voice if available
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 175)   # words per minute
engine.setProperty('volume', 0.95)


WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
DEFAULT_CITY = "Kolkata"
JARVIS_API_BASE = "http://127.0.0.1:8000"   # local FastAPI server

conversation_history: list[dict] = []
MAX_HISTORY = 10   

def add_to_memory(role: str, content: str):
    conversation_history.append({"role": role, "content": content})
    # Trim to max history (keep pairs)
    while len(conversation_history) > MAX_HISTORY * 2:
        conversation_history.pop(0)

def speak(text: str):
    print(f"\n🤖 Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()

def listen(timeout: int = 5, phrase_limit: int = 10) -> str:
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("🎙️  Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return "none"

    try:
        print("🔍 Recognizing...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"👤 You: {query}")
        return query.lower().strip()
    except sr.UnknownValueError:
        print("⚠️  Didn't catch that.")
        return "none"
    except sr.RequestError as e:
        print(f"❌ Recognition error: {e}")
        return "none"

# ─────────────────────────────────────────
# GREETING
# ─────────────────────────────────────────
def wish_me():
    hour = datetime.datetime.now().hour
    greeting = (
        "Good morning!" if hour < 12 else
        "Good afternoon!" if hour < 18 else
        "Good evening!"
    )
    speak(f"{greeting} I am Jarvis, your upgraded AI assistant. Say 'Hey Jarvis' to activate me.")


SYSTEM_PROMPT = """You are Jarvis, a witty, intelligent, and helpful AI voice assistant inspired by Iron Man's Jarvis.
You are running on a local machine. You speak in a friendly, slightly formal British style.
Keep responses SHORT (1-3 sentences) since you will be spoken aloud via text-to-speech.
Never use markdown, bullet points, or special characters.
Always stay helpful, clever, and personable."""

def ai_chat(user_message: str) -> str:
    """Send message to Claude API with conversation history."""
    add_to_memory("user", user_message)

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 200,
        "system": SYSTEM_PROMPT,
        "messages": conversation_history,
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        reply = resp.json()["content"][0]["text"].strip()
        add_to_memory("assistant", reply)
        return reply
    except requests.exceptions.ConnectionError:
        return "I can't reach my brain right now. Check your internet connection, sir."
    except Exception as e:
        print(f"AI error: {e}")
        return "I ran into a small glitch. Let me recalibrate and try again."


def analyze_text(text: str) -> dict:
   
    try:
        resp = requests.post(
            f"{JARVIS_API_BASE}/analyze",
            json={"text": text},
            timeout=3,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"sentiment": "Neutral", "emotion": "Calm", "intent": "unknown"}


def get_time() -> str:
    now = datetime.datetime.now()
    return now.strftime("The time is %I:%M %p, and today is %A, %B %d.")

def get_weather(city: str = DEFAULT_CITY) -> str:
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}"
            f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
        )
        data = requests.get(url, timeout=5).json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            return (
                f"In {city} it is {temp:.1f} degrees Celsius, feels like {feels:.1f}. "
                f"Conditions: {desc}. Humidity is {humidity} percent."
            )
        return "I couldn't retrieve the weather right now."
    except Exception:
        return "Weather service is unreachable at the moment."

def tell_joke() -> str:
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "I asked my computer to play something cool. It said: No problem, I'll go to Spotify.",
        "Why did the AI go to therapy? Too many neural breakdowns.",
        "I tried to write a joke about UDP, but I'm not sure you'll get it.",
        "Why don't skeletons fight each other? They don't have the guts!",
        "My Wi-Fi password is 'incorrect'. So when people ask, I say: the password is incorrect.",
    ]
    return random.choice(jokes)

def calculate(expression: str) -> str:
    """Safely evaluate a math expression."""
    # Sanitize: only allow numbers and operators
    clean = re.sub(r'[^0-9+\-*/().\s]', '', expression)
    try:
        result = eval(clean, {"__builtins__": {}})
        return f"The answer is {result}."
    except Exception:
        return "I couldn't compute that. Please try rephrasing the expression."

def play_youtube(query: str):
    speak(f"Playing {query} on YouTube.")
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(search_url)

def search_google(query: str):
    clean = query.replace("search", "").replace("google", "").strip()
    speak(f"Searching Google for {clean}.")
    webbrowser.open(f"https://www.google.com/search?q={clean.replace(' ', '+')}")

def open_site(name: str, url: str):
    speak(f"Opening {name}.")
    webbrowser.open(url)

def set_reminder(text: str):
    """Simple in-session reminder (extendable to persistent storage)."""
    speak(f"Got it. I'll remind you to: {text}.")
    # TODO: hook into OS notification or a scheduler


SITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "spotify": "https://open.spotify.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "netflix": "https://www.netflix.com",
    "maps": "https://maps.google.com",
}

def route_command(command: str) -> bool:
    """
    Try to handle the command locally.
    Returns True if handled, False if should fall back to AI.
    """
    # ── Time ──────────────────────────────
    if any(w in command for w in ['what time', 'current time', 'what\'s the time', 'time now']):
        speak(get_time())
        return True

    
    if 'weather' in command:
        # Try to extract city name after "in"
        match = re.search(r'weather (?:in|at|for) ([a-z ]+)', command)
        city = match.group(1).strip().title() if match else DEFAULT_CITY
        speak(get_weather(city))
        return True

    
    if any(w in command for w in ['joke', 'funny', 'make me laugh']):
        speak(tell_joke())
        return True

    if 'calculate' in command or 'what is' in command and any(op in command for op in ['+', '-', 'times', 'divided', 'plus', 'minus']):
        expr = re.sub(r'(calculate|what is)', '', command)
        expr = expr.replace('plus', '+').replace('minus', '-')
        expr = expr.replace('times', '*').replace('multiplied by', '*')
        expr = expr.replace('divided by', '/').replace('x', '*')
        speak(calculate(expr))
        return True

    
    match = re.search(r'play (.+?) on youtube', command)
    if match:
        play_youtube(match.group(1))
        return True

    
    for site, url in SITE_MAP.items():
        if f'open {site}' in command:
            open_site(site.capitalize(), url)
            return True

    if 'search' in command or 'google' in command:
        search_google(command)
        return True

   
    match = re.search(r'remind(?:er)? (?:me )?(?:to )?(.+)', command)
    if match:
        set_reminder(match.group(1))
        return True

    
    if 'who made you' in command or 'who built you' in command:
        speak("Ritam built me. A brilliant mind, I must say.")
        return True

    if 'can you speak bengali' in command:
        speak("Ami tomake bhalobashi.")
        return True

    if 'tell it jarvis' in command:
        speak("Somnath Sir bhalo hoyeche to?")
        return True

    return False  # hand off to AI

def execute_commands():
    speak("I'm active and ready, sir.")
    while True:
        command = listen()

        if command == "none":
            continue

        if any(w in command for w in ['exit', 'quit', 'sleep', 'goodbye', 'bye']):
            speak("Going to sleep. Call me when you need me, sir.")
            break

        # Analyze sentiment for awareness
        analysis = analyze_text(command)
        emotion = analysis.get("emotion", "Calm")
        if emotion in ["Sad", "Angry"]:
            speak("I noticed you might be feeling down. I'm here to help.")

        # Route locally or fall back to AI
        handled = route_command(command)
        if not handled:
            response = ai_chat(command)
            speak(response)

def main():
    wish_me()
    speak("Say 'Hey Jarvis' or 'OK Jarvis' to wake me up.")

    while True:
        query = listen(timeout=7)

        if any(wake in query for wake in ['hey jarvis', 'ok jarvis', 'hi jarvis', 'jarvis']):
            speak("Yes sir, I'm listening.")
            execute_commands()

        time.sleep(0.5)

if __name__ == "__main__":
    main()