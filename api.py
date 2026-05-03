
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import datetime
import re
import os
import requests


app = FastAPI(
    title="Jarvis API",
    description="Backend intelligence layer for Jarvis voice assistant",
    version="2.0.0",
)
@app.get("/")
def home():
    return {"message": "Jarvis API is running 🚀"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")


class UserInput(BaseModel):
    text: str

class ChatInput(BaseModel):
    message: str
    system_prompt: Optional[str] = None

class AnalysisResult(BaseModel):
    text: str
    sentiment: str
    emotion: str
    intent: str
    confidence: float
    timestamp: str


conversation_log: list[dict] = []


POSITIVE_WORDS = {
    'happy', 'great', 'awesome', 'love', 'excellent', 'wonderful',
    'fantastic', 'good', 'nice', 'amazing', 'best', 'thanks', 'thank', 'joy'
}
NEGATIVE_WORDS = {
    'sad', 'bad', 'hate', 'terrible', 'awful', 'horrible', 'worst',
    'angry', 'annoyed', 'frustrated', 'upset', 'disappointed', 'sorry'
}
NEUTRAL_WORDS = {
    'okay', 'fine', 'alright', 'sure', 'maybe', 'perhaps'
}

INTENT_PATTERNS = {
    "open_website":  r'\bopen\b.*(youtube|google|spotify|github|netflix)',
    "play_music":    r'\bplay\b',
    "weather":       r'\bweather\b',
    "time":          r'\btime\b|\bdate\b',
    "joke":          r'\bjoke\b|\bfunny\b|\blaugh\b',
    "calculate":     r'\bcalculate\b|\bwhat is\b.*[\d+\-*/]',
    "search":        r'\bsearch\b|\bgoogle\b',
    "reminder":      r'\bremind\b',
    "greeting":      r'\bhello\b|\bhi\b|\bhey\b|\bgood morning\b|\bgood evening\b',
    "farewell":      r'\bbye\b|\bexit\b|\bsleep\b|\bgoodbye\b',
    "question":      r'\bwhat\b|\bwho\b|\bwhere\b|\bwhen\b|\bhow\b|\bwhy\b',
}

EMOTION_MAP = {
    "Positive": ["Happy", "Excited", "Grateful"],
    "Negative": ["Sad", "Angry", "Frustrated"],
    "Neutral":  ["Calm", "Curious", "Neutral"],
}

def detect_sentiment(text: str) -> tuple[str, str, float]:
    words = set(re.findall(r'\b\w+\b', text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    total = pos + neg or 1

    if pos > neg:
        sentiment = "Positive"
        confidence = round(0.5 + (pos / total) * 0.5, 2)
    elif neg > pos:
        sentiment = "Negative"
        confidence = round(0.5 + (neg / total) * 0.5, 2)
    else:
        sentiment = "Neutral"
        confidence = 0.6

    import random
    emotion = random.choice(EMOTION_MAP[sentiment])
    return sentiment, emotion, confidence

def detect_intent(text: str) -> str:
    text_lower = text.lower()
    for intent, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, text_lower):
            return intent
    return "general_conversation"

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "online",
        "version": "2.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
    }

@app.post("/analyze", response_model=AnalysisResult)
def analyze(data: UserInput):
    if not data.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty.")

    sentiment, emotion, confidence = detect_sentiment(data.text)
    intent = detect_intent(data.text)

    result = {
        "text": data.text,
        "sentiment": sentiment,
        "emotion": emotion,
        "intent": intent,
        "confidence": confidence,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    conversation_log.append({"type": "analysis", **result})
    return result

@app.post("/chat")
def chat(data: ChatInput):
    system = data.system_prompt or (
        "You are Jarvis, a witty and helpful AI voice assistant. "
        "Keep replies concise (1-3 sentences) as they will be spoken aloud. "
        "Avoid markdown, bullets, or special characters."
    )

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 200,
        "system": system,
        "messages": [{"role": "user", "content": data.message}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        reply = resp.json()["content"][0]["text"].strip()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI response timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    entry = {
        "type": "chat",
        "user": data.message,
        "assistant": reply,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    conversation_log.append(entry)
    return {"reply": reply, "timestamp": entry["timestamp"]}

@app.get("/history")
def get_history(limit: int = 20):
    return {"history": conversation_log[-limit:], "total": len(conversation_log)}

@app.delete("/history")
def clear_history():
    conversation_log.clear()
    return {"message": "Conversation history cleared."}