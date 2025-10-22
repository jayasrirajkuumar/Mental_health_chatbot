# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
import re
import random
import google.generativeai as genai  # Gemini SDK

# -----------------------------
# BASIC CONFIG
# -----------------------------
DB = 'chat.db'
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# -----------------------------
# DATABASE HELPERS
# -----------------------------
def add_message(session_id, role, text):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO messages (session_id, role, text) VALUES (?,?,?)', (session_id, role, text))
    conn.commit()
    conn.close()

def get_recent_context(session_id, limit=10):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT role, text FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?', (session_id, limit))
    rows = c.fetchall()
    conn.close()
    rows.reverse()  # chronological order
    return [{"role": r[0], "text": r[1]} for r in rows]

# -----------------------------
# EMOTION & CRISIS DETECTION
# -----------------------------
CRISIS_KEYWORDS = [
    'suicide', 'kill myself', 'end my life', 'i want to die', 'hurt myself', 'cant go on', 'cut myself'
]

EMOTION_KEYWORDS = {
    'sadness': ['sad', 'depressed', 'down', 'hopeless', 'unhappy', 'miserable', 'tearful', 'lonely'],
    'anxiety': ['anxious', 'anxiety', 'panic', 'worried', 'nervous', 'scared', 'afraid'],
    'anger': ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'frustrated'],
    'joy': ['happy', 'good', 'fine', 'great', 'hopeful', 'relieved'],
    'neutral': []
}

def detect_crisis(text):
    lowered = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in lowered:
            return True
    return False

def detect_emotion(text):
    lowered = text.lower()
    scores = {k: 0 for k in EMOTION_KEYWORDS.keys()}
    for emo, kws in EMOTION_KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', lowered):
                scores[emo] += 1
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return 'neutral'
    return best

# -----------------------------
# REPLY TEMPLATES (fallbacks)
# -----------------------------
TEMPLATES = {
    'sadness': [
        "I'm really sorry you're feeling this way. Would you like to tell me more about what's been making you sad?",
        "That sounds really hard. I'm here to listen — do you want to share what's been going on?"
    ],
    'anxiety': [
        "I can hear you’re feeling anxious. It might help to try a small breathing exercise — want to try one together?",
        "I'm sorry you're feeling anxious. Can you tell me what’s on your mind right now?"
    ],
    'anger': [
        "It’s okay to feel angry sometimes. Do you want to talk about what made you angry?",
        "I’m listening — what happened that made you feel this way?"
    ],
    'joy': [
        "That's lovely to hear! Would you like to share more about what's going well?",
        "I'm glad you're feeling better. Want to celebrate that a bit?"
    ],
    'neutral': [
        "Thanks for sharing. How can I support you today?",
        "I’m here to listen. Tell me more if you want to."
    ],
    'crisis': [
        "I'm really sorry — I’m concerned for your safety. If you are in immediate danger, please call your local emergency number right now.",
        "If you're having thoughts of harming yourself, please contact emergency services or a mental health crisis line. If you're in India, for example, consider calling AASRA: 91-9820466726 or local helplines."
    ]
}

def choose_template(emotion):
    if emotion == 'crisis':
        return random.choice(TEMPLATES['crisis'])
    return random.choice(TEMPLATES.get(emotion, TEMPLATES['neutral']))

# -----------------------------
# GEMINI INTEGRATION
# -----------------------------
# ⚡ Set your API key directly here
GEN_KEY = "AIzaSyCPsQ5Hd0gteHyIryT6zm4-Lske0zzKWvU"  # ← Replace with your actual Gemini API key
genai.configure(api_key=GEN_KEY)

def call_gemini(prompt):
    """Send prompt to Google Gemini and return its reply."""
    try:
        model = genai.GenerativeModel("models/gemini-flash-latest")  # ✅ working model
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)
        return None

# -----------------------------
# MAIN CHAT ENDPOINT
# -----------------------------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id', 'default')
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    add_message(session_id, 'user', message)

    # 🔹 Crisis check
    if detect_crisis(message):
        reply = choose_template('crisis')
        add_message(session_id, 'bot', reply)
        return jsonify({"reply": reply, "emotion": "crisis", "context": get_recent_context(session_id)})

    # 🔹 Emotion detection
    emotion = detect_emotion(message)
    context = get_recent_context(session_id, limit=8)

    # 🔹 Build prompt for Gemini
    prompt = (
        "You are a compassionate mental-health support assistant.\n"
        "Your goals:\n"
        "- Be empathetic, kind, and supportive.\n"
        "- Never diagnose or prescribe medication.\n"
        "- Encourage healthy coping strategies.\n"
        "- Respond in 2-4 sentences maximum.\n\n"
        "Conversation context:\n"
    )
    for turn in context:
        prompt += f"{turn['role']}: {turn['text']}\n"
    prompt += f"User: {message}\nAssistant (empathetic):"

    # 🔹 Call Gemini
    llm_reply = call_gemini(prompt)
    if llm_reply:
        reply = llm_reply
    else:
        reply = choose_template(emotion)

    add_message(session_id, 'bot', reply)
    return jsonify({"reply": reply, "emotion": emotion, "context": context})

# -----------------------------
# FLASK WEBPAGE
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == '__main__':
    if not os.path.exists(DB):
        print("Database not found. Run 'python init_db.py' first.")
    app.run(debug=True, port=5000)
