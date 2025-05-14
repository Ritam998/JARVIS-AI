# JARVIS-AI
#PYTHON BASED ASSISTANT 
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import random
import time
import pywhatkit
import requests

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def speak(text):
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()

def wish_me():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak("I am Jarvis. Say 'Hey Jarvis' to wake me up!")

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 1
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
    except Exception:
        print("Didn't catch that...")
        return "None"
    return query.lower()

def tell_joke():
    jokes = [
        "Why don't skeletons fight each other? They don't have the guts!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "Why do cows wear bells? Because their horns don't work!",
        "I told my computer I needed a break, and it said: No problem, I’ll go to sleep!"
    ]
    speak(random.choice(jokes))

def play_spotify():
    speak("Opening Spotify.")
    webbrowser.open("https://open.spotify.com/")

def get_weather():
    try:
        speak("Fetching weather details...")
        city = "Kolkata"  
        api_key = "c761bbf3abca88a3bb1bc251dd1beb82" 
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:
            temp = data["main"]["temp"] - 273.15  
            description = data["weather"][0]["description"]
            speak(f"The temperature in {city} is {temp:.1f} degrees Celsius with {description}.")
        else:
            speak("Sorry, couldn't fetch the weather right now.")
    except:
        speak("Error while getting the weather.")

def search_google(query):
    speak(f"Searching Google for {query}")
    query = query.replace("search", "") 
    query = query.strip()
    webbrowser.open(f"https://www.google.com/search?q={query}")

def smart_conversation(command):
    command = command.lower()

    if 'how are you' in command or 'how r u'in command:
        speak("I'm doing great! Thanks for asking. How can I help you today?")
    
    elif 'who are you' in command or 'who r you' in command:
        speak("I am Jarvis, your personal assistant, built to make your life easier.")

    elif 'your name' in command:
        speak("My name is Jarvis. At your service!")

    elif 'thank you' in command or 'thanks' in command:
        speak("You're most welcome!")

    elif 'what\'s up' in command or 'sup' in command:
        speak("Just helping you out, like always!")

    elif 'i love you' in command:
        speak("Aww! I'm flattered! Love you too, in a binary kind of way.")

    elif 'are you real' in command:
        speak("I'm real in your device and in your heart!")

    elif 'who made you' in command:
        speak(" Ritam built me.")
    
    elif 'can you speak bengali' in command:
        speak("Ami tomake bhalobashi.")

    else:
        speak("I'm sorry, I didn't understand that. But I'm learning every day!")



def execute_commands():
    while True:
        command = listen()

        if 'open youtube' in command:
            webbrowser.open("https://www.youtube.com")
            speak("Opening YouTube.")

        elif 'open google' in command:
            webbrowser.open("https://www.google.com")
            speak("Opening Google.")

        elif 'play music' in command or 'open spotify' in command:
            play_spotify()

        elif 'time' in command:
            time_str = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {time_str}.")

        elif 'tell me a joke' in command or 'joke' in command:
            tell_joke()

        elif 'weather' in command:
            get_weather()
  
        elif 'play' in command and 'on youtube' in command:
            song = command.replace('play', '').replace('on youtube', '').strip()
            speak(f"Playing {song} on YouTube")
            pywhatkit.playonyt(song)


        elif 'calculate' in command:
            speak("What should I calculate?")
            calc_query=listen()
            calc_query = calc_query.replace('plus', '+')
            calc_query = calc_query.replace('minus', '-')
            calc_query = calc_query.replace('times', '*')
            calc_query = calc_query.replace('multiplied by', '*')
            calc_query = calc_query.replace('divided by', '/')
            calc_query = calc_query.replace('x', '*')
            calc_query = calc_query.replace('X', '*')
            try:
                result=eval(calc_query)
                speak(f"The answer is {result}")
            except:
                speak("Sorry, I couldn't calculate that.")

        elif 'search' in command:
         search_google(command)

        
        elif 'tell it jarvis' in command:
             speak("Somnath Sir bhalo hoyeche to?")


        elif 'exit' in command or 'quit' in command or 'sleep' in command:
            speak("Okay, going to sleep. Wake me up when you need me!")
            break

        else:
             smart_conversation(command)


if __name__ == "__main__":
    wish_me()
    while True:
        query = listen()

        if 'hey jarvis' in query or 'ok jarvis' in query:
            speak("Yes sir, how can I help you?")
            execute_commands()

        time.sleep(1)
